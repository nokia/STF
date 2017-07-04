import imp
import os
from stf.lib.stf_utils import *
from stf.managers.base_manager import Manager


class ViewManager(Manager):
    def __init__(self, module_manager):
        self.modules = module_manager
        self.plugins = self.modules.getPluginManager()
        super(ViewManager, self).__init__('view', self.plugins)

    def getInstance(self, name):
        if name in self.factory:
            return self.factory[name]

        v = super(ViewManager, self).getInstance(name)
        v.modules = self.modules
        return v


