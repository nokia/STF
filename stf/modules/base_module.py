'''
Created on Mar 31, 2017

@author: Zhao Xia
'''
import os
import random, string
from abc import abstractmethod
from stf.lib.logging.logger import Logger
import time

logger = Logger.getLogger(__name__)

def generateRandomString(N):
    """
    generate a random sring, length is N
    """
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))

class STFBaseModuleError(BaseException):
    """If error, raise it."""
    pass

class STFBaseModule(object):
    """
    the base module of the 
    """
    def __init__(self, plugins):
        """
        constructor
        """
        self.env_cache = []
        self.plugins = plugins
        self.variable = plugins.getInstance("variable")
        self.sshPlugin = plugins.getInstance("ssh")
        self.sshManager = self.sshPlugin.sshManager
        
    @abstractmethod
    def checkMode(self, mode):
        raise NotImplementedError("You must use subclass rather than the base class STFBaseModule")

    @abstractmethod
    def checkModeArgv(self, mode_argv):
        raise NotImplementedError("You must use subclass rather than the base class STFBaseModule")

    @abstractmethod
    def checkModule(self, module):
        raise NotImplementedError("You must use subclass rather than the base class STFBaseModule")

    @abstractmethod
    def checkModuleArgv(self, module_argv):
        raise NotImplementedError("You must use subclass rather than the base class STFBaseModule")

    @abstractmethod
    def checkTmsIDs(self, cases):
        raise NotImplementedError("You must use subclass rather than the base class STFBaseModule")

    @abstractmethod
    def checkTags(self, tags):
        raise NotImplementedError("You must use subclass rather than the base class STFBaseModule")

    @abstractmethod
    def checkOthers(self, file_path):
        raise NotImplementedError("You must use subclass rather than the base class STFBaseModule")

    def checkFileExistAndNotEmpty(self, file_path):
        if os.path.exists(file_path):
            if not os.path.getsize(file_path):
                error_msg = "file %s is empty" %(file_path)
                logger.warning(error_msg)
            return

        error_msg = "file %s is not exist" %(file_path)
        logger.error(error_msg)
        raise Exception(error_msg)

    def preCheck(self, test_step):
        logger.info("mode is %s, mode_argv is %s, module is %s, module_argv is %s, step_tags is %s, test_step.tms_ids is %s",\
                    test_step.mode, test_step.mode_argv, test_step.module, test_step.module_argv, test_step.step_tags, test_step.tms_ids)
        if test_step.path:
            self.checkFileExistAndNotEmpty(test_step.path)
        if test_step.mode:
            self.checkMode(test_step.mode)
        if test_step.mode_argv:
            self.checkModeArgv(test_step.mode_argv)
        if test_step.module:
            self.checkModule(test_step.module)
        if test_step.module_argv:
            self.checkModuleArgv(test_step.module_argv)
        if test_step.step_tags:
            self.checkTags(test_step.step_tags)
        if test_step.tms_ids:
            self.checkTmsIDs(test_step.tms_ids)
        self.checkOthers(test_step)

    @abstractmethod
    def runStep(self, test_step):
        raise NotImplementedError("You must use subclass rather than the base class STFBaseModule")

    def run(self, test_step):
        test_step.starttime = time.time()
        test_step.status = 'running'
        exception = None
        try:
            self.runStep(test_step)
        except Exception, e:
            exception = e

        test_step.endtime = time.time()
        test_step.status = 'end'

        if exception:
            raise exception
        for tp in test_step.process_info:
            if tp.exitcode != 0:
                test_step.exitcode = tp.exitcode

    def copyFileToRemote(self, remoteNode, localFilePath, remoteFileDir=None, account='root'):
        """
        copy local file to remote, return False if copy file action failed.
        
        :param string remoteNode: the hostname or the ipadress of the remote node
        :param string localFilePath: the local file path
        :param sring remoteFileDir: remote file dir path, if None, will use /tmp
        :param string account: default is 'root'
        :return tuple(returnCode, remoteFilePath), returnCode is true means copy action success
        """
        filename = os.path.basename(localFilePath)
        if not remoteFileDir:
            remoteFilePath = "/tmp/" + filename +"_" + generateRandomString(6)
        else:
            remoteFilePath = remoteFileDir + "/" + filename
        logger.debug("copy file %s to %s %s", localFilePath, remoteNode, remoteFilePath)
        rc = self.sshManager.scpPut(localFilePath, remoteNode, remoteFilePath, account)
        return rc, remoteFilePath
 
    def setEnvLocal(self):
        """
        set env local
        use os.environ['ABC'] to set env; os.getenv('ABC') to get env parameter
        :return boolean, true mean set success
        """
        for key in self.variable.options('Env'):
            #cannot modify existed env
            if key in os.environ:
                continue

            os.environ[key] = self.variable.getEnv(key)
            self.env_cache.append(key)

    def clearEnvLocal(self):
        for e in self.env_cache:
            del os.environ[e]
    
    def _generateEnvProfile(self):
        """
        use to generate a profile for env seting
        :return the local path of the profile
        """
        return self.variable.getEnvFile()

    
    
    
    
