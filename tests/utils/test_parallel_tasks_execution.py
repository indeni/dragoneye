import collections
import random
from asyncio import Future
from time import sleep
from typing import Deque, List, Tuple
from unittest import TestCase
from dragoneye.utils.threading_utils import ThreadedFunctionData, execute_parallel_functions_in_threads


class TestParallelTasksExecution(TestCase):

    def test_parallel_execution(self):
        deque_tasks: Deque[List[ThreadedFunctionData]] = collections.deque()
        independed_tasks: List[ThreadedFunctionData] = []
        dependable_tasks: List[ThreadedFunctionData] = []
        tasks_size: int = 100

        for index in range(tasks_size):
            independed_tasks.append(ThreadedFunctionData(self.do_wait_and_get,
                                                         (f'in-dependent task id={index}\n', random.uniform(0.5, 1)),
                                                         'error msg', 'timeout msg'))

        for index in range(tasks_size, tasks_size * 2):
            dependable_tasks.append(ThreadedFunctionData(self.do_wait_and_get,
                                                         (f'dependent task id={index}\n', random.uniform(0.1, 0.5)),
                                                         'error msg', 'timeout msg'))

        deque_tasks.append(independed_tasks)
        deque_tasks.append(dependable_tasks)
        tasks_responses: List[Tuple[Future, str, str]] = execute_parallel_functions_in_threads(deque_tasks, 10, 10)
        for index in range(tasks_size):
            self.assertRegexpMatches(tasks_responses[index][0].result(), r'^in-dependent.*')

        for index in range(tasks_size, tasks_size * 2):
            self.assertRegexpMatches(tasks_responses[index][0].result(), r'^dependent.*')

    @staticmethod
    def do_wait_and_get(message: str, delay: float) -> str:
        sleep(delay)
        return message
