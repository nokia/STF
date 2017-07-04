import re
import sys
import ssl
import json
import urllib
import warnings
import requests
import datetime
from base64 import b64encode
from urllib2 import Request, urlopen
from requests.exceptions import ProxyError
from stf.plugins.base_plugin import STFBasePlugin
from stf.lib.logging.logger import Logger


ERROR_CANNOT_FIND_FILE = 'Cannot find file: %s'
ERROR_CANNOT_CONNECT_JIRA = 'Cannot connect to JIRA server.'
ERROR_NO_STATUS = 'Invalid status: %s'
WARNING_NO_RESULT = '%s does not exist.'

logger = Logger.getLogger(__name__)

class STFZephyrPluginError(BaseException):
    """If error, raise it."""
    pass

class Project:
    def __init__(self):
        self.id = ''
        self.key = ''
        self.name = ''

    def display(self):
        logger.debug('Project - id: %s, key: %s, name: %s' % (self.id, self.key, self.name))


class Worker:
    def __init__(self):
        self.key = ''
        self.name = ''
        self.displayName = ''
        self.emailAddress = ''

    def display(self):
        logger.debug('Worker - key : %s, name: %s, displayName: %s, emailAddress: %s' % (self.key, self.name, self.displayName, self.emailAddress))

class TmsCase:
    def __init__(self):
        self.id = ''
        self.key = ''
        self.summary = ''
        self.description = ''
        self.reference = ''
        self.project = None
        self.creator = None
        self.reporter = None
        self.assignee = None
        self.version_name = ''
        self.cycle_name = ''
    def display(self):
        logger.debug('TmsCase - id : %s, key: %s, summary: %s, description: %s, reference: %s' % (self.id, self.key, self.summary, self.description, self.reference))
        if self.project is not None:
            self.project.display()
        if self.creator is not None:
            self.creator.display()
        if self.reporter is not None:
            self.reporter.display()
        if self.assignee is not None:
            self.assignee.display()

class STFZephyrPlugin(STFBasePlugin):
    warnings.filterwarnings('ignore')

    def __init__(self, plugins):
        super(STFZephyrPlugin, self).__init__(plugins)
        self.plugins = plugins

        self.zapiBaseUrl = ''
        self.username = ''
        self.password = ''
        self.authentication = ''
        self.projectId = ''
        self.projectName = ''
        self.versionId = ''
        self.versionName = ''
        self.cycleId = ''
        self.cycleName = ''
        useRegularExpression = False
        self.statusNumber = {'PASS': 1, 'FAIL': 2, 'WIP': 3, 'BLOCKED': 4, 'CANCEL': 5, 'UNEXECUTED': -1}

        self.urlProjectList = ''
        self.keyOptions = 'options'
        self.keyLabel = 'label'
        self.keyValue = 'value'
        self.keyName = 'name'
        self.keyUnreleasedVersions = 'unreleasedVersions'
        self.keyExecutions = 'executions'
        self.keyIssueKey = 'issueKey'
        self.keyProjectId = 'projectId'
        self.keyVersionId = 'versionId'
        self.keyCycleId = 'cycleId'

    def init(self):
        conf = self.plugins.getInstance("variable")

        self.zapiBaseUrl = conf.get("jira_rest_url", "Zephyr")
        if self.zapiBaseUrl is None or self.zapiBaseUrl == '':
            errmsg = 'Error: [Zephyr] invalid jira_rest_url value.'
            logger.error(errmsg)
            raise STFZephyrPluginError(errmsg)

        self.urlProjectList = self.zapiBaseUrl + '/zapi/latest/util/project-list'
        self.urlVersionList = self.zapiBaseUrl + '/zapi/latest/util/versionBoard-list'
        self.urlCycle = self.zapiBaseUrl + '/zapi/latest/cycle'
        self.urlExecution = self.zapiBaseUrl + '/zapi/latest/execution'

        self.username = conf.get("username", "Zephyr")
        if self.username is None or self.username == '':
            errmsg = 'Error: [Zephyr] invalid username value.'
            logger.error(errmsg)
            raise STFZephyrPluginError(errmsg)

        self.password = conf.get("password", "Zephyr")
        if self.password is None or self.password == '':
            errmsg = 'Error: [Zephyr] invalid password value.'
            logger.error(errmsg)
            raise STFZephyrPluginError(errmsg)
        self.authentication = (self.username, self.password)

        self.projectName = conf.get("project_name", "Zephyr")
        if self.projectName is None or self.projectName == '':
            errmsg = 'Error: [Zephyr] invalid project_name value.'
            logger.error(errmsg)
            raise STFZephyrPluginError(errmsg)

        self.versionName = conf.get("version_name", "Zephyr")
        if self.versionName is None or self.versionName == '':
            errmsg = 'Error: [Zephyr] invalid version_name value.'
            logger.error(errmsg)
            raise STFZephyrPluginError(errmsg)

        self.cycleName = conf.get("cycle_name", "Zephyr")
        if self.cycleName is None or self.cycleName == '':
            errmsg = 'Error: [Zephyr] invalid cycle_name value.'
            logger.error(errmsg)
            raise STFZephyrPluginError(errmsg)

        self.useRegularExpression = conf.get("use_regular_expression", "Zephyr")

        self.projectId = self.getProjectId(self.projectName)
        if self.projectId == '':
            errmsg = 'Error: [Zephyr] getProjectId() failed with project_name:' + self.projectName
            logger.error(errmsg)
            raise STFZephyrPluginError(errmsg)

        self.versionId = self.getVersionId(self.versionName)
        if self.versionId == '':
            errmsg = 'Error: [Zephyr] getVersionId() failed with project_name:' + self.projectName + ', version_name:' + self.versionName
            logger.error(errmsg)
            raise STFZephyrPluginError(errmsg)
        self.cycleId = self.createCycle(self.cycleName)

    def run_ut(self):
        logger.debug("I AM running in Zephyr")
        #print(self.authentication)
        logger.debug(self.projectId)
        logger.debug(self.versionId)
        logger.debug(self.cycleId)
        logger.debug(self.getExistedCycleNames())
        logger.debug(self.getExistedTestNames(self.cycleId))
        logger.debug(self.getCaseList())
        case1 = self.getCaseInfo("CSFOAMTST-123")
        if case1 is not None:
            case1.display()
        else:
            logger.debug("CSFOAMTST-123 not exist.")
        case2 = self.getCaseInfo("CSFOAMTST-321")
        if case2 is not None:
            case2.display()
        else:
            logger.debug("CSFOAMTST-321 not exist.")
        """
        print(self.getCaseList(None, None, "test*"))
        print(self.getCaseList(None, None, "demo*"))
        print(self.getFeatureName("CSFTST-13"))
        print(self.getCaseList("Zephyr plugin"))

        self.updateCaseStatus("CSFTST-1", "PASS")
        self.updateCaseStatus("CSFTST-2", "FAIL")
        smap = {'CSFTST-1': 'PASS', 'CSFTST-2': 'FAIL'}
        self.updateStatusMap(smap)

        print(self.getStepId("CSFTST-1", "test02_s2"))
        print(self.getStepId("CSFTST-2", "test02_s1"))
        self.updateStepStatus("CSFTST-2", "test02_s2", "PASS")
        self.refreshCaseStatus(["CSFTST-1", "CSFTST-2", "CSFTST-4"])
        """
    def getCaseInfo(self, CaseId):
        try:
            url = self.zapiBaseUrl + '/api/2/issue/' + CaseId.strip('\n')
            response = requests.get(url, auth=self.authentication, verify=False)
            responst_body = json.loads(response.text)
            if not responst_body.has_key('errorMessages') and responst_body['fields']['issuetype']['name'] == 'Test':
                case = TmsCase()

                case.id = responst_body['id']
                case.key = responst_body['key']
                case.summary = responst_body['fields']['summary']
                case.description = responst_body['fields']['description']
                case.reference = responst_body['fields']['customfield_15308']

                case.creator = Worker()
                case.creator.name = responst_body['fields']['creator']['name']
                case.creator.key = responst_body['fields']['creator']['key']
                case.creator.displayName = responst_body['fields']['creator']['displayName']
                case.creator.emailAddress = responst_body['fields']['creator']['emailAddress']

                case.reporter = Worker()
                case.reporter.name = responst_body['fields']['reporter']['name']
                case.reporter.key = responst_body['fields']['reporter']['key']
                case.reporter.displayName = responst_body['fields']['reporter']['displayName']
                case.reporter.emailAddress = responst_body['fields']['reporter']['emailAddress']

                case.assignee = Worker()
                case.assignee.name = responst_body['fields']['assignee']['name']
                case.assignee.key = responst_body['fields']['assignee']['key']
                case.assignee.displayName = responst_body['fields']['assignee']['displayName']
                case.assignee.emailAddress = responst_body['fields']['assignee']['emailAddress']

                case.project = Project()
                case.project.id = responst_body['fields']['project']['id']
                case.project.key = responst_body['fields']['project']['key']
                case.project.name = responst_body['fields']['project']['name']

                return case
            else:
                return None
        except ProxyError:
            logger.error(ERROR_CANNOT_CONNECT_JIRA)
        return WARNING_NO_RESULT % 'Case'

    def updateCaseStatus(self, caseName, Status):
        if self.isValidCaseInput(caseName, Status):
            caseList = self.buildValidList(caseName)
            statusList = self.buildValidList(Status)
            if len(caseList) == 0:
                logger.error(WARNING_NO_RESULT % 'Case')
                return False
        else:
            return False

        result = True
        try:
            cycleId = self.createCycle(self.cycleName)
            if cycleId == '':
                logger.error("Error: create clcyle.")
                return False
            existCaseList = self.getExistedTestNames(cycleId)
            for index, case in enumerate(caseList):
                if case not in enumerate(existCaseList):
                    self.addTestToCycle(cycleId, case)
                executionId = self.getExecutionId(case)
                try:
                    number = self.statusNumber[statusList[index]]
                except KeyError:
                    logger.error(ERROR_NO_STATUS % statusList[index])
                    return False
                url = self.zapiBaseUrl + '/zapi/latest/execution/' + str(executionId) + '/execute'
                headers = {'Content-Type': 'application/json'}
                result = json.dumps({'status': str(number)})
                response = requests.put(url, data=result, headers=headers, auth=self.authentication, verify=False)
                result = result and (response.status_code == 200)
        except ProxyError:
            logger.error(ERROR_CANNOT_CONNECT_JIRA)
            return False
        return result

    def updateStatusMap(self, map):
        if not isinstance(map, dict):
            return False

        statusList = []
        testList = []
        for testcaseName in map.keys():
            statusList += [map.get(testcaseName)]
            testList += [testcaseName]

        if (self.isValidCaseInput(testList, statusList)):
            return self.updateCaseStatus(testList, statusList)
        else:
            return False

    def updateStepStatus(self, caseName, TestStep, Status):
        if caseName is None or TestStep is None or Status is None:
            return
        try:
            executionId = self.getExecutionId(caseName)
            if executionId == '':
                logger.error(WARNING_NO_RESULT % 'Case')
                return False
            stepResultId = self.getStepResultId(executionId, caseName, TestStep)
            if stepResultId == '':
                logger.error(WARNING_NO_RESULT % 'Step')
                return False

            try:
                number = self.statusNumber[Status]
            except KeyError:
                logger.error(ERROR_NO_STATUS % Status)
                return False
            url = self.zapiBaseUrl + '/zapi/latest/stepResult/' + str(stepResultId)
            headers = {'Content-Type': 'application/json'}
            result = json.dumps({'status': str(number)})
            response = requests.put(url, data=result, headers=headers, auth=self.authentication, verify=False)
            return response.status_code == 200
        except ProxyError:
            logger.error(ERROR_CANNOT_CONNECT_JIRA)
            return False

    def getCaseList(self, featureName = None, campaignType = None, title = None):
        result = []

        baseURL = self.zapiBaseUrl + '/api/2/search?jql='
        projectURL = 'project="' + self.projectName + '"'
        featureURL = ''
        if featureName is not None:
            featureURL = '&"epic link"="' + str(featureName) + '"'
        campaignURL = ''
        if campaignType is not None:
            campaignURL = '&cf[11720]["value"]="' + str(campaignType) + '"'
        titleURL = ''
        if title is not None and self.useRegularExpression == 'False':
            titleURL = '&summary~"' + str(title) + '"'
        testURL = '&issueType="Test"'

        try:
            url = baseURL + urllib.quote(projectURL + featureURL + campaignURL + titleURL + testURL, ':/?')
            response = requests.get(url, auth=self.authentication, verify=False)
            response_body = json.loads(response.text)
            #print json.dumps(response_body)
            for case in response_body['issues']:
                result += [case['key']]

            if self.useRegularExpression == 'True':
                result = self.filterTestsInIllegibilityTitle(result, title)
            if len(result) == 0:
                logger.error(WARNING_NO_RESULT % 'Case')
            return result
        except ProxyError:
            logger.error(ERROR_CANNOT_CONNECT_JIRA)
            return False


    def getStepResultKey(self, projectId, versionId, cycleId, executionId, testcaseName, TestStep, key):
        # for test only
        stepResultId = self \
            .getStepResultId(projectId, versionId, cycleId, executionId, testcaseName, TestStep)
        url = self.zapiBaseUrl + '/zapi/latest/stepResult/' + str(stepResultId)
        response = requests.get(url, auth=self.authentication, verify=False)
        response_body = json.loads(response.text)
        # print json.dumps(response_body)
        return response_body[key]

    def getExecutionKey(self, projectId, versionId, cycleId, executionId, key):
        # for test only
        url = self.zapiBaseUrl + '/zapi/latest/execution/' + str(executionId)
        response = requests.get(url, auth=self.authentication, verify=False)
        response_body = json.loads(response.text)
        return response_body['execution'][key]

    def getStepResultId(self, executionId, testcaseName, stepName):
        stepId = self.getStepId(testcaseName, stepName)
        url = self.zapiBaseUrl + '/zapi/latest/stepResult?executionId=' + str(executionId)
        response = requests.get(url, auth=self.authentication, verify=False)
        response_body = json.loads(response.text)
        resultId = 0
        for stepResult in response_body:
            if stepResult['stepId'] == stepId:
                resultId = stepResult['id']
        return resultId

    def getIssueId(self, testcaseName):
        url = self.zapiBaseUrl + '/api/2/issue/' + str(testcaseName)
        response = requests.get(url, auth=self.authentication, verify=False)
        response_body = json.loads(response.text)
        # print json.dumps(response_body)
        return response_body['id']

    def getStepId(self, testcaseName, stepName):
        issueId = self.getIssueId(testcaseName)
        url = self.zapiBaseUrl + '/zapi/latest/teststep/' + str(issueId)
        response = requests.get(url, auth=self.authentication, verify=False)
        response_body = json.loads(response.text)
        # print json.dumps(response_body)
        stepId = ''
        for step in response_body:
            for k in step.keys():
                if step[k] == stepName:
                    stepId = step['id']
        return stepId

    def getExecutionIdBatch(self, projectId, versionId, cycleId, TestArray):
        executionId = []
        url = self.zapiBaseUrl + \
            '/zapi/latest/execution?cycleId=' + str(cycleId) + \
            '&versionId=' + str(versionId) + \
            '&projectId=' + str(projectId)
        response = requests.get(url, auth=self.authentication, verify=False)
        response_body = json.loads(response.text)
        # print json.dumps(response_body)
        for caseName in TestArray:
            for execution in response_body['executions']:
                if execution['issueKey'] == caseName.strip('\n'):
                    executionId += [execution['id']]
        return executionId

    def getExecutionId(self, caseName):
        url = self.zapiBaseUrl + \
            '/zapi/latest/execution?cycleId=' + str(self.cycleId) + \
            '&versionId=' + str(self.versionId) + \
            '&projectId=' + str(self.projectId)
        response = requests.get(url, auth=self.authentication, verify=False)
        response_body = json.loads(response.text)
        # print json.dumps(response_body)
        executionId = 0
        for execution in response_body['executions']:
            if execution['issueKey'] == caseName:
                executionId = execution['id']
        return executionId

    def getCycleId(self, cycleName):
        url = '%s?%s=%s&%s=%s' % (self.urlCycle, self.keyProjectId, self.projectId, self.keyVersionId, self.versionId)
        response = requests.get(url, auth=self.authentication, verify=False)
        response_body = json.loads(response.text)
        # print json.dumps(response_body)
        cycleId = ''
        for cycle in response_body:
            if isinstance(response_body[cycle], dict):
                if response_body[cycle]['name'] == cycleName:
                    cycleId = cycle
        return cycleId

    def getVersionId(self, versionName):
        url = '%s?%s=%s' % (self.urlVersionList, self.keyProjectId, self.projectId)
        response = requests.get(url, auth=self.authentication, verify=False)
        response_body = json.loads(response.text)
        # print json.dumps(response_body)
        versionId = ''
        for version in response_body[self.keyUnreleasedVersions]:
            if version[self.keyLabel] == versionName:
                versionId = version[self.keyValue]
        return versionId

    def getProjectId(self, projectName):
        response = requests.get(self.urlProjectList, auth=self.authentication, verify=False)
        response_body = json.loads(response.text)
        #print(json.dumps(response_body))
        projectId = ''
        for project in response_body[self.keyOptions]:
            if project[self.keyLabel] == projectName:
                projectId = project[self.keyValue]
        return projectId

    def getExistedCycleNames(self):
        url = '%s?%s=%s&%s=%s' % (self.urlCycle, self.keyProjectId, self.projectId, self.keyVersionId, self.versionId)
        response = requests.get(url, auth=self.authentication, verify=False)
        response_body = json.loads(response.text)
        # print json.dumps(response_body)
        array = []
        for cycle in response_body:
            if isinstance(response_body[cycle], dict):
                array += [response_body[cycle][self.keyName]]
        return array

    def getExistedTestNames(self, cycleId):
        url = '%s?%s=%s&%s=%s&%s=%s' % (self.urlExecution, self.keyProjectId, self.projectId, self.keyVersionId, self.versionId, self.keyCycleId, cycleId)
        response = requests.get(url, auth=self.authentication, verify=False)
        response_body = json.loads(response.text)
        # print json.dumps(response_body)
        array = []
        for execution in response_body[self.keyExecutions]:
            array += [execution[self.keyIssueKey]]
        return array

    def createCycle(self, cycleName):
        if cycleName in self.getExistedCycleNames():
            return self.getCycleId(cycleName)
        headers = {"Authorization": " Basic " + b64encode(self.username + ":" + self.password),
                   "Content-Type": "application/json"}
        startDate = datetime.datetime.now().strftime('%d/%b/%y')
        values = json.dumps(
            { "clonedCycleId": "",
              "name": cycleName,
              "build": "",
              "environment": "",
              "description": "AACI Zephyr plugin",
              "startDate": startDate,
              "endDate": "",
              "projectId": self.projectId,
              "versionId": self.versionId})
        url = self.zapiBaseUrl + '/zapi/latest/cycle'
        request = Request(url, data=values, headers=headers)
        response = json.load(urlopen(request, context=ssl._create_unverified_context()))
        #print json.dumps(response)
        return response['id']

    def deleteCycle(self, projectId, versionId, cycleName):
        values = json.dumps({})
        headers = {"Authorization": " Basic " + b64encode(self.username + ":" + self.password),
                   "Content-Type": "application/json"}
        cycleId = self.getCycleId(cycleName)
        url = self.zapiBaseUrl + '/zapi/latest/cycle/' + str(cycleId)
        request = Request(url, data=values, headers=headers)
        request.get_method = lambda: 'DELETE'
        response_body = urlopen(request,context=ssl._create_unverified_context()).read()
        #print response_body
        return cycleId

    def addTestToCycle(self, cycleId, caseList):
        if not isinstance(caseList, list):
            cases = [caseList]
        else:
            cases = caseList

        values = json.dumps({
            "issues": cases,
            "versionId": self.versionId,
            "cycleId": cycleId,
            "projectId": self.projectId,
            "method": "1"
        })
        headers = {"Authorization": " Basic " + b64encode(self.username + ":" + self.password),
                   "Content-Type": "application/json"}
        url = self.zapiBaseUrl + '/zapi/latest/execution/addTestsToCycle/'
        request = Request(url, data=values, headers=headers)
        urlopen(request,context=ssl._create_unverified_context()).read()

    def buildValidList(self, name):
        if not isinstance(name, list):
            return [name]
        return name

    def isValidCaseInput(self, value1, value2):
        if isinstance(value1, list) and isinstance(value2, list) and len(value1) == len(value2):
            for item in value1:
                if not isinstance(item, str):
                    return False
            for item in value2:
                if not isinstance(item, str):
                    return False
            return True
        elif isinstance(value1, str) and isinstance(value2, str):
            return True
        return False

    def getFeatureName(self, featureId):
        baseURL = self.zapiBaseUrl + '/api/2/search?jql='
        projectURL = 'project="' + str(self.projectName) + '"'
        testURL = '&issueType="Epic"'

        #url = baseURL + projectURL + testURL
        url = baseURL + urllib.quote(projectURL + testURL, ':/?')
        response = requests.get(url, auth=self.authentication, verify=False)
        response_body = json.loads(response.text)
        for item in response_body['issues']:
            if item['key'] == featureId:
                return item['fields']['customfield_11210']
        return ''

    def filterTestsInCampaign(self, projectId, versionId, array, campaignType = None):
        if campaignType is not None:
            if campaignType not in ['UT', 'DT', 'FT']:
                return []
            else:
                tempResult = []
                cycleId = self.getCycleId(campaignType)
                testcasesInCampaign = self.getExistedTestNames(projectId, versionId, cycleId)
                for caseName in array:
                    if caseName in testcasesInCampaign:
                        tempResult += [caseName]
                return tempResult
        else:
            return array

    def filterTestsInIllegibilityTitle(self, array, filterText = None):
        if filterText is not None:
            tempResult = []
            for caseName in array:
                if re.search(filterText, caseName):
                    tempResult += [caseName]
            return tempResult
        else:
            return array

    def getCaseRunningStatus(self, testcaseName):
        url = self.zapiBaseUrl + \
            '/zapi/latest/execution?cycleId=' + str(self.cycleId) + \
            '&versionId=' + str(self.versionId) + \
            '&projectId=' + str(self.projectId)
        response = requests.get(url, auth=self.authentication, verify=False)
        response_body = json.loads(response.text)
        #print json.dumps(response_body)
        for execution in response_body['executions']:
            if execution['issueKey'] == testcaseName:
                return execution['executionStatus']
        return '-1'

    def refreshCaseStatus(self, caseName):
        testcaseNameArray = self.buildValidList(caseName)
        for testcaseName in testcaseNameArray:
            number = self.getCaseRunningStatus(testcaseName)
            executionId = self.getExecutionId(testcaseName)
            url = self.zapiBaseUrl + '/zapi/latest/execution/' + str(executionId) + '/execute'
            headers = {'Content-Type': 'application/json'}
            result = json.dumps({'status': str(number)})
            requests.put(url, data=result, headers=headers, auth=self.authentication, verify=False)
