import asyncio

from monitor.serializers import MonitorSettings, DbConnectionSettings
from monitor.utils import logger
from monitor.worker import WebsiteWorker, DbWorker


class Monitor:
    def __init__(self, settings: MonitorSettings, db_connection_settings: DbConnectionSettings):
        self._settings = settings
        self._db_connection_settings = db_connection_settings
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=len(settings.websites) * 2)

        self._website_workers = self._setup_website_workers()
        self._db_workers = self._setup_db_workers()
        self._tasks: list[asyncio.Task] = []

    def _setup_db_workers(self) -> list[DbWorker]:
        worker = DbWorker(
            connection_settings=self._db_connection_settings,
            worker_settings=self._settings.db,
            queue=self._queue
        )
        return [worker]

    def _setup_website_workers(self) -> list[WebsiteWorker]:
        workers = []
        for i, setting in enumerate(self._settings.websites):
            worker = WebsiteWorker(settings=setting, queue=self._queue, name=f'WebsiteWorker-{i}')
            workers.append(worker)
        return workers

    def run(self):
        asyncio.run(self._run())

    async def _run(self):
        logger.info('Running monitor')
        for worker in [*self._db_workers, *self._website_workers]:
            task = asyncio.create_task(worker.run())
            self._tasks.append(task)
        await asyncio.gather(*self._tasks)
        logger.info('Monitor completed')

    def stop(self):
        logger.info('Stopping monitor')
        for task in self._tasks:
            task.cancel()
