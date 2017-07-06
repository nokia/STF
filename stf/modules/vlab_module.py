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
from openstackclient.common import clientmanager
from neutronclient.v2_0 import client as neutronclient

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

        self.project_name = self.get('OS_PROJECT_NAME')

        self.auth = self.loader.load_from_options(username=self.get('OS_USERNAME'),
                                                  password=self.get('OS_PASSWORD'),
                                                  project_name=self.project_name,
                                                  auth_url=self.get('OS_AUTH_URL'))

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
            self.existed_instances[l.name] = l.id
            existed_server_list.append(l.name)

        existed_server_list.extend([l.rsplit('-', 1)[0] for l in existed_server_list])
        print(existed_server_list)
        #s = self.nova.servers.find(name=server_s)

        if self.to_delete:
            return

        for server_s in self.server_to_create_or_delete:
            if server_s in existed_server_list:
                errorAndExit('Nova instance [%s] already existed in project [%s]' % (server_s, self.project_name))

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
            flavor = self.get('flavor', server_s)
            flavor_ins = self.nova.flavors.find(name=flavor)

            net = self.get('network', server_s)
            net_ins = self.nova.neutron.find_network(net)

            img = self.get('image', server_s)
            img_ins = self.nova.glance.find_image(name_or_id=img)

            count = self.get('count', server_s)
            login = self.get('login', server_s)
            name = server_s.split(':')[1]

            nova_ins = self.nova.servers.create(name=name, min_count=count, key_name=self.keypair_name,
                                                image=img_ins.id, flavor=flavor_ins.id, nics=[{'net-id': net_ins.id}])
            logger.info('1 %s status is %s (%s)', name, nova_ins.status, nova_ins.id)
            print '-----'
            print dir(nova_ins)
            print '-----'

            logger.info('Bring up ' + name)
            time.sleep(3)
            nova_ins = self.nova.servers.find(id=nova_ins.id)
            logger.info('2 %s status is %s (%s)', name, nova_ins.status, nova_ins.id)
            while nova_ins.status == 'BUILD':
                time.sleep(5)
                nova_ins = self.nova.servers.find(id=nova_ins.id)
                logger.info('Bring up %s, status is %s', name, nova_ins.id)

            logger.info(name + ' is ready')
            # self.variable.createAndAddVhost(nova_ins, self.vlab_name_list

    def doDelete(self, test_process):
        for server_s in self.server_to_create_or_delete:
            if server_s in self.existed_instances:
                self.delNovaIns(server_s)
                continue

            server_s += '-'
            for k in self.existed_instances:
                if not k.startswith(server_s):
                    continue

                suffix = k[len(server_s):]

                if suffix.isdigit():
                    self.delNovaIns(k)


    def delNovaIns(self, name):
        logger.info('will delete %s', name)
        nova_ins = self.nova.servers.find(name=name)
        nova_ins.delete()