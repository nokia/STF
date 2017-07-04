'''
Created on Apr 12, 2017

@author: Liu Dongxiao
'''

from collections import namedtuple
from lib.logging.logger import Logger
from modules.base_module import STFBaseModule
import os
import re

from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.inventory import Inventory
from ansible.parsing.dataloader import DataLoader
from ansible.plugins.callback import CallbackBase
from ansible.vars import VariableManager


logger = Logger.getLogger(__name__)
ACCEPT_MODE = ["loop"]
RC_ERROR = 1
class STFPlaybookModuleError(BaseException):
    """If error, raise it."""
    pass
 
    '''
    ResultsCollector used for collecting the results of executing the playbook, will use later
    '''
class ResultsCollector(CallbackBase):

    def __init__(self, *args, **kwargs):
        super(ResultsCollector, self).__init__(*args, **kwargs)
        self.host_ok     = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def v2_runner_on_unreachable(self, result):
        self.host_unreachable[result._host.get_name()] = result

    def v2_runner_on_ok(self, result,  *args, **kwargs):
        self.host_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result,  *args, **kwargs):
        self.host_failed[result._host.get_name()] = result
      
class STFPlaybookModule(STFBaseModule):
    """
    the playbook module of the 
    """
    def __init__(self, pluginManager):
        """
        constructor
        """
        super(STFPlaybookModule, self).__init__(pluginManager)

    def checkMode(self, mode):
        """
         check mode, now only support the mode in ACCEPT_MODE
        :param mode: the mode of the execution eg:loop(900-1)/async(s-0)
        
        """
        if mode not in ACCEPT_MODE:
            logger.error("playbook module do not support %s mode, now only support %s", mode, ACCEPT_MODE)
            raise STFPlaybookModuleError("playbook module do not support %s mode, now only support %s", mode, ACCEPT_MODE)
    
    def checkModeParameter(self, parameter):
        """
        :param parameter: the parameter of the specific mode
        """
        if not self.isNumeric(parameter):
            logger.error("playbook mode parameter %s is invalid" , parameter)
            raise STFPlaybookModuleError("playbook mode parameter %s is invalid" , parameter)
    
    def checkModuleParameter(self, module, jumphost_info, lab_info):
        """
        :param module parameter
         TODO: DRY-RUN
        """
        logger.info("module name is %s, justhost is %s,  access node is %s", module, jumphost_info, lab_info)
        if module.lower() != "playbook":
            logger.error("this is playbook module, not %s", module)
            raise STFPlaybookModuleError("this is playbook module, not %s", module)
        
   
    def checkTags(self, tags):
        pass
    
    def checkCaseIDs(self, cases):
        pass
    
    def checkOthers(self, f):
        pass

    def genInventoryFromIniFile(self):
        """
        need to do later 
        currently hard code local file which is a invertory file including a host
        file content 
        [webservers]
        135.252.172.11
        """
        filePath = "/home/dongxiao_test/hosts2"
        return filePath
    
    def run(self, caseInfo):
        """
        :param caseInfo 
        :return tuple(returnCode, output)
        """
        playbookPath = caseInfo.current_step.path
        caseFileName = os.path.basename(playbookPath)
        mode = caseInfo.current_step.mode
        parameter = caseInfo.current_step.mode_argv 
        module = caseInfo.current_step.module
        jumphost_info = caseInfo.current_step.jumphost_info
        lab_info = caseInfo.current_step.lab_info
        tags = caseInfo.current_step.step_tags
        
        variable_manager = VariableManager()
        loader = DataLoader()
        inventoryFile = self.genInventoryFromIniFile()
        inventory = Inventory(loader=loader, variable_manager=variable_manager,  host_list=inventoryFile)

        if not os.path.exists(playbookPath):
            logger.error("File %s does not exist ", playbookPath)
            raise STFPlaybookModuleError("File %s does not exist ", playbookPath)

        Options = namedtuple('Options', ['listtags', 'listtasks', 'listhosts', 'syntax', 'connection','module_path', 'forks', 'remote_user', 'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args', 'scp_extra_args', 'become', 'become_method', 'become_user', 'verbosity', 'check'])
        options = Options(listtags=False, listtasks=False, listhosts=False, syntax=False, connection='ssh', module_path=None, forks=100, remote_user='root', private_key_file=None, ssh_common_args=None, ssh_extra_args=None, sftp_extra_args=None, scp_extra_args=None, become=True, become_method=None, become_user='root', verbosity=None, check=False)

#       variable_manager.extra_vars = {'hosts': 'mywebserver'} # This can accomodate various other command line arguments.`

        passwords = {}
        
        try:
            pbex = PlaybookExecutor(playbooks=[playbookPath], inventory=inventory, variable_manager=variable_manager, loader=loader, options=options, passwords=passwords)
  
            results = pbex.run()
        except Exception,e:
                logger.error("Playbook run error %s" ,e)
                results = 1
        return results
#         play = Play().load(playbookPath, variable_manager=variable_manager, loader=loader)
#          #actually run it
#         tqm = None
#         callback = ResultsCollector()
#         try:
#             tqm = TaskQueueManager(
#                                    inventory=inventory,
#                                    variable_manager=variable_manager,
#                                    loader=loader,
#                                    options=options,
#                                    passwords=passwords,
#                                    )
#             tqm._stdout_callback = callback
#             result = tqm.run(play)
#         finally:
#                 if tqm is not None:
#                      tqm.cleanup()
#                              
#         print("OK ***********")
#         for host, result in callback.host_ok.items():
#             print('{} >>> {}'.format(host, result._result['stdout']))
#  
#         print("FAILED *******")
#         for host, result in callback.host_failed.items():
#             print('{} >>> {}'.format(host, result._result['msg']))
#  
#         print("DOWN *********")
#         for host, result in callback.host_unreachable.items():
#             print('{} >>> {}'.format(host, result._result['msg']))
        

        
        def isNumeric(self,str):
                pat = re.compile('\\d+')
                result = pat.findall(str)
                if not result or pat.findall(str)[0] != str  or int(str) <= int(0):
                        logger.error('%s is not a valid num' %(str))
                        return False
                else:
                        return True

    
    
