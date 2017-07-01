'''
GOAL: high level command that Diffs two images and add to DIFF table
given: two images to diff, diff method of choice
return: diff image between 2 screenshots of a state,
        add a new diff object to DIFF table
'''
import os

from django.conf import settings  # database dir
from django.core.management.base import BaseCommand, CommandError
from HookCatcher.management.commands.functions.gen_diff import gen_diff
from HookCatcher.models import Diff, Image

# directory for storing images in the data folder
IMG_DATABASE_DIR = os.path.join(settings.DATABASE_DIR, 'img')


def getDiffImageName(imgObj1, imgObj2):
    # format the name of the diff image to be base(target) commit -> diffs -> head(source) commit

    # formula: (baseGitinfo)/diffs/(headGitInfo)/(imgMetadata).png
    stateAndRepoBase = os.path.join(imgObj1.state.stateName, imgObj1.state.gitCommit.gitRepo)
    branchAndCommitBase = os.path.join(imgObj1.state.gitCommit.gitBranch,
                                       imgObj1.state.gitCommit.gitHash[:7])
    imgPathBase = os.path.join(stateAndRepoBase, branchAndCommitBase)

    stateAndRepoHead = os.path.join(imgObj2.state.stateName, imgObj2.state.gitCommit.gitRepo)
    branchAndCommitHead = os.path.join(imgObj2.state.gitCommit.gitBranch,
                                       imgObj2.state.gitCommit.gitHash[:7])
    imgPathHead = os.path.join(stateAndRepoHead, branchAndCommitHead)

    diffPath = os.path.join(os.path.join(imgPathBase, 'diffs'), imgPathHead)
    name = '{0}_{1}_{2}x{3}.png'.format(imgObj1.browserType,  # {0}
                                        imgObj1.operatingSystem,
                                        imgObj1.width,    # {2}
                                        imgObj1.height)

    diffCompletePath = os.path.join(diffPath, name)
    return diffCompletePath


def addDiffData(diffImgName, imgObj1, imgObj2, diffPercent):
    # check if image already exists in data to prevent duplicates
    findDuplicateDiff = Diff.objects.filter(targetImg=imgObj1,
                                            sourceImg=imgObj2)
    # if there was a duplicate found, update percent and imageName
    if (findDuplicateDiff.count() > 0):
        findDuplicateDiff = findDuplicateDiff.get()
        findDuplicateDiff.diffImgName = diffImgName
        findDuplicateDiff.diffPercent = diffPercent
        findDuplicateDiff.save()
        return findDuplicateDiff
    else:
        diffObj = Diff(diffImgName=diffImgName,
                       targetImg=imgObj1,
                       sourceImg=imgObj2,
                       diffPercent=diffPercent)
        diffObj.save()
        return diffObj


class Command(BaseCommand):
    help = 'Choose two image screenshots of the same state, resolution, os, and browser to take a diff of'  # noqa: E501

    def add_arguments(self, parser):
        # use state UUID for identification rather thatn commitHash, repo, branch, state names
        parser.add_argument('diffTool')
        parser.add_argument('imgName1')
        parser.add_argument('imgName2')

# if one of the image objects don't exist in database should we just add it?
    def handle(self, *args, **options):
        try:
            # Make sure these images exist in the image database
            diffTool = options['diffTool']
            img1 = Image.objects.get(imgName=options['imgName1'])
            img2 = Image.objects.get(imgName=options['imgName2'])
        except Image.DoesNotExist:
            raise CommandError('At least one of the two images does not exist in the database')

        imgPath1 = os.path.join(IMG_DATABASE_DIR, img1.imgName)
        imgPath2 = os.path.join(IMG_DATABASE_DIR, img2.imgName)
        diffName = getDiffImageName(img1, img2)

        # call the function gen_diff from gen_diff file
        percentDiff = gen_diff(diffTool,
                               imgPath1,
                               imgPath2,
                               os.path.join(IMG_DATABASE_DIR, diffName))
        # update database info only when a new diff has been generated
        if percentDiff:
            diffObj = addDiffData(diffName, img1, img2, percentDiff)
            self.stdout.write(self.style.SUCCESS('Finished adding new Diff "{0}"'.format(diffObj)))
