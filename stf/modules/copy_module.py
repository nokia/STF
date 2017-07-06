import sys
import os
import shutil
import time
from stf.modules.base_module import STFBaseModule
from stf.lib.logging.logger import Logger
from stf.lib.SParser import SParser
from stf.managers.test_case_manager import TestStep, TestProcess

logger = Logger.getLogger(__name__)

class STFCopyModuleError(BaseException):
    """If error, raise it."""
    pass
class STFCopyModule(STFBaseModule):
    def __init__(self, pluginManager):
        super(STFCopyModule, self).__init__(pluginManager)
        self.lab = None
        self.jumphost = None

    def checkMode(self, mode):
        pass
    
    def checkModeParameter(self, parameter):
        pass

    def checkModule(self, module):
        if module == 'copy':
            return

        raise Exception("module name should be [copy] while it is [%s]" % module )
                 
    def checkModuleArgv(self, module_argv):
        """
        :param module parameter
        """
        self.jumphost, self.lab = SParser.parseModule(module_argv)

        logger.info("justhost is %s,  access node is %s", self.jumphost, self.lab)

        if self.jumphost:
            logger.error("not support jump host now")
            raise STFCopyModuleError("not support jump host now")

        #vlab is dynamically created, so return here
        node_id = self.lab
        if '@' in self.lab:
            node_id = self.lab.split("@")[1]

        if self.variable.isVlabValid(node_id):
            return

        if self.lab is None:
            return

        userName, nodeName = self.lab.split("@")
        labs = self.variable.getLabInfo(nodeName, userName)
        if not labs:
            logger.error("there is no lab for %s  as %s" % (nodeName, userName))
            raise Exception("there is no lab for %s  as %s" % (nodeName, userName))

        for lab in labs:
            try:
                if not lab.become_user:
                    self.sshManager.getClient(lab.IP, user=lab.user, pw=lab.password)
                else:
                    self.sshManager.getClient(lab.IP, lab.user, lab.password, lab.become_user, lab.become_password)
            except BaseException, msg:
                 errorMsg = "cannot access to %s as user %s:%s, error msg is %s" % (lab.IP, lab.user, lab.password, str(msg))
                 logger.error(errorMsg)
                 raise STFCopyModuleError(errorMsg)
       
    def checkTags(self, tags):
        pass
    
    def checkTmsIDs(self, cases):
        pass
    
    def checkOthers(self, test_step):
        pass
    
    def copyLocal(self, src, dst):
        try:
            if not os.path.exists(src):
                raise STFCopyModuleError("Source  %s does not exits" , src);
            if not os.path.isdir(dst):
                raise STFCopyModuleError("Target dir %s does not exits" , dst);
            if os.path.isdir(src):
                logger.info("copy local dir begin from %s to %s" ,src, dst)
                if src.endswith("/"):
                    src = src[:-1]
                srcbasename = os.path.basename(src)
                shutil.copy(src, os.path.join(dst, srcbasename))
            if os.path.isfile(src):
                
                if not dst.endswith("/"):
                    dst = dst + "/"
                logger.info("copy local file begin from %s to %s" ,src, dst)
                shutil.copy(src, dst)
        except Exception as err:
                logger.error("copy local from %s to %s fail, error msg is %s" , src, dst, err)
                rc = 255
                output = "copy fail"
        else:
            rc = 0
            output = "copy success"
            err = ""
                
        return rc, output, err
     
    def copyremote(self, src, dst, ip, account, pw, cpmode):
        
        try:
            if cpmode == "Download":
                #for dir and file
                logger.info("download from server %s , user is %s, %s to %s" , ip, account, src, dst);
                self.sshManager.scpGetDir(ip, src, account, dst, pw);
            
            if cpmode == "Upload":
                logger.info("upload to server %s , user is %s, %s to %s" , ip, account, src, dst);
                self.sshManager.scpPutDirOrFile(src, dst, ip, account, pw)
        except Exception as err:
             logger.error("copy remote from %s to %s fail, , cp mode is %s, error msg is %s" , src, dst, cpmode, err)
             rc = 255
             output = "copy fail"
        else:
            rc = 0
            output = "copy success"
            err = ""
        return rc, output, err


    def runStep(self, test_step):
        tp = TestProcess()
        test_step.addProcess(tp)

        tp.status = 'running'
        tp.starttime = time.time()
        caseFileLocation = test_step.path
        caseFileName = os.path.basename(caseFileLocation)
        mode = test_step.mode
        mode_argv = test_step.mode_argv
        module = test_step.module
        tags = test_step.step_tags
        
        logger.info( "copycasefile is %s", caseFileLocation)
        #file content format: 
        #download :remotefile -> localdir
        #upload:   localdir -> :remotefilepath
        file = open(caseFileLocation)

        #initialize env
        self.setEnvLocal()

        for line in file:
            logger.debug("line in file is %s", line)
            linearray = line.strip("\n").split("->")
            src = linearray[0].strip()
            dst = linearray[1].strip()
            cpmode = ""
            if ":" in src and not ":" in dst:
                src = os.path.expandvars(src.split(":")[1])
                cpmode = "Download"
            elif ":" in dst and not ":" in src :
                dst = os.path.expandvars(dst.split(":")[1])
                cpmode = "Upload"
            elif not ":" in src and not ":" in dst:
                cpmode = "Local"
            else:
                cpmode = "Error"
            
            logger.debug("copy mode is %s", cpmode)

            if not self.lab and cpmode == "Local":
                    logger.debug("copy in local, src is %s, dst is %s", src, dst)
                    tp.exitcode, tp.stdout, tp.stderr = self.copyLocal(src, dst)
                    logger.debug("run copy %s  return code is %s, output is %s", caseFileName, tp.exitcode, tp.stdout)
            elif self.lab and  cpmode == "Upload" or cpmode == "Download":
                userName, nodeName = self.lab.split("@")
                labs = self.variable.getLabInfo(nodeName, userName)
                if not labs:
                    logger.error("there is no lab for %s  as %s" % (nodeName, userName))
                    raise Exception("there is no lab for %s  as %s" % (nodeName, userName))

                for lab in labs:
                    tp.exitcode, tp.stdout, tp.stderr = self.copyremote(src, dst, lab.IP, lab.user, lab.password, cpmode)
            else:
                logger.error("copy moudule error, lab in case file name not coordinate with case content")
                self.clearEnvLocal()
                raise STFCopyModuleError("copy moudule error, lab in case file name not coherent with case content")

            self.clearEnvLocal()

        tp.endtime = time.time()
    
           
        