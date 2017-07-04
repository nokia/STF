import imp
import os
from stf.lib.stf_utils import *
from stf.managers.base_manager import Manager
class ModuleManager(Manager):
    def __init__(self, plugin_manager):
        self.plugins = plugin_manager
        super(ModuleManager, self).__init__('module', self.plugins)

    def getPluginManager(self):
        return self.plugins
