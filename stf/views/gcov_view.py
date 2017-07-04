import os
import re
import subprocess
from stf.views.base_view import *
from stf.lib.stf_utils import *
from stf.lib.logging.logger import Logger
from stf.lib.SParser import SParser, GRE, SRE
from stf.managers.test_case_manager import TestSuite, TestCase, TestStep


logger = Logger.getLogger(__name__)

class STFGcovView(STFBaseView):
    def __init__(self, plugins):
        super(STFGcovView, self).__init__(plugins)
        self.build_command = ''

    def parseArguments(self, parser, argv):
        parser.add_argument("-b", "--build", nargs='+', help="build command (e.g. make all, g++ a.cpp -o a)", required=True)
        parser.add_argument("-e", "--exclude", help="excluded file for directory path", required=False)
        args = parser.parse_args(argv)
        self.build_command = args.build
        self.path = '%s/%s:%s' % (os.path.dirname(os.path.dirname(__file__)), 'helper', os.environ['PATH'])

    def run(self):
        subprocess.call(self.build_command, env={"PATH": self.path}, shell=True)


    def preCheck(self):
        self._detectJenkins()
        try:
            subprocess.call(['bash', '--version'])
        except OSError as e:
            if e.errno == os.errno.ENOENT:
                errorAndExit('bash not found on current system.')
            raise

    def addCaseSource(self, case_dir):
        pass

    def _findTests(self):
        pass

    #always return false, means delpoy view won't affected by any filter
    def _omitByTagFilter(self, tags):
        return False



