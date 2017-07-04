'''
Created on May 12, 2017

@author: root
'''
import os
import datetime
import time
from git import Repo
from stf.plugins.base_plugin import STFBasePlugin
from stf.lib.logging.logger import Logger
logger = Logger.getLogger(__name__)

class STFGitrepoPlugin(STFBasePlugin):

    def __init__(self, plugins):
        super(STFGitrepoPlugin, self).__init__(plugins)

    def prepareCaseSourceList(self, gitRepoUrl, envFile=None):
        """
        """
        if envFile:
            ssh_cmd ='ssh -i '+ envFile
        else:
            ssh_cmd = 'ssh -i conf/id_rsa'
        logger.debug("try to clone %s", gitRepoUrl)
        date = datetime.datetime.now().strftime("%Y%m%d-"+ time.tzname[1] + "-%H%M%S.%f")
        caseDir = "TestCase-" + date
        Repo.clone_from(gitRepoUrl, caseDir, branch='master', env={'GIT_SSH_COMMAND': ssh_cmd})
        caseDirFullPath = os.path.join(os.getcwd(), caseDir)
        logger.info("case dir is %s", caseDirFullPath)
        return caseDirFullPath
        
        
