import sys
import os
import shutil
import time
import subprocess
from stf.modules.base_module import STFBaseModule
from stf.lib.logging.logger import Logger
from stf.lib.SParser import SParser
from stf.managers.test_case_manager import TestStep, TestProcess
from stf.lib.STFParser import STFParser
from stf.lib.stf_utils import *

from novaclient import client as nova_client
from keystoneauth1 import loading
from keystoneauth1 import session
#from neutronclient.v2_0 import client as neutronclient

logger = Logger.getLogger(__name__)


class STFVlabModule(STFBaseModule):
    def __init__(self, pluginManager):
        super(STFVlabModule, self).__init__(pluginManager)
        self.lab = None
        self.parser = None
        self.test_step = None
        self.server_sections = None
        self.server_to_create_or_delete = None
        self.project_name = None
        self.id_rsa_pub = None
        self.keypair_name = 'stf_'
        self.vlab_name_list = []
        self.options = ['count', 'flavor', 'image', 'security-group', 'network', 'login']
        self.to_delete = False
        self.existed_instances = {}

    def checkMode(self, mode):
        pass
    
    def checkModeParameter(self, parameter):
        pass

    def checkModule(self, module):
        if module == 'vlab':
            return

        raise Exception("module name should be [vlab] while it is [%s]" % module )
                 
    def checkModuleArgv(self, module_argv):
        if module_argv is None:
            raise Exception('file name illegal: vlab parameter missed')

        self.vlab_name_list = module_argv.split('~')
        for l in self.vlab_name_list:
            if '@' in l:
                self.to_delete = True
                return

            self.variable.createVlab(l)

    def checkTags(self, tags):
        pass
    
    def checkTmsIDs(self, cases):
        pass

    def parseCaseFile(self, test_step):
        self.test_step = test_step
        self.parser = STFParser(test_step.path)
        # self.setEnvLocal()

        # check server create strategy

        self.server_sections = self.parser.subSections('Vlab')
        if len(self.server_sections) == 0:
            errorAndExit('You should define [Vlab:***] in %s, *** means the instance name' % (self.test_step.path))

        self.server_to_create_or_delete = self.parser.childHeaders('Vlab')
        if len(self.server_to_create_or_delete) == 0:
            errorAndExit('Impossible but you should define [Vlab:***] in %s, *** means the instance name' % (
            self.test_step.path))

        self.keypair_name += '_'.join(self.server_to_create_or_delete)

        self.loader = loading.get_plugin_loader('password')

        # openstack OS_* variable will read from Jenkins credential plugin or Jenkinsfile environment section
        self.project_name = os.path.expandvars(self.get('OS_PROJECT_NAME'))

        self.auth = self.loader.load_from_options(username=os.path.expandvars(self.get('OS_USERNAME')),
                                                  password=os.path.expandvars(self.get('OS_PASSWORD')),
                                                  project_name=self.project_name,
                                                  auth_url=os.path.expandvars(self.get('OS_AUTH_URL')))

        self.session = session.Session(auth=self.auth)
        self.nova = nova_client.Client(2, session=self.session)

        # check options have been configured
        for server_s in self.server_sections:
            for option in self.options:
                self.get(option, server_s)

        #if no ssh key then generate it
        ssh_path = os.path.expanduser('~/.ssh')
        self.id_rsa_pub = ssh_path + '/id_rsa.pub'
        command = "ssh-keygen -f %s/id_rsa -t rsa -N '' " % (ssh_path)
        if not os.path.exists(ssh_path + '/id_rsa') or not os.path.exists(self.id_rsa_pub):
            try:
                out = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout.read()
            except Exception, e:
                errorAndExit('%s: %s' % (str(e), out))

        if not os.path.exists(ssh_path + '/id_rsa') or not os.path.exists(self.id_rsa_pub):
            errorAndExit('generate ssh key failed.')


    
    def checkOthers(self, test_step):
        self.parseCaseFile(test_step)
        #check whether server alreay existed
        existed_server_list = []
        for l in self.nova.servers.list():
            self.existed_instances[l.id] = l.name
            existed_server_list.append(l.name)

        existed_server_list.extend([l.rsplit('-', 1)[0] for l in existed_server_list])
        #s = self.nova.servers.find(name=server_s)

        if self.to_delete:
            return

        for server_s in self.server_to_create_or_delete:
            if server_s in existed_server_list:
                logger.warning('Nova instance [%s] already existed in project [%s]' % (server_s, self.project_name))
                #errorAndExit('Nova instance [%s] already existed in project [%s]' % (server_s, self.project_name))

        # check whether flavor existed
        for server_s in self.server_sections:
            flavor = self.get('flavor', server_s)
            flavor_ins = self.nova.flavors.find(name=flavor)

        # check whether network existed
        for server_s in self.server_sections:
            net = self.get('network', server_s)
            net_ins = self.nova.neutron.find_network(net)

        # check whether image existed
        for server_s in self.server_sections:
            img = self.get('image', server_s)
            img_ins = self.nova.glance.find_image(name_or_id=img)

        # check count is in the range , 1 ~ 5
        for server_s in self.server_sections:
            count = int(self.get('count', server_s))
            if count < 1 or count > 5:
                errorAndExit('[count] in [%s] is out of range (1 - 5): %d' % (server_s, count))


    def get(self, option, section='Vlab'):
        if self.parser is None:
            raise Exception('self.parser not initialized')

        option_value = self.parser.get(section, option)
        if option_value is None:
            errorAndExit('You Need to configure [%s] in %s' % (option, self.test_step.path))

        if len(option_value) == 0:
            errorAndExit('[%s] value is incorrect in %s' % (option, self.test_step.path))

        return option_value

    def runStep(self, test_step):
        tp = TestProcess()
        test_step.addProcess(tp)

        tp.status = 'running'
        tp.starttime = time.time()

        if self.to_delete:
            self.doDelete(tp)
        else:
            self.doCreate(tp)

        tp.endtime = time.time()

    def doCreate(self, test_process):
        # register the key pair to openstack
        f = open(self.id_rsa_pub, 'r')
        public_key = f.readline()[:-1]

        try:
            self.nova.keypairs.create(self.keypair_name, public_key)
        except:
            self.nova.keypairs.delete(self.keypair_name)
            self.nova.keypairs.create(self.keypair_name, public_key)
        f.close()

        for server_s in self.server_sections:
            count = int(self.get('count', server_s))
            if count < 1 or count > 5:
                raise Exception('[count] in [%s] is out of range (1 - 5): %d' % (server_s, count))
            #help me: we can use nova create several instance simutaniously, but don't know how to query the status of each
            #so here I create it serially
            for index in range(0, count):
                flavor = self.get('flavor', server_s)
                flavor_ins = self.nova.flavors.find(name=flavor)

                net = self.get('network', server_s)
                net_ins = self.nova.neutron.find_network(net)

                img = self.get('image', server_s)
                img_ins = self.nova.glance.find_image(name_or_id=img)


                login = self.get('login', server_s)
                name = server_s.split(':')[1]
                # help me: we can use nova create several instance simutaniously, but don't know how to query the status of each
                # so here I create it serially
                nova_ins = self.nova.servers.create(name=name, min_count=1, key_name=self.keypair_name,
                                                    image=img_ins.id, flavor=flavor_ins.id, nics=[{'net-id': net_ins.id}])

                logger.info('%s status is %s (%s), address: %s', name, nova_ins.status, nova_ins.id, nova_ins.addresses)

                while nova_ins.status == 'BUILD':
                    time.sleep(5)
                    nova_ins = self.nova.servers.get(nova_ins.id)
                    logger.info('Bring up %s (%s), status is %s, address: %s', name, nova_ins.id, nova_ins.status, nova_ins.addresses)

                if nova_ins.status != 'ACTIVE':
                    logger.error('Bring up %s (%s) failed, status is %s, address: %s', name, nova_ins.id, nova_ins.status,
                                nova_ins.addresses)
                    raise Exception('Create nova instance failed.')

                logger.info(name + ' is ready')

                #extract the instance ip
                ip = self.getNovaIp(nova_ins.addresses)

                if ip is None:
                    raise Exception('Cannot get ip address of created nova instance')

                self.variable.createAndAddVhost(self.vlab_name_list, nova_ins.id, login, ip)

    def getNovaIp(self, address):
        ip = None
        for k in address:
            # get list
            tmp_ip_list = address[k]
            # list element is a dict
            for tmp_ip_dict in tmp_ip_list:
                ip = tmp_ip_dict['addr']
                if ip:
                    return ip

    def doDelete(self, test_process):
        for server_to_del in self.server_to_create_or_delete:
            server_to_del_with_suffix = server_to_del + '-'
            for server_id in self.existed_instances:
                server_name = self.existed_instances[server_id]
                if server_name == server_to_del:
                    self.delNovaIns(server_name, server_id)
                    continue

                if not server_name.startswith(server_to_del_with_suffix):
                    continue

                suffix = server_name[len(server_to_del_with_suffix):]
                #e.g. gemfieldServer-1
                if suffix.isdigit():
                    self.delNovaIns(server_name, server_id)


    def delNovaIns(self, name, id):
        logger.info('will delete %s (%s)', name, id)
        try:
            nova_ins = self.nova.servers.find(id=id)
        except Exception, e:
            logger.warning('Cannot find the instance %s(%s): %s', name, id, str(e))
            return
        try:
            nova_ins.delete()
        except Exception, e:
            logger.warning('Cannot delete the instance %s(%s): %s', name, id, str(e))