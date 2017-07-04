import imp
import os
from stf.lib.stf_utils import *
from stf.managers.base_manager import Manager

class PluginManager(Manager):
    def __init__(self):
        super(PluginManager, self).__init__('plugin')

