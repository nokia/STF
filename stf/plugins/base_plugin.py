from abc import ABCMeta, abstractmethod

class STFBasePlugin(object):
    def __init__(self, plugins):
        self.plugins = plugins

    #@abstractmethod
    #def checkOthers(self): pass

    #@abstractmethod
    #def preCheck(self, f):
    #    mode, parameter, module, tags, cases = SParser.parseS(os.path.basename(f))
    #    self.checkMode(mode)