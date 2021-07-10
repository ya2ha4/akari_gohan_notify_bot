from typing import List
from logging import getLogger

import notify


logger = getLogger(__name__)


class _RegisteredNotifyTaskList():
    def __init__(self):
        self._task_list: List[notify.NotifyTask] = []


    def append_task(self, task: notify.NotifyTask) -> None:
        self._task_list.append(task)


    def remove_task(self, task: notify.NotifyTask) -> None:
        self._task_list.remove(task)


    def find_task(self, message_id: int) -> notify.NotifyTask:
        for task in self._task_list:
            if message_id == task._register_send_message.id:
                return task
        logger.debug(f"not found:{len(self._task_list)=}")
        return None


registered_notify_task_list: _RegisteredNotifyTaskList = _RegisteredNotifyTaskList()
