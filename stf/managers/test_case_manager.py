import os
import time
import collections
import signal
from stf.lib.SParser import SParser
from stf.lib.logging.logger import Logger
from stf.lib import stf_utils


logger = Logger.getLogger(__name__)
CONST_STATUS = ['no', 'started', 'running', 'end']
MAX_PID_NUM = 32769

#will be initialized to ModuleManager instance in the beginning of program
modules = None
plugins = None
variables = None
report = None

def init(module_manager):
    global modules, plugins, variables, report
    modules = module_manager
    plugins = modules.getPluginManager()
    variables = plugins.getInstance('variable')
    report = plugins.getInstance('report')

class TestSuite(object):
    view = None
    def __init__(self, path):
        self.path = path
        try:
            self.name = os.path.basename(self.path)
        except:
            self.name = self.path
        self.current_case = None
        self.case_list = []
        self.has_failed = False
        self.has_run = False
        self.setup = None
        self.teardown = None

        self.starttime = None
        self.endtime = None

        self.elapsed_time = None
        self.status = 'no'

    @staticmethod
    def setView(view):
        TestSuite.view = view

    def addCase(self, case):
        self.case_list.append(case)

    def caseNumbers(self):
        return len(self.case_list)

    def preCheck(self):
        if len(self.case_list)  < 1:
            logger.warning('No test cases found in current test suite: %s', self.path)
            return

        if self.setup:
            self.current_case = self.setup
            self.current_case.preCheck()

        for case in self.case_list:
            self.current_case = case
            self.current_case.preCheck()

        if self.teardown:
            self.current_case = self.teardown
            self.current_case.preCheck()

    def run(self):
        if self.has_run:
            return

        self.has_run = True

        if len(self.case_list) < 1:
            logger.warning('No test cases found in current test suite: %s', self.path )
            return

        try:
            self.starttime = time.time()
            if self.setup:
                self.current_case = self.setup
                self.current_case.run()
                if self.setup.has_failed:
                    self.has_failed = True
                    raise Exception('setup failed in current test suite, omit the following test cases.')

            for case in self.case_list:
                self.current_case = case
                self.current_case.run()

            if self.teardown:
                self.current_case = self.teardown
                self.current_case.run()
        except BaseException, e:
            self.has_failed = True
            logger.error('Test suite %s failed: %s' %(self.path, str(e) ) )
        finally:
            self.endtime = time.time()
            self.elapsed_time = "{0:.6f}".format(self.endtime - self.starttime)

class TestCase(object):
    view = None
    def __init__(self, path, name, tags, tms_ids=None, tid=None):
        self.path = path
        self.name = name
        self.id = tid
        self.test_tags = tags
        self.tms_ids = tms_ids
        self.step_list = []
        self.current_step = None

        self.has_run = False
        self.has_precheck = False
        self.has_failed = False

        self.starttime = None
        self.endtime = None
        self.elapsed_time = None
        #exitcode could be 0(success) or 1(failed)
        self.exitcode = 0
        self.status = 'no'
        self.fatal_error = None
        #key is step Id, value is StepInfo Instance

    @staticmethod
    def setView(view):
        TestCase.view = view

    def addStep(self, step):
        self.step_list.append(step)

    def preCheck(self):
        if self.has_precheck:
            return

        self.has_precheck = True

        if len(self.step_list) < 1:
            logger.warning('No step found in current case: %s', self.path )
            return

        for step in self.step_list:
            self.current_step = step
            self.current_step.tms_ids = self.tms_ids
            self.current_step.preCheck()


    def run(self):
        if self.has_run:
            return

        self.has_run = True

        if len(self.step_list) < 1:
            logger.warning('No step found in current case: %s', self.path )
            return

        variables.refreshCaseEnv()
        self.starttime = time.time()

        for step in self.step_list:
            self.current_step = step
            try:
                self.current_step.run()
            except BaseException, e:
                logger.error(str(e))
                self.has_failed = True
                self.exitcode = 1
                self.current_step.exitcode = 1
            finally:
                self.terminateTimeoutSteps()
                if self.has_failed:
                    break

        self.endtime = time.time()
        self.elapsed_time = "{0:.6f}".format(self.endtime - self.starttime)

        # Begin to update report plugin
        if self.exitcode == 0:
            logger.info('SUCCESS: %s', self.id)
            plugins.getInstance('report').setCaseListPass(self.tms_ids)
            return

        logger.error('FAIL: %s', self.id)
        plugins.getInstance('report').setCaseListFail(self.tms_ids)
        # End the update

    def isProcessTimeout(self, process):
        if not process.timeout:
            return False

        duration = int(time.time()) - process.starttime
        if process.timeout < duration:
            return True
        return False

    def killTimeoutProcess(self, force=False, exception=False):
        alive = False
        sig_value = signal.SIGTERM
        if force:
            sig_value = signal.SIGKILL

        for step in self.step_list:
            for process in step.process_info:
                if process.pid == MAX_PID_NUM:
                    continue

                if not self.isProcessTimeout(process):
                    continue

                status = stf_utils.getPidStatus(process.pid)
                if status == 'N':
                    continue

                if exception:
                    raise Exception('Cleanup Error: %s %d status is %s - %s' % (
                    process.processDesc, process.pid, status, process.status))

                alive = True
                logger.info('%s %d status is %s - %s' %(process.descripton, process.pid, status, process.status))
                os.kill(process.pid, sig_value)
        if alive:
            time.sleep(5)
        return alive

    def terminateTimeoutSteps(self):
        alive = self.killTimeoutProcess()
        if not alive:
            return

        alive = self.killTimeoutProcess(True)
        if not alive:
            return

        self.killTimeoutProcess(exception=True)

        
class TestStep(object):
    view = None
    def __init__(self, path, name, mode, mode_argv, module, step_tags, sid):
        self.has_run = False
        self.path = path
        self.name = name
        self.id = sid
        self.mode = mode
        self.mode_argv = mode_argv
        if '~' in module:
            self.module, self.module_argv = module.split('~',1)
        else:
            self.module = module
            self.module_argv = None

        self.step_tags = step_tags
        self.tms_ids = None
        self.starttime = None
        self.endtime = None
        # exitcode could be 0(success) or 1(failed)
        self.exitcode = 0
        self.status = 'no'
        self.fatal_error = None
        self.stdout = None
        self.stderr = None
        # key is the processIndex, eg: 0 1 2 3 4 5 6 7 8, value is ProcessInfo Instance
        self.process_info = []

    def addProcess(self, process):
        self.process_info.append(process)

    def preCheck(self):
        logger.info('PRECHECK %s ...' % self.path)
        m = modules.getInstance(self.module)
        if m is None:
            raise Exception('Module %s not found.', self.module)

        m.preCheck(self)

    def run(self):
        self.has_run = True
        m = modules.getInstance(self.module)
        if m is None:
            raise Exception('Module %s not found.' % self.module)

        logger.info('RUN %s ...' % self.path)

        try:
            self.starttime = time.time()
            m.run(self)
        except BaseException, e:
            logger.error(str(e))
            self.fatal_error = str(e)
            self.has_failed = True
        finally:
            self.endtime = time.time()
            self.elapsed_time = "{0:.6f}".format(self.endtime - self.starttime)
            for tp in self.process_info:
                variables.parseStdout(tp.stdout, report)


class TestProcess(object):
    def __init__(self):
        #the short description of the process
        self.description = ""
        self.starttime = None
        self.endtime = None
        self.exitcode = 0
        self.status = 'no'
        self.fatal_error = None
        self.stdout = None
        self.stderr = None
        self.pid = MAX_PID_NUM
        self.timeout = 0