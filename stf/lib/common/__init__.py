'''
Created on Feb 13, 2015

:author: zhao, xia
'''
import os
import re
import fileinput
import shutil
from datetime import datetime
from stf.lib.logging.logger import Logger
LOGGER = Logger.getLogger(__name__)

STANDARD_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

class Utils(object):
    """Common functions
    """

    @staticmethod
    def findDir(dirName, envVariable):
        """find the given dir
        """
        dirFound = False
        localDir = os.environ.get(envVariable)
        if localDir and os.path.isdir(localDir):
            dirFound = True

        directories = os.getcwd().split(os.sep)
        while directories and not dirFound:
            localDir = os.path.join(os.sep.join(directories), dirName)
            if os.path.isdir(localDir):
                dirFound = True
                break
            directories.pop()
        if not dirFound:
            LOGGER.warning(dirName + " directory not found")
            raise Exception(dirName + " directory not found")
        return localDir

    @staticmethod
    def findFile(pathName, fileName):
        """Find the given file name under path directory and subdirectories"""
        print os.getcwd()
        for root, _, files in os.walk(pathName):
            if fileName in files:
                return os.path.join(root, fileName)
        return None

    @staticmethod
    def getCurrentLabTime(sshManager, lab, isString=True):
        """Get current lab time.

        If isString is True by default, the return value is string like '2015-10-10 11:22:33'. If
        isString is False, the return value is a datetime type like datetime.datetime(2015, 10,
        10, 11, 22, 33).

        Keyword arguments:
        sshManager -- one MultiMcasSshManager object
        lab -- one lab object
        isString -- flag indicating a string type value is returned or not (default True)
        """
        response = sshManager.run(lab.oamIpAddress, "date '+%F %T'")
        if int(response[0]):
            LOGGER.warning(lab.id + ": Can not get lab time")
            raise Exception("Can not get lab time")
        curTime = response[1]
        curTime = datetime.strptime(curTime.strip(), STANDARD_DATE_FORMAT)
        return str(curTime) if isString else curTime

    @staticmethod
    def getCurrentLabSeconds(sshManager, lab):
        """Return seconds on lab since 1970-01-01 00:00:00 UTC

        :param SshManager sshManager: SshManager object
        :param Lab lab: Lab object
        :return: seconds on lab since 1970-01-01 00:00:00 UTC
        :rtype: str

        >>> Utils.getCurrentLabSeconds(sshManager, lab)
        """
        response = sshManager.run(lab.oamIpAddress, "date '+%s'")
        if int(response[0]):
            LOGGER.warning(lab.id + ": Can not get lab time")
            raise Exception("Can not get lab time")
        return response[1]

    @staticmethod
    def convertStringToDatetime(dateString):
        """
        Convert a string representing a date to a datetime object
        the format of date is supposed to be '%Y-%m-%d %H:%M:%S'
        """
        return datetime.strptime(dateString, STANDARD_DATE_FORMAT)

    @staticmethod
    def replaceInFile(_fil, patternToFind='', strToReplace=None, byOccurStr=''):
        """
        In file '_fil', on lines matching 'patternToFind' : string 'strToReplace' will be replaced by 'byOccurStr'
        :param str patternToFind: lines matching the patternToFind will be selected for change. regex compliant
                               if empty string, all lines will be selected
        :param str strToReplace: the string to be modified on the line selected . regex compliant.
                          strToReplace=None means  strToReplace = patternToFind
        :param str byOccurStr: string 'strToReplace' will be replaced by string 'byOccur'
        """
        if strToReplace is None:
            strToReplace = patternToFind
        # fileinput allows to replace "in-place" directly into the file
        for lin in fileinput.input(_fil, inplace=1):
            if re.search(patternToFind, lin):
                lin = re.sub(strToReplace, byOccurStr, lin.rstrip())
            print(lin)



    @staticmethod
    def copyDirectoryTree(src, dest):
        '''
        copy recursively a tree from src to dest
        Caution : dest must not exist. it will be deleted at the beginning of the function
        '''
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(src, dest)


