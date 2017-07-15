'''
GOAL: high level generate image for the screenshot of a state and add to Image table
given: state UUID, config file [img resolution for screenshot, os, browser option]
return: png image of screenshot of a state,
        add a new image object to Image table
'''
import json
import os
import platform
import sh
import tempfile

from django.conf import settings  # database dir
from django.core.files.images import ImageFile
from HookCatcher.models import Image

# directory for storing images in the data folder
IMG_DATABASE_DIR = os.path.join(settings.DATABASE_DIR, 'img')


def get_img_name(browser, osys, img_width, img_height, state_obj):
    # generate an apporpriate namme for the
    state_repo_path = os.path.join(state_obj.state_name, state_obj.git_commit.git_repo)
    branch_commit_path = os.path.join(state_obj.git_commit.git_branch, state_obj.git_commit.git_hash[:7])
    img_dir = os.path.join(state_repo_path, branch_commit_path)
    img_name = '{0}_{1}_{2}x{3}.png'.format(browser,  # {0}
                                            osys,
                                            img_width,  # {2}
                                            img_height)
    img_path = os.path.join(img_dir, img_name)

    return img_path


def phantom(real_img_name, img_obj):
    with tempfile.NamedTemporaryFile(suffix='.png') as temp_img:
        sh.phantomjs('screenshotScript/capture.js',  # where the capture.js script is
                     img_obj.state.state_url,        # url for screenshot
                     temp_img.name,                  # img name
                     img_obj.device_res_width,                          # width
                     img_obj.device_res_height)                         # height

        # save this file plus information into Image model
        img_obj.img_file.save(real_img_name, temp_img, save=True)
        print('Generated image named: {0}'.format(img_obj.img_file.name))
        return img_obj


# retrieve the information of a single state and generate an image based on that
# this function should always return an image object no matter if a new one has been generated
def gen_screenshot(state_obj, config, browser, curr_OS, capture_tool):   
    res = config["resolution"]
    # build the iamge name for this screenshot
    img_name = get_img_name(browser, curr_OS, res[0], res[1], state_obj)

    # find the database entry for this image should return only one img_obj
    try: 
        img_obj = Image.objects.get(browser_type=browser, 
                                    operating_system=curr_OS, 
                                    state=state_obj,
                                    device_res_width=res[0],
                                    device_res_height=res[1])

        # see if the actual file of the image exists, else create one
        if not os.path.exists(img_obj.img_file.name):
            if capture_tool=='phantom':
                # generate new phantom screenshot, but make sure only one entry of the image is in model
                return phantom(img_name, img_obj)
            else:
                print('{0} is not an screenshot capture option'.format(capture_tool))
        else:
            print('The screenshot "{0}" already exists'.format(img_obj.img_file.name))
            # Else do nothing since image is already generated and metadata is in models
        return img_obj
    except Image.DoesNotExist:  # no entry in DB and no file, generate new phnatom and add to models
        placeholder_img = Image(img_file=None, 
                                browser_type=browser, 
                                operating_system=curr_OS, 
                                state=state_obj,
                                device_res_width=res[0],
                                device_res_height=res[1])
        if capture_tool=='phantom':
            return phantom(img_name, placeholder_img)

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
            for config in config_file:
                # check if there is the browser is a valid option
                if (str(config["id"]).lower() == 'phantom'):
                    # pass phantomJS specific variables to genereic screenshot capturing method
                    current_OS = platform.system() + ' ' + platform.release()
                    i = gen_screenshot(state_obj, config['config'], 'PhantomJS', current_OS, str(config["id"]).lower())
                    if i:
                        img_list.append(i)
                else:
                    print('"{0}" is not an screenshot capture option in "{1}". Options: "Phantom" for PhantomJS'.format(config["id"], config_path))
    return img_list
