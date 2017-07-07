import sys
import os
import re
import tempfile
import ast
from stf.lib.stf_utils import *
from stf.plugins.base_plugin import STFBasePlugin
from stf.lib.STFParser import STFParser
#from docutils.parsers.rst.directives import path
from stf.lib.logging.logger import Logger

logger = Logger.getLogger(__name__)

IP_POOL = 'Deploy:IP:Dynamic'

class Vhost(object):
    def __init__(self, vhost_name):
        self.name = vhost_name
        self.login = None
        self.IP = None

class Vlab(object):
    def __init__(self, vlab_name):
        self.name = vlab_name
        self.vhosts = {}

    def addVhost(self, vhost_ins):
        if vhost_ins.name in self.vhosts:
            return

        self.vhosts[vhost_ins.name] = vhost_ins


class Lab(object):
    def __init__(self, variable, lab):
        self.name = lab
        self.kv = {}
        self.hosts = {}
        self.roles = {}
        self.lab_ins = None
        self.role_ins = None
        self.variable = variable

    def setParent(self, lab_ins=None, role_ins=None):
        self.lab_ins = lab_ins
        self.role_ins = role_ins

    def getParentRole(self):
        return self.role_ins

    def getParentLab(self):
        return self.lab_ins

    def setKv(self, k, v):
        if k in self.kv:
            logger.error("Duplicate key %s" %k)
            raise Exception("Duplicate key %s" %k)
        self.kv[k] = v

    def getV(self, k):
        try:
            return self.kv[k]
        except:
            return None

    def getVV(self, k):
        return self.getV(k)

    def setHosts(self, k, v):
        if k in self.hosts:
            logger.error("Duplicate key %s" %k)
            raise Exception("Duplicate key %s" %k)
        self.hosts[k] = v

    def setRoles(self, k, v):
        if k in self.roles:
            logger.error("Duplicate key %s" %k)
            raise Exception("Duplicate key %s" %k)
        self.roles[k] = v

    def getHosts(self):
        return self.hosts


class LabRole(Lab):
    def __init__(self, variable, lab, role):
        super(LabRole, self).__init__(variable, lab)
        self.name = role

    def getVV(self, k):
        v = self.getV(k)
        if v:
            return v
        return self.lab_ins.getVV(k)

class LabHost(LabRole):
    def __init__(self, variable, lab, role, host):
        super(LabHost, self).__init__(variable, lab, role)
        self.name = host
        self.symbol = ''
        self.ip_kind = {'internal': 'internal', 'floating': 'floating', 'interface': 'interface', 'IP': ['floating', 'interface', 'internal']}

    def setSymbol(self, symbol):
        self.symbol = symbol

    def getVV(self, k):
        v = self.getV(k)
        if v:
            return v
        return self.role_ins.getVV(k)

    def getVVIP(self, ip='IP'):
        if ip not in self.ip_kind:
            raise Exception('IP kind not supported: %s' % ip)
        ip_kind = self.ip_kind[ip]
        #1st find IP defined manually in host
        v = self.getV(ip)
        if v:
            return v
        #2nd find IP in IP_POOL which is created dynamically
        if isinstance(ip_kind, list):
            for kind in ip_kind:
                v = self.variable.get('%s__%s' % (self.symbol, kind), IP_POOL)
                if v:
                    return v
        else:
            v = self.variable.get('%s__%s' % (self.symbol, ip_kind), IP_POOL)
            if v:
                return v
        #3rd find IP from pararent section, i.e. role and lab
        return self.role_ins.getVV(ip)


class LabInfo:
    def __init__(self):
        self.IP = None
        self.user = 'root'
        self.password = None
        self.become_user = None
        self.become_password = None
        self.internal_ip = None
        self.interface_ip = None
        self.floating_ip = None

    def setIP(self, ip):
        self.IP = ip

    def setAccount(self, account, become=False):
        if account is None:
            return

        if ':' not in account:
            account += ':'

        if become:
            self.become_user, password = account.split(':', 1)
        else:
            self.user, password = account.split(':', 1)

        if len(password) is 0:
            return

        if become:
            self.become_password = password
        else:
            self.password = password

class STFVariablePlugin(STFBasePlugin):
    def __init__(self, plugins):
        super(STFVariablePlugin, self).__init__(plugins)
        self.ENV_RE = re.compile(
            r'^__STFENV__:'  # g<op>
            r'(?P<name>[a-zA-Z][0-9a-zA-Z_]*?)'  # name
            r'=' #assign symbol
            r'(?P<value>.*)'  # value
            r'$'  # end
        )
        self.REPORT_RE = re.compile(
            r'^__STF__:'  # g<op>
            r'(?P<case>[a-zA-Z][0-9a-zA-Z_\-@]+?)'  # case id
            r'='
            r'(?P<result>(PASS|Pass|pass|FAIL|Fail|fail))'  # value
            r'$'  # end
        )
        self.parser = None
        self.ini_file = None
        self.lab_infos = {}
        self.case_lifetime_env = {}
        self.global_lifetime_env = {}
        self.pipeline = None
        self.test_sec = 'Test'
        self.vlab = {}

    def init(self, ini_file, pipeline=None, section=None):
        if ini_file is None:
            logger.warning('ini file is not provided.')
            return

        if not os.access(ini_file, os.R_OK):
            logger.error('INI file %s does not exist or cannot be read' % ini_file)
            raise Exception('INI file %s does not exist or cannot be read' % ini_file)

        self.ini_file = os.path.abspath(ini_file)
        self.parser = STFParser(self.ini_file)
        self.initLabinfo()

        if section:
            sections = self.childHeaders(self.test_sec)
            if section not in sections:
                logger.error('section %s does not exist in %s' % (section, self.ini_file))
                raise Exception('section %s does not exist in %s' % (section, self.ini_file))
            self.test_sec = self.test_sec + ':' + section

        if pipeline:
            pipelines = self.childHeaders(self.test_sec)
            if pipeline not in pipelines:
                logger.error('pipeline %s does not exist in %s' % (pipeline, self.ini_file))
                raise Exception('pipeline %s does not exist in %s' % (pipeline, self.ini_file))
            self.pipeline = pipeline

    def refreshCaseEnv(self):
        self.case_lifetime_env.clear()

    def audit(self):
        if not self.parser:
            logger.warning('You did not provide ini file, some functions may missed')
            #errorAndExit('You should specify ini file in command line to use the variable plugin')

    def get(self, option, scope = 'Global'):
        self.audit()
        value = None
        try:
            value = self.parser.get(scope, option)
        except:
            value = None
        return value

    def getBuild(self, options,scope = 'Build'):
        self.audit()
        return self.get(options, scope)
    def getBuildFile(self, scope = 'Build'):
        self.audit()
        fd,path = tempfile.mkstemp()
        self.parser.dumpSectionToFile(scope, path)
        return path

    def getRobotVarFile(self):
        self.audit()
        fd,path = tempfile.mkstemp(suffix=".py")
        self.parser.dumpSectionToFile('Robot:Variable', path)
        return path

    def isIniFileWritable(self):
        return self.parser.isIniFileWritable()

    def subSections(self, section = None):
        return self.parser.subSections(section)

    def updateDynamic(self, section, option, value=None):
        self.parser.updateDynamic(section, option, value)

    def flushDynamic(self):
        self.parser.flushDynamic()

    def directUpdateDynamic(self, section, option, value=None):
        self.parser.directUpdateDynamic(section, option, value)
        
    def getEnv(self, option):
        self.audit()
        return self.get(option, 'Env')

    def getEnvs(self):
        self.audit()
        return self.parser.items('Env')

    def exportEnvs(self):
        for e in self.options('Env'):
            os.environ[e] = self.getEnv(e)

    def unsetEnvs(self):
        for e in self.options('Env'):
            del os.environ[e]

    def getEnvFile(self):
        self.audit()
        fd, path = tempfile.mkstemp()
        self.parser.dumpSectionToFile('Env', path)
        if len(self.case_lifetime_env) < 1:
            return path

        with open(path, 'a+') as fp:
            fp.write("\n")
            for k in self.case_lifetime_env:
                fp.write("%s=%s\n" % (k, self.case_lifetime_env[k]))
        return path

    def setEnv(self, option, value):
        self.audit()
        self.set('Env', option, value)

    def set(self, section, option, value):
        self.audit()
        self.parser.set(section, option, value)

    def parseStdout(self, stdout, report):
        if stdout is None:
            return

        for line in stdout.replace('\r', '').split('\n'):
            if not line.startswith('__STF'):
                continue
            line = line.strip()
            mo = self.ENV_RE.match(line)
            if mo:
                name = mo.group('name')
                if name is None:
                    continue
                value = mo.group('value')
                self.case_lifetime_env[name] = value
                continue

            mo = self.REPORT_RE.match(line)
            if mo:
                case = mo.group('case')
                if case is None:
                    continue

                result = mo.group('result')

                if result is None:
                    continue

                report.setCaseStatus(case, result)

    #will fix this later
    def getAccountInfo(self, user):
        self.audit()
        return self.get(user, 'ACCOUNT').split(':', 1)

    def childHeaders(self, section = None):
        self.audit()
        return self.parser.childHeaders(section)

    def options(self, section):
        self.audit()
        return self.parser.options(section)
    
    def hasOption(self, option, section):
        self.audit()
        return self.parser.options(section)
    
    def hasSection(self, section):
        self.audit()
        return self.parser.hasSection(section)
    
    def getInt(self, option, section):
        self.audit()
        return self.parser.getInt(section, option)
    

    def _setLabInfos(self, name, ins):
        if name in self.lab_infos:
            logger.error('Duplicate Lab names %s' % name)
            raise Exception('Duplicate Lab names %s' % name)
        self.lab_infos[name] = ins

    def _getLabInfos(self,name):
        try:
            return self.lab_infos[name]
        except:
            return None
    # base_name: mylab, name: mylab__0
    def _fullLabName(self, base_name, name, append=None):
        if append:
            name = name + ':' + append
            base_name = base_name + ':' + append

        sec_name = 'Deploy:Lab:' + base_name
        return sec_name, base_name, name

    def initLabinfo(self):
        lab_header = 'Deploy:Lab'
        for lab in self.childHeaders(lab_header):
            lab_sec, lab_base_name, lab_name = self._fullLabName(lab, lab)

            lab_count = self.get('count', lab_sec)
            if lab_count is None:
                lab_count = 1
            try:
                lab_count = int(lab_count)
            except Exception, e:
                logger.error('count value illegal : %s' % str(e))
                raise Exception('count value illegal : %s' % str(e))

            if lab_count < 1:
                continue

            for c in range(1, lab_count + 1):
                lab_name = lab_base_name if lab_count == 1 else '%s__%d' % (lab_base_name, c)
                lab_ins = Lab(self, lab_name)
                try:
                    for k in self.options(lab_sec):
                        v = self.get(k, lab_sec)
                        if v:
                            lab_ins.setKv(k, v)
                except:
                    pass
                logger.debug('Add lab to lab resource: %s' % lab_name)
                self._setLabInfos(lab_name, lab_ins)

                for role in self.childHeaders(lab_sec):
                    role_sec, role_base_name, role_name = self._fullLabName(lab_base_name, lab_name, role)
                    role_ins = LabRole(self, lab_name, role_name)
                    role_ins.setParent(lab_ins)
                    for k in self.options(role_sec):
                        v = self.get(k, role_sec)
                        if v:
                            role_ins.setKv(k, v)
                    logger.debug('Add role to lab resource: %s' % role_name)
                    self._setLabInfos(role_name, role_ins)
                    count = self.get('count',role_sec)
                    if count is None:
                        count = 0
                    try:
                        count = int(count)
                    except:
                        logger.error('count value illegal in %s' % role_sec)
                        raise Exception('count value illegal in %s' % role_sec)
                    if  count >= 1:
                        #hosts, defined by count in role section
                        for c in range(1, count + 1):
                            host_name = "%s:host%d" % (role_name, c)
                            host_symbol = '%s__%s__host%d' %(lab_name, role, c)
                            host_ins = LabHost(self, lab_name, role_name, host_name)
                            host_ins.setParent(lab_ins, role_ins)
                            host_ins.setSymbol(host_symbol)
                            logger.debug('Add host to lab resource: %s' % host_name)
                            self._setLabInfos(host_name, host_ins)
                            role_ins.setHosts(host_name, host_ins)
                            lab_ins.setHosts(host_name, host_ins)
                            host_ins.setHosts(host_name, host_ins)

                    #hosts, defined manually
                    for host in self.childHeaders(role_sec):
                        host_sec, host_base_name, host_name = self._fullLabName(role_base_name, role_name, host)
                        host_symbol = '%s__%s__%s' % (lab_name, role, host)
                        host_ins = LabHost(self, lab_name, role_name, host_name)
                        host_ins.setParent(lab_ins, role_ins)
                        host_ins.setSymbol(host_symbol)

                        for k in self.options(host_sec):
                            v = self.get(k, host_sec)
                            if v:
                                host_ins.setKv(k, v)
                        logger.debug('Add host to lab resource: %s' % host_name)
                        self._setLabInfos(host_name, host_ins)
                        role_ins.setHosts(host_name, host_ins)
                        lab_ins.setHosts(host_name, host_ins)
                        host_ins.setHosts(host_name, host_ins)

    def _getValueAsList(self, option, section='Global'):
        l = self.get(option, section)
        if l is None:
            return None

        try:
            list_v = ast.literal_eval(l)
        except Exception, e:
            return None

        if not isinstance(list_v, list):
            list_v = filter(None, l.split('\n'))

        return list_v

    def getTestValue(self, option):
        #self.pipeline may be None
        if self.pipeline is None:
            l = self.get(option, self.test_sec)
            logger.debug("pipeline is none, %s is %s ", option, l)
            return self.get(option, self.test_sec)

        v = self.get(option, self.test_sec + ':' + self.pipeline)
        if v:
            return v

        return self.get(option, self.test_sec)

    def getTestValueAsList(self, option):
        l = self.getTestValue(option)
        if l is None:
            return None

        try:
            list_v = ast.literal_eval(l)
        except Exception, e:
            list_v = l

        if not isinstance(list_v, list):
            list_v = filter(None, l.split('\n'))

        return list_v

    def getLabInfo(self, node_id, account_id):
        if node_id is None:
            raise Exception('1st parameter missing when calling getLabInfo(node_id, account_id)')
        # first to check whether it is a vlab
        vlab_list = self.getVhostList(node_id, account_id)
        if vlab_list:
            return vlab_list

        #2nd to check whether we should get them from Env
        lab_list = self.getTestValueAsList(node_id)
        if lab_list is None:
            return self.getLabInfoFromEnv(node_id, account_id)

        #3rd to check whether we should get them from Deploy:Vlab
        lab_info_list = []
        try:
            for lab in lab_list:
                lab_ins = self._getLabInfos(lab)
                if lab_ins is None:
                    continue
                for k in lab_ins.getHosts():
                    lab_info = LabInfo()
                    ins = self._getLabInfos(k)
                    if ins is None:
                        continue
                    lab_info.setAccount(ins.getVV(account_id))
                    lab_info.setAccount(ins.getVV(account_id + '_become'), True)
                    lab_info.setIP(ins.getVVIP())
                    lab_info.interface_ip = ins.getVVIP('interface')
                    lab_info.internal_ip = ins.getVVIP('internal')
                    lab_info.floating_ip = ins.getVVIP('floating')
                    lab_info_list.append(lab_info)
        except Exception,e:
            errorAndExit(str(e))
        return lab_info_list

    def getLabInfoFromEnv(self, node_id, account_id):
        if account_id is None:
            account_id = 'user'

        lab_info_list = []
        lab_info = LabInfo()
        lab_info.setAccount(self.getEnv(account_id))
        lab_info.setAccount(self.getEnv(account_id + '_become'), True)
        lab_info.setIP(self.getEnv(node_id))
        lab_info_list.append(lab_info)
        return lab_info_list

    #vlab will use this API
    def getVhostList(self, vlab_name, account_id):
        if vlab_name not in self.vlab:
            return None

        lab_info_list = []
        vlab_ins = self.vlab[vlab_name]
        if vlab_ins is None:
            return None

        for k in vlab_ins.vhosts:
            host_ins = vlab_ins.vhosts[k]
            lab_info = LabInfo()
            lab_info.setAccount(host_ins.login)
            lab_info.setIP(host_ins.IP)
            lab_info_list.append(lab_info)

        return lab_info_list

    def createVlab(self, vlab_name):
        if vlab_name in self.vlab:
            return

        lab_ins = Vlab(vlab_name)
        self.vlab[vlab_name] = lab_ins

    def createAndAddVhost(self, vlab_list, name, login, IP):
        host_ins = Vhost(name)
        host_ins.login = login
        host_ins.IP = IP

        for lab in vlab_list:
            self.vlab[lab].addVhost(host_ins)


    def isVlabValid(self, vlab_name):
        if vlab_name in self.vlab:
            return True

        return False


