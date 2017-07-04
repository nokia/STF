#!/usr/bin/env python
import os
import sys
import re
from pwd import getpwuid
from stf.lib.stf_utils import *
from stf.plugins.base_plugin import STFBasePlugin

from lib.logging.logger import Logger

logger = Logger.getLogger(__name__)

hc_omitdirs = ['/u/ainet/','/u/root/']
hc_target = ['/u/suteam/']
stf_base = "/n/csf/auto/CSFcommon"
stf_include_dirs = []

mcas_home_pattern = re.compile('.*(/u/[a-z0-9]+/).*')
csf_home_pattern = re.compile('.*(/n/csf).*')
csf_include_pattern = re.compile('.*(/include/[a-zA-Z0-9]+/).*')


class STFAuditPlugin(STFBasePlugin):
    def __init__(self, plugins):
        super(STFAuditPlugin, self).__init__(plugins)

    def preCheck(self, dir):
        logger.debug("Start STF coding standard audit in %s ...", dir)
        self.auditDirs(dir)
        for d in stf_include_dirs:
            logger.debug("Start STF coding standard audit in %s ...", d)
            self.auditDirs(d)

    def auditFile(self, path):
        try:
            f = open(path)
        except:
            return False
        lineno = 0
        for line in f:
            lineno += 1
            try:
                line.decode('ascii')
            except UnicodeDecodeError:
                logger.error('STF think %s is not an ASCII file when parsing to line %d, why not put them in CSFcommon/lib or Nexus server?', path, lineno)
                raise Exception('STF think %s is not an ASCII file' % path)
            except:
                logger.error('STF think %s is not an regular STF case file when parsing to line %d, why not put them in CSFcommon/lib or Nexus server?', path, lineno)
                raise Exception('STF think %s is not an regular STF case file ' % path)

            line = line.lstrip()
            if line.startswith('#'):
                continue

            # check mcas_home_pattern
            rc = mcas_home_pattern.match(line)
            if rc:
                homedir = rc.group(1)
                if homedir in hc_omitdirs:
                    pass
                elif homedir in hc_target:
                    logger.error('hard coded build server absolute path in line %d of %s ' % (lineno, path))
                    raise Exception('hard coded build server absolute path in line %d of %s ' % (lineno, path))
                elif os.path.isdir(homedir):
                    logger.error('hard coded build server absolute path in line %d of %s ' % (lineno, path))
                    raise Exception('hard coded build server absolute path in line %d of %s ' % (lineno, path))
                else:
                    hc_omitdirs.append(homedir)

            # check csf_home_pattern
            rc = csf_home_pattern.match(line)
            if rc:
                logger.error('hard coded build server absolute path in line %d of %s ' % (lineno, path))
                raise Exception('hard coded build server absolute path in line %d of %s ' % (lineno, path))

            # check include pattern
            rc = csf_include_pattern.match(line)
            if rc:
                indir = stf_base + rc.group(1)
                if os.path.isdir(indir):
                    if indir not in stf_include_dirs:
                        logger.debug("Add %s to the STF coding standard audit dirs" % (indir))
                        stf_include_dirs.append(indir)

        return True

    def auditDirs(self, base):
        for root, dirs, files in os.walk(base, followlinks=True):
            for file in files:
                if root.find('gcov_common') != -1:
                    continue
                if root.endswith('_'):
                    continue
                if file.startswith('.'):
                    continue
                if file.endswith('.log'):
                    continue
                if file.endswith('_'):
                    continue
                if file.endswith('.html'):
                    continue
                if file.endswith('.result'):
                    continue
                if file.endswith('.pyc'):
                    continue

                path = os.path.join(root, file)

                try:
                    f_size = os.path.getsize(path)
                except:
                    logger.error("%s has wrong priviledge as STF cases" % (path))
                    raise Exception("%s has wrong priviledge as STF cases" % (path))

                if f_size > 200000:
                    logger.error("%s is not a regular test case file [1,log file use *.log suffix; 2, binary file should built from source or put in Nexus server]" % (path))
                    raise Exception("%s is not a regular test case file [1,log file use *.log suffix; 2, binary file should built from source or put in Nexus server]" % (path))

                # note("STF coding standard for file %s" %(path))
                self.auditFile(path)


