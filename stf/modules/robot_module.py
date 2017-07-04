import sys
from stf.modules.base_module import STFBaseModule
from stf.lib.logging.logger import Logger
import subprocess
import commands
import os
from shutil import copyfile

logger = Logger.getLogger(__name__)

class STFRobotModuleError(BaseException):
    """If error, raise it."""
    pass
class STFRobotModule(STFBaseModule):
    
    def __init__(self, pluginManager):
        """
        constructor
        """
        super(STFRobotModule, self).__init__(pluginManager)

    def checkMode(self, mode):
        """
        TBD
        """
        pass
    
    def checkModeParameter(self, parameter):
        """
        TBD
        """
        pass
    
    def checkModuleParameter(self, module, jumphost_info, lab_info):
        """
        :param module parameter
         TODO: DRY-RUN
        """
        logger.info("module name is %s, justhost is %s,  access node is %s", module, jumphost_info, lab_info)
        if module.lower() != "robot":
            logger.error("this is robot module, not %s", module)
            raise STFRobotModuleError("this is ansible module, not %s", module)
        self.isRobotInstalled()
        
        
    def isRobotInstalled(self):
        (status, output) = commands.getstatusoutput("pybot --version| grep -i robot")
        if status != 0:
            logger.error("Robot has not installed")
            raise STFRobotModuleError("Robot has not installed")
        
    def checkTags(self, tags):
        pass
    
    def checkCaseIDs(self, cases):
        pass
    
    def checkOthers(self, f):
        pass
    
    def appendExtToCaseFile(self, filefullname):
        """
        functin: cope case file to /tmp/robot dir; rename filename to filename.ext(a.txt)
        return the new file fullpath
        """
        caseExt = ".txt";
        tmpdir = "/tmp/robot"
        if not os.path.isdir(tmpdir):
            os.makedirs(tmpdir)
        #TODO: stf case has no ext, while robot not support this format, so usr should conf the file ext, then the ext will be append to case for running
        newfilefullname = tmpdir + os.path.basename(filefullname) + caseExt
        copyfile(filefullname, newfilefullname)
        return newfilefullname
    
    def extractVarFileFromIni(self):
        '''
        function: generate tmp file storing robot variable, from [Robot:Variable] section of ini file
        return:   absolate paht of robot variable file, the ext of file should be .py
        '''
        varFile = self.variablePlugin.getRobotVarFile();
        if not os.path.isfile(varFile):
            logger.error("Robot module generate variable file failed")
            raise STFRobotModuleError("Robot module generate variable file failed")
        
        return varFile
    
    def run(self, caseInfo):
        
        caseFileLocation = caseInfo.current_step.path
        caseFileName = os.path.basename(caseFileLocation)
        mode = caseInfo.current_step.mode
        parameter = caseInfo.current_step.mode_argv 
        module = caseInfo.current_step.module
        jumphost_info = caseInfo.current_step.jumphost_info
        lab_info = caseInfo.current_step.lab_info
        tags = caseInfo.current_step.step_tags
        
#         casefile = self.appendExtToCaseFile(caseFileLocation)
        logger.debug( "casefile is %s", caseFileLocation)
        (rc, output) = commands.getstatusoutput('robot --output None --report None --log None --dryrun ' + caseFileLocation)
        if rc != 0:
            logger.error("test case %s syntax error", caseFileLocation);
            raise STFRobotModuleError("test case %s syntax error", caseFileLocation)
        
        else:
            logger.info("Robot dryrun passed")

        self.processStart(caseInfo, 0)
        outputdir = os.path.dirname(os.path.abspath('.')) + "/testcase_reports/robot_reports/"
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)
        casename = os.path.splitext(caseFileName)[0]
        outputfile = outputdir + casename +"_output.xml"
        reportfile = outputdir + casename +"_report.html"
        logfile = outputdir + casename +"_log.html"
        cmd = "robot --output %s --report %s --log %s  %s" %(outputfile,  reportfile , logfile, caseFileLocation)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdoutput, erroutput = proc.communicate()
        #logger.debug("stdout is %s; stderr is %s ",(stdoutput, erroutput))
#         print "stdoutput is "+stdoutput
        rc = proc.returncode
        self.processEnd(caseInfo, 0, caseFileName, rc, stdoutput, erroutput, proc.pid)
        return rc;
    if __name__ == '__main__':
        print os.path.splitext('a.txt')[0]
        
    
        
        

