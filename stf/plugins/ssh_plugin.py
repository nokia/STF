'''
Created on May 12, 2017

@author: root
'''
import os
import datetime
import time
from stf.lib.ssh.ssh_manager import SshManager
from stf.plugins.base_plugin import STFBasePlugin
from stf.lib.logging.logger import Logger
logger = Logger.getLogger(__name__)

class STFSshPluginError(BaseException):
    """If error, raise it."""
    pass

class STFSshPlugin(STFBasePlugin):

    def __init__(self, plugins):
        super(STFSshPlugin, self).__init__(plugins)
        sshGateway = os.getenv("SSH_GATEWAY")
        sshUser = os.getenv("SSH_GATEWAY_USER")
        sshPassword = os.getenv("SSH_GATEWAY_PASSWORD")
        self.sshManager = SshManager(sshGateway, sshUser, sshPassword)
        
        
    def getSshManager(self, host, user=None, pw=None, useKey=True, sshGateway=None, sshUser=None, sshPassword=None):
        """
        """
        if not sshGateway:
            sshGateway = os.getenv("SSH_GATEWAY")
        if not sshUser:
            sshUser = os.getenv("SSH_GATEWAY_USER")
        if not sshPassword:
            sshPassword = os.getenv("SSH_GATEWAY_PASSWORD")
        sshManager = SshManager(sshGateway, sshUser, sshPassword)
        sshManager.getClient(host, user=user, pw=pw)
        return sshManager

    def getClient(self, host, user=None, pw=None, becomeUser=None, becomePW=None):
        """
        """
        try:
            if not becomeUser:
                self.sshManager.getClient(host, user, pw)
            else:
                self.sshManager.getClient(host, user, pw, becomeUser, becomePW)
        except BaseException, msg:
            errorMsg = "cannot access to %s as user %s:%s, error msg is %s" % (str(host), str(user), str(pw), str(msg))
            logger.error(errorMsg)
            raise STFSshPluginError(errorMsg)
    
    def getLabClient(self, lab):
        """
        get a lab ssh client
        
        :param LabInfo lab: the LabInfo object
        """
        account = lab.user
        passwd = lab.password
        ip = lab.IP
        becomeUser = lab.become_user
        becomePW = lab.become_password
        logger.debug("try to get lab %s client, account: %s, passwd: %s, becomeUser: %s, becommePW: %s", str(ip), str(account), str(passwd), str(becomeUser), str(becomePW))
        self.getClient(ip, account, passwd, becomeUser, becomePW)
    
    def getLabList(self, labInfoStr):
        """
        get a list of LabInfo object
        
        :param str labInfoStr: the string of the lab info
        """
        if "@" in labInfoStr:
            nodeName = labInfoStr.split("@")[1]
            userName = labInfoStr.split("@")[0]
        else:
            nodeName = labInfoStr
            userName = None
        variablePlugin = self.plugins.getInstance("variable")
        labs = variablePlugin.getLabInfo(nodeName, userName)
        return labs
    
    def getAllLabClinet(self, labInfoStr):
        """
        get ssh clinet of all labs
        
        :param str labInfoStr: the string of the lab info
        """
        labs = self.getLabList(labInfoStr)
        if labs:
            for lab in labs:
                self.getLabClient(lab)

    def getLabListClient(self, labs):
        """
        get ssh client of all labs
        
        :param list labs: a list of LabInfo instances
        """
        if labs:
            for lab in labs:
                self.getLabClient(lab)

    def copyFileToRemote(self, remoteNode, localFilePath, remoteFile=None, account='root'):
        """
        copy local file to remote, return False if copy file action failed.
        
        :param string remoteNode: the hostname or the ipadress of the remote node
        :param string localFilePath: the local file path
        :param sring remoteFile: remote file dir path, if None, will use /tmp/filename
        :param string account: default is 'root'
        :return tuple(returnCode, remoteFilePath), returnCode is true means copy action success
        """
        filename = os.path.basename(localFilePath)
        if not remoteFile:
            remoteFilePath = "/tmp/" + filename +"_" + self.generateRandomString(6)
        else:
            remoteFilePath = remoteFile
        logger.debug("copy file %s to %s %s", localFilePath, remoteNode, remoteFilePath)
        rc = self.sshManager.scpPut(localFilePath, remoteNode, remoteFilePath, account)
        return rc, remoteFilePath
        

    def prepareCaseSourceList(self, serverInfo):
        """
        r51.ih.lucent.com:/u/xguan005/test/@@xguan005:mypasswd
        """
        remoteInfo = serverInfo.split("@@")[0]
        server = remoteInfo.split(":")[0]
        caseRemotePath = remoteInfo.split(":")[1]
        accountInfo = serverInfo.split("@@")[1]
        account = accountInfo.split(":")[0]
        if ":" in accountInfo:
            password = accountInfo.split(":")[1]
            useKey = False
        else:
            password = None
            useKey = True

        sshManager = self.getSshManager(server, account, password, useKey)

        logger.debug("try to clone %s from server %s", caseRemotePath, server)
        date = datetime.datetime.now().strftime("%Y%m%d-"+ time.tzname[1] + "-%H%M%S.%f")
        caseDir = "TestCase-" + date
        
        sshManager.scpGetDir(server, caseRemotePath, account, caseDir)
        caseDirFullPath = os.path.join(os.getcwd(), caseDir)
        logger.info("case dir is %s", caseDirFullPath)
        return caseDirFullPath

        
        
