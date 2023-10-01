import asyncio
import asyncio.exceptions
import time

from monitor.utils import logger


class Worker:
    def __init__(self, period: float, name: str = 'BaseWorker'):
        self._period = period
        self._name = name

    async def run(self):
        logger.info('Running worker %s', self._name)
        try:
            while True:
                start = time.time()
                await self.task()
                task_duration = time.time() - start
                time_to_wait = self._period - task_duration
                if time_to_wait >= 0:
                    await asyncio.sleep(time_to_wait)
        except asyncio.exceptions.CancelledError:
            logger.info('Worker %s is stopped', self._name)

    async def task(self):
        raise NotImplementedError  # pragma: nocover
