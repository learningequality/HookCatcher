'''
GOAL: high level generate image for the screenshot of a state and add to Image table
given: state UUID, config file [img resolution for screenshot, os, browser option]
return: png image of screenshot of a state,
        add a new image object to Image table
'''
import json
import os
import platform
import tempfile
import time

import django_rq
import requests
import sh
from django.conf import settings  # database dir
from HookCatcher.models import Image


# Temporary function to convert local urls to ngrok url
def get_ngrok(local_url):
    ngrok_url = "885684bc.ngrok.io"
    if "localhost:8000" in local_url:
        return local_url.replace("localhost:8000", ngrok_url)

    elif "127.0.0.1:8000" in local_url:
        return local_url.replace("127.0.0.1:8000", ngrok_url)


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

    img_query = Image.objects.filter(browser_type=BROWSER,
                                     operating_system=OS,
                                     state=state_obj,
                                     device_res_width=WIDTH,
                                     device_res_height=HEIGHT)

    # generate new image if this image file doesn't exist
    if (img_query.count() == 0 or img_query.count() == 1 and
       img_query.get().image_rendered() and not img_query.get().image_exists()):
        # need to save the image object and get the pk to send to the callback url
        if img_query.count() == 1:
            # save this file plus information into Image model
            img_obj = img_query.get()
        else:
            img_obj = Image(img_file=None,
                            browser_type=BROWSER,
                            operating_system=OS,
                            state=state_obj,
                            device_res_width=WIDTH,
                            device_res_height=HEIGHT)
            img_obj.save()

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        # all browserstck devices --> https://www.browserstack.com/screenshots/browsers.json
        data = {"url": get_ngrok(state_obj.state_url),
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
            print('Browserstack is currently generating the image. Check on the progress: {0}'.format(bs_job_url))  # noqa: E501
            return img_obj
        else:
            img_obj.delete()
            print ('There was some error in the BrowserStack API request settings')

    # if this exact image is in the database and in the file system, just return the image obj
    elif img_query.count() == 1 and img_query.get().image_exists():
        print('Image named already exists: {0}'.format(img_query.get().img_file.name))
        return img_query.get()
    elif img_query.count() > 1:
        # if the img_query returns more than 1 item there is an error
        print img_query
        print 'there are more than 1 copies of this image'
    # else the image may be still proccessing
    return


def chrome(state_obj, config):
    BROWSER = 'Headless Chrome'
    OS = platform.system() + ' ' + platform.release()
    WIDTH = config['resolution'][0]
    HEIGHT = config['resolution'][1]

    real_img_name = get_img_name(BROWSER, OS, WIDTH, HEIGHT, state_obj)

    img_query = Image.objects.filter(browser_type=BROWSER,
                                     operating_system=OS,
                                     state=state_obj,
                                     device_res_width=WIDTH,
                                     device_res_height=HEIGHT)

    # generate new image if this image file doesn't exist
    if (img_query.count() == 0 or
       img_query.count() == 1 and not img_query.get().image_exists()):
        with tempfile.NamedTemporaryFile(suffix='.png') as temp_img:
            sh.node('screenshotScript/headlessChrome.js',  # where the capture.js script is
                    '--url={0}'.format(state_obj.state_url),                # url for screenshot
                    '--imgName={0}'.format(temp_img.name),                  # img name
                    '--viewportWidth={0}'.format(WIDTH),                          # width
                    '--viewportHeight={0}'.format(HEIGHT))                        # height
            if img_query.count() == 1:
                # save this file plus information into Image model
                img_obj = img_query.get()
            else:
                img_obj = Image(img_file=None,
                                browser_type=BROWSER,
                                operating_system=OS,
                                state=state_obj,
                                device_res_width=WIDTH,
                                device_res_height=HEIGHT)

            img_obj.img_file.save(real_img_name, temp_img, save=True)
            print('Generated image named: {0}'.format(os.path.join(settings.MEDIA_ROOT,
                                                                   img_obj.img_file.name)))
            return img_obj
    # if this exact image is in the database and in the file system, just return the image obj
    elif img_query.count() == 1 and img_query.get().image_exists():
        print('Image named already exists: {0}'.format(os.path.join(settings.MEDIA_ROOT,
                                                                    img_query.get().img_file.name)))
        return img_query.get()
    else:
        print('There is more than 1 copy of the same image in the database. QuerySet: {0}'.format(img_query))  # noqa: E501
        # if the img_query returns more than 1 item there is an error
        return


def phantom(state_obj, config):
    # build the new image name for this new screenshot
    BROWSER = 'PhantomJS'
    OS = platform.system() + ' ' + platform.release()
    WIDTH = config['resolution'][0]
    HEIGHT = config['resolution'][1]

    real_img_name = get_img_name(BROWSER, OS, WIDTH, HEIGHT, state_obj)

    img_query = Image.objects.filter(browser_type=BROWSER,
                                     operating_system=OS,
                                     state=state_obj,
                                     device_res_width=WIDTH,
                                     device_res_height=HEIGHT)

    # generate new image if this image file doesn't exist
    if (img_query.count() == 0 or
       img_query.count() == 1 and not img_query.get().image_exists()):
        with tempfile.NamedTemporaryFile(suffix='.png') as temp_img:
            sh.phantomjs('screenshotScript/capture.js',  # where the capture.js script is
                         state_obj.state_url,        # url for screenshot
                         temp_img.name,                  # img name
                         WIDTH,                          # width
                         HEIGHT)                         # height
            if img_query.count() == 1:
                # save this file plus information into Image model
                img_obj = img_query.get()
            else:
                img_obj = Image(img_file=None,
                                browser_type=BROWSER,
                                operating_system=OS,
                                state=state_obj,
                                device_res_width=WIDTH,
                                device_res_height=HEIGHT)

            img_obj.img_file.save(real_img_name, temp_img, save=True)
            print('Generated image named: {0}'.format(os.path.join(settings.MEDIA_ROOT,
                                                                   img_obj.img_file.name)))
            return img_obj
    # if this exact image is in the database and in the file system, just return the image obj
    elif img_query.count() == 1 and img_query.get().image_exists():
        print('Image named already exists: {0}'.format(os.path.join(settings.MEDIA_ROOT,
                                                                    img_query.get().img_file.name)))
        return img_query.get()
    else:
        # there is an ERROR in the database because there is more than one unique image
        return


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
    config_path = settings.SCREENSHOT_CONFIG
    img_list = []
    if(os.path.exists(config_path) is True):
        with open(config_path, 'r') as c:
            config_file = json.loads(c.read())
            queue = django_rq.get_queue('default')

            for config in config_file:
                # image_obj = gen_screenshot    (state_obj, config['id'], config['config'])
                job = queue.enqueue(gen_screenshot, state_obj, config['id'], config['config'])
                while not job.is_finished:
                    time.sleep(1)
                image_obj = job.result
                if image_obj:
                    img_list.append(image_obj)
            return img_list
