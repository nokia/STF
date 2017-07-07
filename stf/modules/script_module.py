'''
Created on Mar 31, 2017

@author: Zhao Xia
'''
import os
import subprocess32 as subprocess
from subprocess32 import TimeoutExpired
from posix import X_OK
import signal
import time
from stf.lib.logging.logger import Logger
from stf.modules.base_module import STFBaseModule
from stf.lib.SParser import SParser
from stf.managers.test_case_manager import TestStep, TestProcess

logger = Logger.getLogger(__name__)

ACCEPT_MODE = ["parallel", "loop", "async"]

class STFScriptModule(STFBaseModule):
    def __init__(self, pluginManager):
        super(STFScriptModule, self).__init__(pluginManager)
        self.jumphost = None
        self.lab = None

    def checkMode(self, mode):
        if mode not in ACCEPT_MODE:
            logger.error("script module do not support %s mode, now only support %s", mode, ACCEPT_MODE)
            raise Exception("script module do not support %s mode, now only support %s", mode, ACCEPT_MODE)

    def checkModeArgv(self, mode_argv):
        pass

    def checkModule(self, module):
        if module == 'script':
            return

        raise Exception("module name should be [script] while it is [%s]" % module )


    def checkModuleArgv(self, module_argv):
        self.jumphost, self.lab = SParser.parseModule(module_argv)
        if self.lab is None:
            return

        if self.jumphost:
            raise Exception('not support jump host now')

        #vlab is dynamically created, so return here
        node_id = self.lab
        if '@' in self.lab:
            node_id = self.lab.split("@")[1]

        if self.variable.isVlabValid(node_id):
            return

        labs = self.sshPlugin.getLabList(self.lab)
        if not labs:
            logger.error("there is no such lab %s", self.lab)
            raise Exception("there is no such labs %s", self.lab)

        self.sshPlugin.getLabListClient(labs)

    def checkTmsIDs(self, cases):
        pass

    def checkTags(self, tags):
        pass

    def checkOthers(self, test_step):
        if os.access(test_step.path, X_OK):
            return

        logger.debug("add +x for %s", test_step.path)
        command = "chmod +x " + test_step.path
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        outs, errs = proc.communicate()
        rc = proc.returncode
        if rc:
            raise Exception("command %s failed: rc is %s, output is %s, errs is %s ", command, rc, outs, errs)

    def runStep(self, test_step):
        """
        :param class test_step: instance of TestStep
        :return tuple(returnCode, output)
        """
        #local
        if not self.lab:
            self.setEnvLocal()
            #no specified mode
            if not test_step.mode:
                return self.runScriptLocal(test_step)

            if test_step.mode == "async":
                return self.runScriptLocal(test_step.path, 0.1, async=True)

            raise Exception('mode is not supported currently: %s' % test_step.mode )

        #remote
        if test_step.mode:
            raise Exception('mode is not supported currently when lab is specified: %s' %test_step.mode)


        self.sshPlugin.getAllLabClinet(self.lab)
        nodeName = self.lab.split("@")[1]
        userName = self.lab.split("@")[0]
        lab_instances = self.variable.getLabInfo(nodeName, userName)
        if lab_instances is None:
            raise Exception('script module cannot find lab instances: %s' % self.lab)

        for lab in lab_instances:
            account = lab.user
            ip = lab.IP
            finalAccount = account
            if lab.become_user:
                finalAccount = lab.become_user

            self.runScriptOnRemote(ip, test_step, account=finalAccount)

    def runScriptLocal(self, test_step, timeout=None, async=False):
        """
        run a script on current machine
        :param str localScriptPath: the path of the script
        :param int timeout: unit is second
        :param boolean kill: if False, will not kill the process
        :return tuple (returnCode, output)
        """
        command = test_step.path
        tp = TestProcess()
        test_step.addProcess(tp)
        tp.starttime = time.time()
        tp.status = 'running'
        try:
            proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            tp.pid = proc.pid
            if not tp.pid:
                logger.debug("get process %s pid failed ", command)
                raise Exception("get process %s pid failed ", command)
            tp.stdout, tp.stderr = proc.communicate(timeout=timeout)
            tp.exitcode = proc.returncode
        except TimeoutExpired:
            if async:
                tp.stdout = ""
                tp.stderr = "%s timeout reached" % command
                tp.exitcode = 0
            else:
                logger.debug("%s timeout reached, kill the process %s",command, pid)
                proc.kill()
                os.kill(tp.pid, signal.SIGKILL)
                tp.stdout, tp.stderr = proc.communicate()
                tp.exitcode = 255
        except Exception, e:
            tp.stdout = ''
            tp.stderr = str(e)
            tp.exitcode = 1

        finally:
            tp.endtime = time.time()
            tp.status = 'end'

    def runScriptOnRemote(self, remoteNode, test_step, remoteFileDir=None, account='root'):
        """
        run remote script with a env profile, (source remoteProfile, then run the script on remote)
        :param string remoteNode: the hostname or the ipadress of the remote node
        :param class test_step: instance of TestStep
        :param string remoteFileDir: the full path of the remoteFileDir
        :param string account: default is 'root'
        :return tuple (returnCode, output)
        """
        tp = TestProcess()
        test_step.addProcess(tp)
        tp.starttime = time.time()
        tp.status = 'running'

        tp.exitcode, remoteScriptPath = self.copyFileToRemote(remoteNode, test_step.path, remoteFileDir, account)

        if not tp.exitcode:
            return

        localEnvProfile = self._generateEnvProfile()
        tp.exitcode, remoteEnvProfile = self.copyFileToRemote(remoteNode, localEnvProfile, remoteFileDir, account)
        if not tp.exitcode:
            return
        
        command = "set -a; source " + remoteEnvProfile + "; "+ "chmod +x "+ remoteScriptPath + "; " + remoteScriptPath
        logger.debug("run command %s on %s as %s", command, remoteNode, account)
        tp.exitcode, tp.stdout, tp.stderr = self.sshManager.run(remoteNode, command, user=account)
        logger.debug("run command %s on %s as %s, tp.exitcode is %s, output is %s ",
                    command, remoteNode, account, tp.exitcode, tp.stdout + os.linesep + tp.stderr)
        rmCommand = "rm " + remoteEnvProfile + " " + remoteScriptPath
        logger.debug("run command %s on %s as %s", rmCommand, remoteNode, account)
        self.sshManager.run(remoteNode, rmCommand, user=account)
        logger.debug("return %s, %s, %s", tp.exitcode, tp.stdout, tp.stderr)

        tp.status = 'end'

