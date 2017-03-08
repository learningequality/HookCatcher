# sh.cd('..')
from os import path

import sh

KOLIBRI_DIR = path.abspath("../../kolibri")

# Directory name of the sample data
SAMPLE_DATA = 'HookCatcherData'
# External databse folder with db.sqlite3 and
DATABASE_DIR = path.join(path.dirname(path.dirname(path.dirname(
                         path.abspath(__file__)))), SAMPLE_DATA)

IMAGES_DIR = path.join(DATABASE_DIR, 'img')
print(IMAGES_DIR)


'''
take screenshot of a url with PhantomJS and save the file into images folder
    url = the url that the screenshot is taken
    fileName = name of the file for the screenshot,
        represents the state name and the gitSource version
'''


def genScreenshot(url, fileName):
    screenshotName = '{0}.png'.format(fileName)
    print(screenshotName)
    sh.phantomjs('capture.js', url,
                 '{0}/{1}'.format(IMAGES_DIR, screenshotName))


'''
switch the kolibri branch so that the state of kolibri changes
    gitBranch = the name of the git branch for the kolibri instance
        to be switched to
'''


def switchBranch(gitBranch):
    kolibri_git_dir = path.abspath(path.join(KOLIBRI_DIR, '.git'))
    print('kolibri dir: ' + kolibri_git_dir)

    print(sh.git('--git-dir', kolibri_git_dir, '--work-tree',
                 KOLIBRI_DIR, 'checkout', gitBranch))


'''
pass in two file names and generate a new fle
    img1 = the file name of the image being compared by
    img2 = the file name of the image being compared to
'''


def createDiff(img1, img2):
    diffIMG = img1 + '_' + img2 + 'DIFF.png'
    try:
        sh.compare('{0}/{1}.png'.format(IMAGES_DIR, img1),
                   '{0}/{1}.png'.format(IMAGES_DIR, img2),
                   '{0}/{1}'.format(IMAGES_DIR, diffIMG))
    except sh.ErrorReturnCode_1 as e:
        print "Hopefully empty error code", e.stderr

    gitBranches = ['test-pr', 'test-master']

    states = [('explore', 'http://localhost:8000/learn/#/explore/5b1e904335ab4dfda82e3e37735262c5'),  # noqa: E501
              ('learn', 'http://localhost:8000/learn/#/learn/5b1e904335ab4dfda82e3e37735262c5')]  # noqa: E501

    for stateTuple in states:   # change to next state
        imgArray = ['', '']     # save name of file for each branch in aray

        # iterate to next branch
        for idxBranch, branchToggle in enumerate(gitBranches):
            tempFilename = '{0}_{1}'.format(branchToggle, stateTuple[0])
            imgArray[idxBranch] = '{0}'.format(tempFilename)

            genScreenshot(stateTuple[1], tempFilename)

            # switch the branch and take another screenshot of the state
            switchBranch(branchToggle)

        print('DIFFF ' + imgArray[0] + ' WITHH ' + imgArray[1])
        createDiff(imgArray[0], imgArray[1])


'''
Insert IMage info to model

'''

# In [4]: git_dir = os.path.abspath(os.path.join('HookCatcherProj', '.git'))

# In [5]: working_dir = os.path.abspath('HookCatcherProj')

# In [6]:

# In [6]:

# In [6]: working_dir
# Out[6]: '/Users/mingdai/Documents/Python/HookCatcherProj'

# In [7]: git_dir
# Out[7]: '/Users/mingdai/Documents/Python/HookCatcherProj/.git'

# In [9]: sh.git('--git-dir', git_dir, '--work-tree', working_dir, 'status')
