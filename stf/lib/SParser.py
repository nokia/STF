import re
from stf.lib.logging.logger import Logger
logger = Logger.getLogger(__name__)

GRE = re.compile(
    r'^stf'  # g<num>
    r'(?P<tags>__[a-zA-Z][0-9a-zA-Z\-~_]*?[^_])'  # tag
    r'(?P<cases>__[a-zA-Z][0-9a-zA-Z_\-~_]+[^_])?'  # case ids
    r'$'  # end
)
# (parallel|loop|async|batch)
SRE = re.compile(
    r'^(s|stfs)(?P<num>[0-9]{1,5})'  # s<num>
    r'(?P<mode>~(parallel|loop|async|batch))?'  # <mode>
    r'(?P<mode_parameter>~[0-9]{1,3})?'  # <mode_parameter>
    r'(?P<module>__[a-zA-Z][0-9a-zA-Z\-~@_]+?[^_])'  # module
    r'(?P<tags>__[a-zA-Z][0-9a-zA-Z\-~_]+?[^_])'  # tag
    r'(?P<cases>__[a-zA-Z][0-9a-zA-Z_\-~_]+[^_])?'  # case ids
    r'(?P<suffix>\.[a-zA-Z]+[^_])?'
    r'$'  # end
)

class SParserError(BaseException):
    """If error, raise it."""
    pass

class SParser(object):
    @staticmethod
    def parseS(f):
        mo = SRE.match(f)
        if not mo:
            raise SParserError('This is impossible but case file name is illegal: %s' % f)

        sid = mo.group('num')

        mode = mo.group('mode')
        if mode:
            mode = mode[1:]

        mode_argv = mo.group('mode_parameter')
        if mode_argv:
            mode_argv = mode_argv[1:]

        module = mo.group('module')
        if module:
            module = module[2:]

        tags = mo.group('tags')
        if tags:
            tags = tags[2:].split('~')

        return mode, mode_argv, module, tags, sid

    @staticmethod
    def parseModule(module_argv):
        """
        parser the module string
        module string will be like below:
        script
        script~LAB1
        script~LAB1~LAB2
        script~USER1@LAB1
        
        :param string module_argv: the module parameters
        :return tuple(moduleName, jumpHostinfo, labinfo)
                eg: script  return: "script", None, None
                script~LAB1 return: "script", None, "root"@"LAB1"
                script~LAB1~LAB2  return: "script", "root"@"LAB1", "root"@"LAB2"
                script~USER1@LAB1  return: "script", None, "USER1@LAB1" 
        """

        jumpHostinfo = None
        labinfo = None
        if module_argv is None:
            return jumpHostinfo, labinfo

        argv_list = module_argv.split("~")

        if len(argv_list) == 1:
            labinfo = argv_list[0]
            if "@" not in labinfo:
                labinfo = "user@" + labinfo

            return jumpHostinfo, labinfo

        if len(argv_list) == 2:
            jumpHostinfo = argv_list[0]
            if "@" not in jumpHostinfo:
                jumpHostinfo = "user@" + jumpHostinfo

            labinfo = argv_list[1]
            if "@" not in labinfo:
                labinfo = "user@" + labinfo

        return jumpHostinfo, labinfo
