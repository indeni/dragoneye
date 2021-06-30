import concurrent
from concurrent.futures import Future, ThreadPoolExecutor, ALL_COMPLETED
from dataclasses import dataclass
from typing import Callable, List, Tuple, Deque

from dragoneye.utils.app_logger import logger


@dataclass
class ThreadedFunctionData:
    callable: Callable
    args: Tuple
    error_msg: str
    timeout_msg: str = None


def execute_parallel_functions_in_threads(tasks_groups: Deque[List[ThreadedFunctionData]], max_workers, timeout=None)\
        -> List[Tuple[Future, str, str]]:
    """
    This function takes a Queue (tasks_groups: Deque[List[ThreadedFunctionData]])
    of lists, when each queued item represents a list of functions that should be run in parallel.
    """
    tasks_responses: List[Tuple[Future, str, str]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:

        for tasks_group in tasks_groups:
            for task in tasks_group:
                tasks_responses.append((
                    executor.submit(task.callable, *task.args),
                    task.error_msg, task.timeout_msg))

            concurrent.futures.wait([response[0] for response in tasks_responses], timeout=timeout, return_when=ALL_COMPLETED)

        timeout_tasks = [response for response in tasks_responses if response[0].running()]
        for timeout_task in timeout_tasks:
            logger.exception(timeout_task[2])
        failed_tasks = [response for response in tasks_responses if response[0].exception()]
        for failed_task in failed_tasks:
            logger.exception(failed_task[1], exc_info=failed_task[0].exception())

    return tasks_responses
