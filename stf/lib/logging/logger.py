"""
This class is used for logging.

:author: zhao, xia
"""
import datetime
import logging.config
import os
import sys
import time
from logging import FileHandler


TRACE_LEVEL = 5

class Logger(logging.Logger):
    """
    This class is custom logger for python framework.

    This class can be used the same way as the standard library logging.logger:

    >>> import stf.lib.logging.logger
    >>> logger = Logger.getLogger(__name__)
    >>> logger.debug("my debug message")

    of course you can use all debug functions provided by python logging
    standard lib (debug, info, warning, error, etc.).

    All messages are displayed on both standard output and in a common file.
    This common log file is in log directory and its name starts with date.
    Its name contains jenkins job id and build id if the corresponding
    environment variables are available.

    For messages sent from a test case file, a subdirectory is created in
    log directory with the test case name (zz0000_hello_world). A file
    is created which name contains the date, the test case name, and
    jenkins job and build id if available. This log file contains only
    test case messages. It can be used to debug the test case itself.

    As soon as there is an issue in the framework or in a library, the
    common log file must be used to investigate.

    All messages from test cases automatically reach the common file thanks
    to the "propagate" property of python standard logging library.
    """

    logging.addLevelName(TRACE_LEVEL, "TRACE")
    jenkins_job_name = "JOB_NAME"
    jenkins_build_number = "BUILD_NUMBER"
    jenkins_joburl = "JOB_URL"
    jenkinsJob = os.environ.get(jenkins_job_name)
    jenkinsBuild = os.environ.get(jenkins_build_number)
    jenkinsJobURL = os.environ.get(jenkins_joburl)
    date = datetime.datetime.now().strftime("%Y%m%d-" + time.tzname[1] + "-%H%M%S.%f")
    log_dir_name = "log"
    if not os.path.exists(log_dir_name):
        os.makedirs(log_dir_name)
    filename = log_dir_name + os.sep + date
    if jenkinsJob:
        jenkinsJob = jenkinsJob.split('/')[-1]
        filename += "_job_" + jenkinsJob
    if jenkinsBuild:
        filename += "_build_" + jenkinsBuild
    if jenkinsJobURL is None:
        jenkinsJobURL = ""
    filename_full = filename
    filename_full += "_full.log"
    filename += "_debug.log"
    loggerConfig = {
        "version": 1,
        "loggers": {
            "": {
                "handlers": ["console", "defaultFile", "fullFile"],
                "level": "TRACE"
            },
            "paramiko": {
                "level": "CRITICAL"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "stream": sys.stdout,
                "formatter": "colored"
            },
            "defaultFile": {
                "class": "logging.FileHandler",
                "formatter": "defaultFormatter",
                "level": "DEBUG",
                "filename": filename
            },
            "fullFile": {
                "class": "logging.FileHandler",
                "formatter": "defaultFormatter",
                "level": "TRACE",
                "filename": filename_full
            }
        },
        "formatters": {
            "defaultFormatter": {
                "format": "%(asctime)s - %(levelname)-8s - %(threadName)-12s - %(filename)-25.25s - "
                            "%(lineno)-4d - %(message)s"
            },
            "colored": {
                '()': 'colorlog.ColoredFormatter',
                "format" : "%(bold)s%(asctime)s %(reset)s - %(log_color)s%(levelname)-8s %(reset)s - "
                            "%(threadName)12s - %(filename)-25.25s - %(lineno)-4d - %(message)s"
            }
        }
    }
    logging.config.dictConfig(loggerConfig)
    if jenkinsBuild:
        filename = jenkinsBuild + "/artifact/log/"
    logging.getLogger().debug("Global PostBuild Log directory is : \n" + jenkinsJobURL + filename)
    current_tc_log_dir = str()

    @staticmethod
    def getLogger(name):
        """
        This method is logger configuration.
        Goal of this is to customize logger, to have different logging level for console and file and file_full.

        It returns logger with the specified name.

        :param str name: test case/class name
        :return: Logger object
        :rtype: object

        >>> from stf.lib.logging.logger import Logger
        >>> LOGGER = Logger.getLogger(__name__)
        >>> LOGGER.info('info level log message')
        """
        loggerName = name
        loggerName_full = name + "_full"
        if "ci_" in name or "stf" in name:
            logging.getLogger().debug("\n\n++++++++++++++++++++++++++++" + name + "++++++++++++++++++++++++++++++++++++")
            shortName = name.split(".")[-1]
            handler = name + "FileHandler"
            handler_full = name + "FileHandler" + "_full"
            Logger.loggerConfig["loggers"][name] = {
                "handlers": [handler],
                "level": "DEBUG"
            }
            Logger.loggerConfig["loggers"][loggerName_full] = {
                "handlers": [handler_full],
                "level": "TRACE"
            }
            Logger.loggerConfig["handlers"][handler] = Logger.loggerConfig["handlers"]["defaultFile"].copy()
            Logger.loggerConfig["handlers"][handler_full] = Logger.loggerConfig["handlers"]["fullFile"].copy()
            logDir = Logger.log_dir_name + os.sep + shortName
            if not os.path.exists(logDir):
                os.makedirs(logDir)
            filename = logDir + os.sep + Logger.date
            if Logger.jenkinsJob:
                filename += "_job_" + Logger.jenkinsJob
            if Logger.jenkinsBuild:
                filename += "_build_" + Logger.jenkinsBuild
            filename += "_" + shortName + "_TC_skeleton.log"
            Logger.loggerConfig["handlers"][handler]["filename"] = filename
            if Logger.jenkinsBuild:
                filename = Logger.jenkinsBuild + "/artifact/" + filename
            Logger.postBuildTestLogFile = ("Test PostBuild Log file is : \n" + Logger.jenkinsJobURL + "/" + filename)
        else:
            loggerName = None
        logging.config.dictConfig(Logger.loggerConfig)
        return logging.getLogger(loggerName)


    @staticmethod
    def getLogDir(name):
        """
        This method returns string type: log/<name>, or None in case when 'ci_' is not in 'name'.

        :param str name: string
        :return: string log/<name>
        :rtype: str

        >>> from stf.lib.logging.logger import Logger
        >>> LOGDIR = Logger.getLogDir(__name__)
        """
        if "ci_" in name or "stf" in name:
            shortName = name.split(".")[-1]
            return Logger.log_dir_name + os.sep + shortName
        else:
            return None


    def trace(self, message, *args, **kws):
        """
        This method adds a new logger level below DEBUG.

        No return value for the method.

        :param str message: the message
        :param *args: the positional arguments
        :param **kws: the keyword arguments

        >>> from stf.lib.logging.logger import Logger
        >>> LOGGER = Logger.getLogger(__name__)
        >>> LOGGER.trace("Low level message")
        """
        if self.isEnabledFor(TRACE_LEVEL):
            self._log(TRACE_LEVEL, message, args, **kws)
    logging.Logger.trace = trace

    @staticmethod
    def switchToTcLog(LOGGER, tcName, loop=None):
        """
        This method:
        - removes the main handler from the logger
        - creates and adds the TC handler to the logger

        It returns the main handler, the TC handler and the link to the TC log file.

        :param Logger LOGGER: Logger object
        :param str tcName: test case name
        :param int loop: number of loops, the default value is None
        :return: tuple (main handler, TC handler, link to the TC log file)
        :rtype: tuple

        >>> from stf.lib.logging.logger import Logger
        >>> LOGGER = Logger.getLogger(__name__)
        >>> mainHandler, mainHandlerFull, message = Logger.switchToTcLog(LOGGER, testItem)
        """
        # copy "DefaultFile handler"
        oldHandler = LOGGER.handlers[1]
        oldHandlerFull = LOGGER.handlers[2]
        # create filename
        jenkins_job_name = "JOB_NAME"
        jenkins_build_number = "BUILD_NUMBER"
        jenkins_joburl = "JOB_URL"
        jenkinsJob = os.environ.get(jenkins_job_name)
        jenkinsBuild = os.environ.get(jenkins_build_number)
        jenkinsJobURL = os.environ.get(jenkins_joburl)
        date = Logger.date
        log_dir_name = "log/" + tcName
        TcFilename = log_dir_name + os.sep + date
        if jenkinsJob:
            jenkinsJob = jenkinsJob.split('/')[-1]
            TcFilename += "_job_" + jenkinsJob
        if jenkinsBuild:
            TcFilename += "_build_" + jenkinsBuild
        if jenkinsJobURL is None:
            jenkinsJobURL = ""
        if loop == None:
            TcFilename_full = TcFilename + "_" + tcName + '_full.log'
            TcFilename = TcFilename + "_" + tcName + "_debug.log"
        else:
            TcFilename = TcFilename + "_" + tcName + "_" + str(loop)
            TcFilename_full = TcFilename + '_full.log'
            TcFilename += "_debug.log"
        # copy the oldHandler formatter
        formatter = oldHandler.__getattribute__("formatter")
        # create the new handler to replace "DefaultFile" handler
        newHandler = FileHandler(TcFilename)
        newHandlerFull = FileHandler(TcFilename_full)
        newHandler.setLevel('DEBUG')
        newHandlerFull.setLevel(TRACE_LEVEL)
        newHandler.setFormatter(formatter)
        newHandlerFull.setFormatter(formatter)
        # change main handler
        LOGGER.removeHandler(oldHandler)
        LOGGER.removeHandler(oldHandlerFull)
        LOGGER.addHandler(newHandler)
        LOGGER.addHandler(newHandlerFull)

        # create url to WS directory
        filename = log_dir_name + "/"
        if jenkinsBuild:
            filename = jenkinsBuild + "/artifact/" + filename
        message = jenkinsJobURL + "/" + filename
        Logger.current_tc_log_dir = log_dir_name
        return oldHandler, oldHandlerFull, message

    @staticmethod
    def switchToMainLog(LOGGER, mainLog, mainLogFull):
        """
        This method removes the tcLog handler from the logger and adds the mainLog handler to the logger.

        No return value for the method.

        :param Logger LOGGER: Logger object
        :param Logger mainLog: main handler object
        :param Logger mainLogFull: TC handler object

        >>> from stf.lib.logging.logger import Logger
        >>> LOGGER = Logger.getLogger(__name__)
        >>> mainLog, mainLogFull, _ = Logger.switchToTcLog(LOGGER, testItem)
        >>> Logger.switchToMainLog(LOGGER, mainLog, mainLogFull)
        """
        # remove TC handler + TC Handler Full
        LOGGER.removeHandler(LOGGER.handlers[2])
        LOGGER.removeHandler(LOGGER.handlers[1])
        # add old handler
        LOGGER.addHandler(mainLog)
        LOGGER.addHandler(mainLogFull)
