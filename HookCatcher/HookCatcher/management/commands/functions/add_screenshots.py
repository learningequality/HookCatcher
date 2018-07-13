'''
GOAL: high level generate image for the screenshot of a state and add to Image table
given: state UUID, config file [img resolution for screenshot, os, browser option]
return: png image of screenshot of a state,
        add a new image object to Image table
'''
import json
import logging
import os
import platform
import tempfile

import requests
import sh
from django.conf import settings  # retrieve BASE_DIR
from django.core.files import File
from HookCatcher.models import Image

# Logger variable to record such things
LOGGER = logging.getLogger(__name__)


def get_img_name(browser, osys, img_width, img_height, state_obj):
    # generate an apporpriate namme for the
    state_repo_path = os.path.join(state_obj.state_name, state_obj.git_commit.git_repo)
    branch_commit_path = os.path.join(state_obj.git_commit.git_branch,
                                      state_obj.git_commit.git_hash[:7])
    img_dir = os.path.join(state_repo_path, branch_commit_path)
    img_name = '{0}_{1}_{2}x{3}.png'.format(browser,  # {0}
                                            osys,
                                            img_width,  # {2}
                                            img_height)
    img_path = os.path.join(img_dir, img_name)

    return img_path


# NOTE: doesn't work if state_url is a localhost
def browserstack(state_obj, config):
    WIDTH = config['device_resolution'][0]
    HEIGHT = config['device_resolution'][1]

    if config['browser_version']:
        BROWSER = config['browser'] + config['browser_version']
    else:
        BROWSER = config['browser']

    if config['os_version']:
        OS = config['os'] + config['os_version']
    else:
        OS = config['os']

    # need to save the image object and get the pk to send to the callback url
    try:
        img_obj, is_new_img = Image.objects.get_or_create(browser_type=BROWSER,
                                                          operating_system=OS,
                                                          state=state_obj,
                                                          device_res_width=WIDTH,
                                                          device_res_height=HEIGHT)
    except Image.MultipleObjectsReturned:
        # if the img query gets more than 1 item there is an error
        real_img_name = get_img_name(config['browser'],
                                     config['os'],
                                     config['resolution'][0],
                                     config['resolution'][1],
                                     state_obj)
        LOGGER.error('There is more than 1 copy of the same image in the database. Image info: {0}'.format(real_img_name))  # noqa: E501
        return

    if is_new_img:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        # TODO: NGROK CALLBACK URL NEEDS CHANGE
        # all browserstck devices --> https://www.browserstack.com/screenshots/browsers.json
        data = {"url": state_obj.full_url,
                "callback_url": "http://fdaac17c.ngrok.io/bs_callback/{0}/".format(img_obj.id),
                "win_res": '{0}x{1}'.format(config['desktop_resolution'][0],
                                            config['desktop_resolution'][1]),
                "mac_res": '{0}x{1}'.format(config['desktop_resolution'][0],
                                            config['desktop_resolution'][1]),
                "quality": "compressed",
                "wait_time": 5,
                "local": "true",
                "orientation": "portrait",
                "browsers": [{"device": config['device'],
                              "os": config['os'],
                              "os_version": config['os_version'],
                              "browser": config['browser'],
                              "browser_version": config["browser_version"]}]
                }

        # actually generate the image
        bs_request = requests.post('https://www.browserstack.com/screenshots',
                                   headers=headers,
                                   data='{0}'.format(json.dumps(data)),
                                   auth=(settings.BROWSERSTACK_USERNAME,
                                         settings.BROWSERSTACK_OAUTH))
        if bs_request.status_code == 200:
            bs_job_url = 'https://www.browserstack.com/screenshots/{0}.json'.format(json.loads(bs_request.text)['job_id'])  # noqa: E501
            LOGGER.debug('Browserstack is currently generating the image. Check on the progress: {0}'.format(bs_job_url))  # noqa: E501
            return img_obj
        else:
            img_obj.delete()
            LOGGER.error('There was some error in the BrowserStack API request settings')

    # if this exact image is in the database and in the file system, just return the image obj
    else:
        LOGGER.error('Image named already exists: {0}'.format(os.path.join(settings.MEDIA_ROOT,
                                                                           img_obj.img_file.name)))
        return img_obj


def chrome(state_obj, config):
    BROWSER = 'Headless Chrome'
    OS = platform.system() + ' ' + platform.release()
    WIDTH = config['resolution'][0]
    HEIGHT = config['resolution'][1]

    real_img_name = get_img_name(BROWSER, OS, WIDTH, HEIGHT, state_obj)

    num_img_obj = Image.objects.filter(browser_type=BROWSER,
                                       operating_system=OS,
                                       state=state_obj,
                                       device_res_width=WIDTH,
                                       device_res_height=HEIGHT).count()
    if num_img_obj > 1:
        # if the img query gets more than 1 item there is an error
        LOGGER.error('There is more than 1 copy of the same image in the database. Image info: {0}'.format(real_img_name))  # noqa: E501
        return
    elif num_img_obj < 1:
        temp_img = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        # temp_img.close()
        try:
            sh.node(os.path.join(settings.BASE_DIR, 'screenshotScript/puppeteer.js'),
                    '--url={0}'.format(state_obj.full_url),                # url for screenshot
                    '--imgName={0}'.format(temp_img.name),                 # img name
                    '--imgWidth={0}'.format(WIDTH),                        # width
                    '--imgHeight={0}'.format(HEIGHT))                      # height
            # img_obj.img_file defaults to None on a new create
            LOGGER.debug('Generated image in Puppeteer')
        # if there is some issue with screenshotting then say so
        # but still create the image object
        except sh.ErrorReturnCode_1 as e:
            LOGGER.error('There was an error in puppeteer: {0}'.format(e))
        with open(temp_img.name) as write_temp_img:
            ff = File(write_temp_img)
            ff.name = real_img_name
            # create an image object, then replace the file with an nontemporary image
            img_obj = Image.objects.create(img_file=ff,
                                           browser_type=BROWSER,
                                           operating_system=OS,
                                           state=state_obj,
                                           device_res_width=WIDTH,
                                           device_res_height=HEIGHT)
            # closes the write_temp_img here
        LOGGER.debug('Uploaded image to s3 bucket: {0}'.format(os.path.join(settings.MEDIA_ROOT,
                                                                            img_obj.img_file.name)))  # noqa: E501

    # if this exact image is in the database and in the file system, just return the image obj
    else:
        img_obj = Image.objects.get(browser_type=BROWSER,
                                    operating_system=OS,
                                    state=state_obj,
                                    device_res_width=WIDTH,
                                    device_res_height=HEIGHT)
        LOGGER.error('Image named already exists: {0}'.format(os.path.join(settings.MEDIA_ROOT,
                                                                           img_obj.img_file.name)))
    return img_obj


def phantom(state_obj, config):
    # build the new image name for this new screenshot
    BROWSER = 'PhantomJS'
    OS = platform.system() + ' ' + platform.release()
    WIDTH = config['resolution'][0]
    HEIGHT = config['resolution'][1]

    real_img_name = get_img_name(BROWSER, OS, WIDTH, HEIGHT, state_obj)

    try:
        img_obj, is_new_img = Image.objects.get_or_create(browser_type=BROWSER,
                                                          operating_system=OS,
                                                          state=state_obj,
                                                          device_res_width=WIDTH,
                                                          device_res_height=HEIGHT)
    except Image.MultipleObjectsReturned:
        # if the img query gets more than 1 item there is an error
        LOGGER.error('There is more than 1 copy of the same image in the database. Image info: {0}'.format(real_img_name))  # noqa: E501
        return

    # generate new image if this image file doesn't exist, even if object does
    if is_new_img:
        with tempfile.NamedTemporaryFile(suffix='.png') as temp_img:
            try:
                sh.phantomjs('screenshotScript/capture.js',  # where the capture.js script is
                             state_obj.full_url,        # url for screenshot
                             temp_img.name,                  # img name
                             WIDTH,                          # width
                             HEIGHT)                         # height

                img_obj.img_file.save(real_img_name, temp_img, save=True)
                LOGGER.debug('Generated image named: {0}'.format(os.path.join(settings.MEDIA_ROOT,
                                                                              img_obj.img_file.name)))  # noqa: E501
                if img_obj.img_file:
                    return img_obj
                else:
                    # don't want an object with No image file to be saved
                    img_obj.delete()
                    return
            # if there is some issue with screenshotting then say so
            except sh.ErrorReturnCode_1, e:
                error_msg = e.stdout
                LOGGER.error(error_msg)
            return
    # if this exact image is in the database and in the file system, just return the image obj
    else:
        LOGGER.error('Image named already exists: {0}'.format(os.path.join(settings.MEDIA_ROOT,
                                                                           img_obj.img_file.name)))
        return img_obj


# retrieve the information of a single state and generate an image based on that
# this function should always return an image object no matter if a new one has been generated
def gen_screenshot(state_obj, capture_tool, config):
    if capture_tool == 'phantom':
        # generate new phantom screenshot, but make sure only one entry of the image is in model
        return phantom(state_obj, config)

    elif capture_tool == 'chrome':
        return chrome(state_obj, config)

    elif capture_tool == 'browserstack':
        return browserstack(state_obj, config)
    else:
        # if the capture_tool is not under one of these valid options
        return


'''
I chose not to call the genScreenshot command because I need the image object to be
created first before to name the image of the screenshot in screenshot tool
'''


def add_screenshots(state_obj):
    config_path = os.path.join(settings.BASE_DIR, settings.SCREENSHOT_CONFIG)
    img_list = []
    if(os.path.exists(config_path) is True):
        with open(config_path, 'r') as c:
            config_file = json.loads(c.read())
            for config in config_file:
                image_obj = gen_screenshot(state_obj, config['id'], config['config'])
                if image_obj:
                    img_list.append(image_obj)
            return img_list
    else:
        LOGGER.critical('MISSING CONFIG FILE: {0} was not found!'.format(config_path))
