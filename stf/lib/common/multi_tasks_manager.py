"""
:author: SUN, Andy

MultiTasksManager class based on python threading lib is provided for multi-tasks in parallel.
"""

import stf.lib.exceptions_messages as msgs
from stf.lib.logging.logger import Logger
from threading import Thread
from Queue import Queue

LOGGER = Logger.getLogger(__name__)

class MultiTasksManagerError(BaseException):
    """If error, raise it."""
    pass

class MultiTasksManager(object):
    """
    Run multi-tasks in parallel based on Python threading lib.
    The class provides two public methods for external user: register and runMultiTasks. The register method is used for
    registering the tasks that need to run in parallel. The runMultiTasks method will run the registered tasks in
    parallel and be blocked until all tasks are completed and then return the result.

    >>> multiTasks = MultiTasksManager()
    >>> multiTasks.register(function1, arg1, arg2, kwarg1, kwarg2)
    >>> multiTasks.register(function2, arg1, arg2, kwarg1, kwarg2)
    >>> multiTasks.register(function3, arg1, arg2, kwarg1, kwarg2)
    >>> result = multiTasks.runMultiTasksManager()
    """

    # Decide how to check the tasks result
    # All tasks have no return value
    TASK_NO_RETURN = 0
    # All tasks have the return value
    TASK_RETURN_VALUES = 1
    # Keep the task order so can return the results according to the registered order
    TASK_INDEX = "taskIndex"

    def __init__(self):
        """
        Init MultiTasksManager
        """
        self._setup()

    def _runTask(self, *args, **kwargs):
        """
        Run one task in specific thread.

        Run one task and keep the result of this task in Queue. Each item in Queue includes task index, return code and
        the task result.

        The task index is one integer number to indicate the registered task order.

        The return code is bool value to indicate whether the task is successful or not. If no exception is raised for
        the task, the value will be True. Or its value will be False.

        The task result is from the task return result. If exception is raised for the task, the field is the exception
        message

        :param func taskFun: the function need to be added in the task list and will be run by the thread.
        :param taskArgs: the positional arguments of function registed.
        :param taskKwargs: the keyword arguments of function registed.
        :param kwargs: record the task index
        :raises originException: if the registered function executed failed
        :return: return value depend on the registered function return result

        >>> taskThread = Thread(target=self._runTask, args=(taskFun, taskArgs, taskKwargs), kwargs=kwargs)
        """

        taskFun = args[0]
        taskArgs = args[1]
        taskKwargs = args[2]


        if 'logLevel' in taskKwargs.keys():
            logLevel = taskKwargs['logLevel']
        else :
            logLevel = 'error'


        taskIndex = kwargs[self.__class__.TASK_INDEX]
        LOGGER.debug("Run task %s (index=%d): args=%s, kwargs=%s", taskFun.__name__, taskIndex, taskArgs, taskKwargs)
        try:
            result = taskFun(*taskArgs, **taskKwargs)
            LOGGER.debug("result=%s (index=%d)", result, taskIndex)
            self.taskResults.put((taskIndex, True, result))
            LOGGER.debug("Success for task %s: args=%s, kwargs=%s", taskFun.__name__, taskArgs, taskKwargs)
        except BaseException as originException:
            self.taskResults.put((taskIndex, False, str(originException)))
            if logLevel.lower() == 'error':
                LOGGER.exception("Failure for task %s: args=%s, kwargs=%s", taskFun.__name__, taskArgs, taskKwargs)
            else :
                LOGGER.debug("Failure for task %s: args=%s, kwargs=%s", taskFun.__name__, taskArgs, taskKwargs)
            raise originException

    def register(self, taskFun, *taskArgs, **taskKwargs):
        """
        Register the tasks to be run in parallel and return the thread name

        :param func taskFun: the function to be run in multi-tasks in parallel.
        :param taskArgs: the positional arguments of function registed.
        :param taskKwargs: the keyword arguments of function registed.
        :return: the thread name
        :rtype: String

        >>> multiTasks = self.surepayManager.multiTasksManager
        >>> threadName = multiTasks.register(function1, arg1)
        >>> multiTasks.register(function2, arg1, arg2)
        """
        # Record the task index
        kwargs = {self.__class__.TASK_INDEX:self.taskIndex}
        # Add this task to task list
        taskThread = Thread(target=self._runTask, args=(taskFun, taskArgs, taskKwargs), kwargs=kwargs)
        self.tasks.append(taskThread)
        threadName = taskThread.getName()
        debugMsg = "Register task: task - %s, index - %d, thread name - %s, args - %s, kwargs - %s" \
                    % (taskFun.__name__, self.taskIndex, threadName, taskArgs, taskKwargs)
        LOGGER.trace(debugMsg)
        self.taskIndex += 1
        return threadName

    def _setup(self):
        """Clean share information
        """
        # Record the each task result into thread-safety Queue
        self.taskResults = Queue()
        # Keep tasks in list
        self.tasks = list()
        # Keep the registered task order so return the task result according to this order
        self.taskIndex = 1

    def _checkTaskResult(self, taskType):
        """
        Check task result based on task type

        If the taskType is TASK_NO_RETURN, that means all registered tasks have no return value. True or False will be
        return based on whether any exception is raised in any task.

        If the taskType is TASK_RETURN_VALUES, that means those registered tasks have return value. So one result list
        is returned. The result in the list is based on the registered task order. That is the first item is the result
        of the first registered task and the like.

        :param constant taskType: task type(TASK_NO_RETURN or TASK_RETURN_VALUES)

        >>> result = self._checkTaskResult(self.__class__.TASK_NO_RETURN)
        :return: a boolean(True/False) based on above input parameter TASK_NO_RETURN
        >>> result = self._checkTaskResult(self.__class__.TASK_RETURN_VALUES)
        :return: a list of the task executing result
        """
        returnCodes = list()
        results = dict()
        while not self.taskResults.empty():
            index, rc, result = self.taskResults.get()
            returnCodes.append(rc)
            results[index] = (rc, result)
        # Only need to check whether all tasks are successful or not
        if taskType == self.__class__.TASK_NO_RETURN:
            return all(returnCodes)
        else:
            # return the task result according to the registered order
            return [results[key] for key in sorted(results.keys())]

    def runMultiTasks(self, taskType=None):
        """
        Run registed tasks in parallel and return a bool value or list based on task type.

        The argument taskType can be set to TASK_NO_RETURN (by default) or TASK_RETURN_VALUES. The return value of this
        method is based on this type.

        If the registered tasks have no return value, that means the tasks only do something (for example, run health
        check), call this method with default value. This method will return True or False (exception is raised
        in any tasks)

        If the registered tasks have return value that you need to check, call this method with TASK_RETURN_VALUES. Thus
        one result list is returned. Each item in this list is a tuple like (bool, result or exception string) and it
        keeps consistent with the registered task order.

        If the function is executed successfuly, each item of the result list will be like (True, function result)
        If exception is raised in any tasks, the corresponding result will like (False, function exception string).
        
        :param constant taskType: registered task type (TASK_NO_RETURN or TASK_RETURN_VALUES)
        :return: <list here the two possible return value/type, see exmaple below>
                 a boolean based on above usage, no parameter of runMultiTasks()
                 a list with the result of current function, there's a parameter of runMultiTasks()
                 eg:(True, 'function result') or (False, 'function exception')

        >>> multiTasks = MultiTasksManager()
        >>> multiTasks.register(function1, arg1, arg2, kwarg1, kwarg2)
        >>> multiTasks.register(function2, arg1, arg2, kwarg1, kwarg2)
        >>> TureOrFalse = multiTasks.runMultiTasks()

        >>> multiTasks.register(function3, arg1, arg2, kwarg1, kwarg2)
        >>> multiTasks.register(function4, arg1, arg2, kwarg1, kwarg2)
        >>> resultList = multiTasks.runMultiTasks(MultiTasksManager.TASK_RETURN_VALUES)
        """
        if taskType is None:
            taskType = self.__class__.TASK_NO_RETURN
        if taskType not in (self.__class__.TASK_NO_RETURN, self.__class__.TASK_RETURN_VALUES):
            errorMsg = "%s - %s" % (msgs.TASK_TYPE_FAILURE, taskType)
            LOGGER.error(errorMsg)
            raise MultiTasksManagerError, errorMsg
        # Start all registered tasks
        for task in self.tasks:
            task.start()
        # Wait all tasks complete
        for task in self.tasks:
            task.join()
        # Check the task results based on task type
        result = self._checkTaskResult(taskType)
        # Clean the share information before next multiple tasks.
        self._setup()
        return result
