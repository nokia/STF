#!/usr/bin/env python
import os
from abc import ABCMeta, abstractmethod
from stf.managers.plugin_manager import *
from stf.managers.module_manager import *
from stf.lib.stf_utils import *
from stf.lib.logging.logger import Logger
import argparse

logger = Logger.getLogger(__name__)

class STFBaseView(object):
    def __init__(self, plugins):
        self.plugins = plugins
        self.process = None
        self.report = None
        self.variables = self.plugins.getInstance('variable')
        self.mode = 'local'
        self.case_dir_list = []
        self.global_test_id = 0
        self.source_map = {'tms': 'report', 'git': 'gitrepo', 'remote': 'ssh', 'localhost': 'localhost'}
        self.tags_filter = ['setup', 'teardown']
        self.is_tag_filter = False

    @abstractmethod
    def preCheck(self):
        pass

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def parseArguments(self, parser, argv):
        pass

    def _detectJenkins(self):
        JOB_NAME = os.environ.get('JOB_NAME')
        WORKSPACE = os.environ.get('WORKSPACE')
        if JOB_NAME and WORKSPACE:
            self.mode = 'jenkins'

    def addTags(self, tags):
        if tags is None:
            return
        logger.info('You specified tags with --tags in command line: %s' % tags)
        self.is_tag_filter = True
        self.tags_filter.extend(tags.split(','))

    def _omitByFilter(self):
        return False

    def addCaseSource(self, case_dirs):
        # from command line
        if case_dirs is None:
            return
        logger.info('You specified case directory with --case in command line: %s' % case_dirs)
        for case_dir in case_dirs:
            self._prepareCaseSource(case_dir)

    # case dir list comes from tms, git clone, or scp, or local
    def prepareCaseSourceList(self):
        #from ini file
        if self.variables.parser is None:
            logger.info("No ini file specified")
            return

        l = self.variables.getTestValueAsList('source')
        logger.info("start to prepare case %s", str(l))
        
        if l is None:
            if len(self.case_dir_list) == 0:
                logger.warning("No cases will be performed since you did not specify --case in command line, too")
            return

        for i in l:
            logger.info("try to prepare case %s", i)
            self._prepareCaseSource(i)

    def _prepareCaseSource(self, i):
        if i is None:
            return

        if '@@' not in i:
            i = 'localhost@@' + i
        func, arg = i.split('@@', 1)
        if func not in self.source_map:
            raise Exception(" '%s' not supported as test case 'source' in [Test], choose one of %s " % (
            func, self.source_map.keys()))

        if i.startswith('tms@@') and self.mode == 'local':
            raise Exception('We can only get case source from tms in Jenkins.')

        if func == 'localhost':
            if arg.startswith('/'):
                self.case_dir_list.append(arg)
            else:
                self.case_dir_list.append(os.path.join(os.getcwd(),arg))
        else:
            # call prepareCaseSourceList of each plugin
            caseDir = self.plugins.getInstance(self.source_map[func]).prepareCaseSourceList(arg)
            self.case_dir_list.append(caseDir)




