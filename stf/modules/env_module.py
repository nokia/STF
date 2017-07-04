import sys
from stf.modules.base_module import STFBaseModule


class STFEnvModule(STFBaseModule):
    def __init__(self, plugins):
        pass

    def run(self, case):
        print("I AM running env")
        print(vars(case))

    def preCheck(self, case):
        print('I AM doing precheck: %s' % vars(case))
