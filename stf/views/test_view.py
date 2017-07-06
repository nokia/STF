import os
import re
from stf.views.base_view import *
from stf.lib.stf_utils import *
from stf.lib.logging.logger import Logger
from stf.lib.SParser import SParser, GRE, SRE
from stf.managers.test_case_manager import TestSuite, TestCase, TestStep


logger = Logger.getLogger(__name__)

class STFTestView(STFBaseView):
    def __init__(self, plugins):
        super(STFTestView, self).__init__(plugins)

    def parseArguments(self, parser, argv):
        parser.add_argument("-c", "--case", nargs='+', help="file or directory path, multi paths split by whitespace", required=False)
        parser.add_argument("-s", "--section", help="The test section name (without Test:)", required=False)
        parser.add_argument("-t", "--tags", help="To filter the cases by tags", required=False)
        parser.add_argument("-i", "--ini", help="the ini file path", required=False)
        parser.add_argument("-p", "--pipeline", help="The test section pipeline name or deploy parallel number", required=False)
        parser.add_argument("--log",help="the name of log flag, The log file will be stf_logFlag",required=False)
        args = parser.parse_args(argv)

        variables = self.plugins.getInstance('variable')
        variables.init(args.ini, pipeline=args.pipeline, section=args.section)
        self.addCaseSource(args.case)
        self.addTags(args.tags)

    def run(self):
        for case_suite in self.report.case_suite_list:
            case_suite.run()

        self.report.reportToTms()
        self.report.generateXmlReport()

    def preCheck(self):
        self._detectJenkins()
        # initialize tms here, _findTests has dependency on this
        self.report = self.plugins.getInstance('report')
        self.report.init()
        self._findTests()

        for case_suite in self.report.case_suite_list:
            case_suite.preCheck()

    def _findTestWithSteps(self, root, d, test_suite, direct=False):
        if not d.startswith("stf__"):
            return False

        if d.endswith("_"):
            return False

        mo = GRE.match(d)

        if not mo:
            if direct:
                return False
            errorAndExit('case directory name illegal: %s' % d)

        tags = mo.group('tags')
        tms_ids = mo.group('cases')
        path = os.path.join(root, d)
        logger.info('found test case: %s' % (path))
        if tags:
            tags = tags.split('__', 1)[1].split('~')
            # apply filter
            if self._omitByTagFilter(tags):
                return True

        if tms_ids:
            tms_ids = tms_ids.split('__', 1)[1].split('~')

        # only setup and teardown cases have no and must have no tms ids
        self.global_test_id += 1
        test_id = 'stf-%s-%s' % (str(self.global_test_id), d)
        # tms_ids not None, mean a regular case rather than setup and teardown
        if tms_ids:
            test_ins = TestCase(path, d, tags, tms_ids, test_id)
            test_suite.addCase(test_ins)
            self._findSteps(test_ins, path)
            return True

        # if tms_ids is None:
        if 'setup' in tags:
            if test_suite.setup:
                raise Exception(
                    'Duplicate setup case: %s . Notice: Can only has one single setup case in a directory' % path)
            test_suite.setup = TestCase(path, d, tags, tms_ids, test_id)
            self._findSteps(test_suite.setup, path)
            return True

        if 'teardown' in tags:
            if test_suite.teardown:
                raise Exception(
                    'Duplicate teardown case: %s . Notice: Can only has one single setup case in a directory' % path)
            test_suite.teardown = TestCase(path, d, tags, tms_ids, test_id)
            self._findSteps(test_suite.teardown, path)
            return True

        raise Exception('Test cases must have tms id if they are neither setup nor teardown cases.')

    def _findTestWithoutSteps(self, root, f, test_suite, direct=False):
        if not f.startswith("stfs"):
            return False

        if f.endswith("_"):
            return False

        mo = SRE.match(f)
        if not mo:
            if direct:
                return False
            errorAndExit('case file name illegal: %s' % f)

        tags = mo.group('tags')
        tms_ids = mo.group('cases')

        mode = mo.group('mode')
        mode_argv = mo.group('mode_parameter')
        module = mo.group('module')

        tags = tags.split('__', 1)[1].split('~')
        # apply filter
        if self._omitByTagFilter(tags):
            return True

        path = os.path.join(root, f)
        logger.info('found test case: %s' % (path))
        if tms_ids:
            tms_ids = tms_ids.split('__', 1)[1].split('~')

        # only setup and teardown cases have no and must have no tms ids
        self.global_test_id += 1

        test_ins = TestCase(path, f, tags, tms_ids, 'stf-%s-%s' % (str(self.global_test_id), f))
        test_ins.module = module
        step_ins = TestStep(path, f, *SParser.parseS(f))
        test_ins.step_list.append(step_ins)

        test_suite.addCase(test_ins)
        return True

    def _findTests(self):
        self.prepareCaseSourceList()
        #pass view to TestSuite and TestCase
        TestSuite.setView(self)
        TestCase.setView(self)
        for test_dirs in self.case_dir_list:
            # d must be absolute path here
            #if test_dirs itself is a case
            test_root, test_name = os.path.split(test_dirs.rstrip('\/'))

            test_suite = TestSuite(test_root)
            if self._findTestWithoutSteps(test_root, test_name, test_suite, True):
                self.report.case_suite_list.append(test_suite)
                continue

            if self._findTestWithSteps(test_root, test_name, test_suite, True):
                self.report.case_suite_list.append(test_suite)
                continue

            del test_suite

            #else find the case in this directory
            for root, subdirs, files in os.walk(test_dirs):
                # start a dir contains test_dir
                # only one setup and teardown case in this subdir
                test_suite = TestSuite(root)
                for f in files:
                    self._findTestWithoutSteps(root, f, test_suite)

                for d in subdirs:
                    if not d.startswith("stf"):
                        continue

                    if d.endswith("_"):
                        continue

                    if d.startswith("stf__"):
                        self._findTestWithSteps(root, d, test_suite)

                    if d.startswith("stfs"):
                        self._findTestWithoutSteps(root, d, test_suite)

                #No regular case found in current test suite
                if test_suite.caseNumbers() < 1:
                    continue

                self.report.case_suite_list.append(test_suite)

    def _omitByTagFilter(self, tags):
        if not self.is_tag_filter:
            return False
        if bool(set(self.tags_filter) & set(tags)):
            return False
        return True

    def _findSteps(self, test_ins, case_dir):
        step_list = []
        num_list = []
        for s in os.listdir(case_dir):
            abs_file = os.path.join(case_dir, s)

            if s.endswith("_"):
                continue

            if not s.startswith("s"):
                errorAndExit('Case file name not starts with s :%s' % abs_file)

            if not os.path.isfile(abs_file):
                errorAndExit('%s is not a regular file.' %abs_file)

            mo = SRE.match(s)

            if not mo:
                errorAndExit('Case file name illegal: %s' % abs_file)

            if s.startswith('s00'):
                errorAndExit('Illegal infinite symbol in file name: %s' % abs_file)

            n = s.split('__')[0][1:]
            if n in num_list:
                errorAndExit('Case %s has the duplicated priority number' % self.case_dir)

            num_list.append(n)
            step_list.append(s)

        try:
            step_list.sort(key=lambda x: int(x.split('__')[0].split('~')[0][1:]))
        except:
            errorAndExit('Case file name illegal with unknown issue')

        for s in step_list:
            path = os.path.join(case_dir, s)
            step_ins = TestStep(path, s, *SParser.parseS(s))
            test_ins.addStep(step_ins)








