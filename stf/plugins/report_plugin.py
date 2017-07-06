from stf.plugins.base_plugin import STFBasePlugin
from stf.lib.stf_utils import *
import re
import os
import datetime
import time
from stf.lib.logging.logger import Logger
from xml.dom.minidom import Document
import six

logger = Logger.getLogger(__name__)

class STFReportPlugin(STFBasePlugin):
    def __init__(self, plugins):
        super(STFReportPlugin, self).__init__(plugins)
        self.tms_name = None
        self.tms = None
        self.case_list = []
        self.case_suite_list = []
        self.case_status = {}
        self.mode = 'local'
        self.const_status = {'PASS': 'PASS', 'pass': 'PASS', 'Pass': 'PASS', 'FAIL': 'FAIL', 'Fail': 'FAIL', 'fail': 'FAIL' }

    def init(self):
        try:
            if self.plugins.getInstance('variable').parser is None:
                self.mode = 'local'
                logger.warning('Will not get and push info to test case management system since you did not provide ini file')
                return

            self.mode = self.plugins.getInstance('variable').get('mode')
            self.tms_name = self.plugins.getInstance('variable').get('tms')
            if self.tms_name is None:
                self.mode = 'local'

            if self.mode == 'local':
                logger.info('report mode is local, no TMS will be updated...')
                return

            self.tms = self.plugins.getInstance(self.tms_name)
            logger.info('initialize %s plugin' % self.tms_name)
            self.tms.init()
            logger.info('initialize %s case list' % self.tms_name)
            self.case_list = self.tms.getCaseList()
        except Exception,e:
            info = 'During report plugin initialize: %s' % (str(e))
            errorAndExit(info)

    def setCasePass(self, id):
        self.setCaseStatus(id, 'PASS')

    def setCaseFail(self, id):
        self.setCaseStatus(id, 'FAIL')

    def setCaseListFail(self, id_list):
        if id_list is None:
            return
        try:
            for c in id_list:
                self.setCaseFail(c)
        except Exception,e:
            logger.error(str(e))

    def setCaseListPass(self, id_list):
        if id_list is None:
            return
        try:
            for c in id_list:
                self.setCasePass(c)
        except Exception, e:
            logger.error(str(e))

    def setCaseStatus(self, id, status='FAIL'):
        if self.mode == 'local':
            return

        if self.tms is None:
            errorAndExit('call init() of report plugin first.')

        if id not in self.case_list:
            logger.warning('case id %s does not exist on %s' %(id, self.tms_name))
            return

        if status is None:
            status = 'FAIL'

        if status not in self.const_status:
            logger.error('Unsupported case status: %s' % status)
            return

        if id in self.case_status:
            if self.const_status[status] == 'PASS':
                logger.info('Case %s status already be set with %s and will not override by new status: %s' % (id, self.case_status[id], status))
                return

            logger.info('Case %s status already be set with %s and will override by new status: %s' %(id, self.case_status[id], status))

        self.case_status[id] = status

    def reportToTms(self):
        if self.mode == 'local':
            return
        logger.info('update tms ...')
        self.tms.updateStatusMap(self.case_status)

    def generateXmlReport(self):
        """
        Generates the XML reports to a given TestInfo object.
        """
        try:
            doc = Document()
            testsuites= doc.createElement('testsuites')
            doc.appendChild(testsuites)
            parentElment = testsuites
            xml_content = None
            for cs in self.case_suite_list:
                if not cs.has_run:
                    break
                testsuite = doc.createElement('testsuite')
                testsuites.appendChild(testsuite)
                testsuite.setAttribute('name',cs.path)
                testsuite.setAttribute('tests','1')

                testsuite.setAttribute('failures','0')
                xml_properties = doc.createElement('properties')
                testsuite.appendChild(xml_properties)
                property = doc.createElement('property')
                xml_properties.appendChild(property)

                systemout=doc.createElement('system-out')
                cdata = doc.createCDATASection("")
                systemout.appendChild(cdata)
                testsuite.appendChild(systemout)


                systemerr= doc.createElement('system-err')
                cdata=doc.createCDATASection("")
                systemerr.appendChild(cdata)
                testsuite.appendChild(systemerr)
                """
                Appends a testcase section to the XML document.
                """
                testCaseDurs = 0.0
                failures = 0
                for c in cs.case_list:
                    if not c.has_run:
                        break
                    testcase = doc.createElement('testcase')
                    testcase.setAttribute('classname','STF')
                    testcase.setAttribute('name',c.id)
                    testcase.setAttribute('time',six.text_type(c.elapsed_time))
                    failure = c.exitcode
                    if failure == 1:
                        error= doc.createElement('error')
                        testcase.appendChild(error)
                        error.setAttribute('type','error')
                        error.setAttribute('message',c.fatal_error)
                        cdata = doc.createCDATASection(c.__dict__)
                        error.appendChild(cdata)
                        failures = failures + 1
                    testsuite.appendChild(testcase)
                testsuite.setAttribute('errors', six.text_type(failures))
                testsuite.setAttribute('time', cs.elapsed_time)
                xml_content = doc.toprettyxml(indent='\t',encoding='UTF8')

            if xml_content is None:
                return

            if not os.path.exists('./testcase_reports'):
                os.mkdir('./testcase_reports')

            date = datetime.datetime.now().strftime("%Y%m%d-"+ time.tzname[1] + "-%H%M%S.%f")
            filename = os.path.join('./testcase_reports','TEST-STF-%s.xml' % date)
            with open(filename, 'wb') as report_file:
                report_file.write(xml_content)
        finally:
            pass




