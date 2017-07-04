import imp
import os
import sys
from stf.lib.stf_utils import *
from stf.lib.logging.logger import Logger

logger = Logger.getLogger(__name__)
class Manager(object):
    def __init__(self,name, manager=None):
        self.kind = name
        self.factory_folder = os.path.dirname(os.path.dirname(__file__)) + '/%ss' % self.kind
        self.suffix = "_%s.py" % self.kind
        self.class_prefix = 'STF'
        self.class_suffix = self.kind.title()
        self.factory = {}
        self.plugins = manager
        if self.plugins is None:
            self.plugins = self

    def getInstance(self, name):
        if name in self.factory:
            return self.factory[name]


        logger.debug('try to find %s [%s] from directory [%s]' %(self.kind, name, self.factory_folder) )

        file_name = '%s%s' % (name, self.suffix)
        file_path = os.path.join(self.factory_folder, file_name)
        class_name = self.class_prefix + name.title() + self.class_suffix
        external_module_name = '%s_%s' %(name, self.kind)

        if not os.path.isfile(file_path):
            logger.debug('try to find %s [%s] from %s' %(self.kind, name, [os.path.join(x, '%s/%s' %(external_module_name,file_name)) for x in sys.path]) )
            try:
                file_ins = __import__('%s.%s' % (external_module_name, external_module_name), globals(), locals(),[external_module_name], 0)
            except ImportError:
                try:
                    logger.debug('Not found')
                    logger.debug('try to find %s [%s] from %s' % (self.kind, name, [os.path.join(x, file_name) for x in sys.path]))
                    file_ins = __import__(external_module_name)
                except BaseException,e:
                    errorAndExit('Error when to load %s [%s] from python library directory: %s' % (self.kind, name, str(e)))
            except BaseException,e:
                errorAndExit('Error when to load %s [%s] from python library directory: %s' %(self.kind, name, str(e)))
        else:
            try:
                logger.debug('try to find %s [%s] from %s' %(self.kind, name, file_path))
                file_ins = imp.load_source(class_name, file_path)
            except BaseException, e:
                errorAndExit('Error when to load %s [%s] with file %s : %s' %(self.kind, class_name, file_path, str(e)))

        try:
            class_ins = getattr(file_ins, class_name)(self.plugins)
        except BaseException, e:
            errorAndExit('Error when load class [%s] : %s' %(class_name, str(e)))

        self.factory[name] = class_ins
        return self.factory[name]
