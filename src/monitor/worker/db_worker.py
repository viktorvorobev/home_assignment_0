import asyncio
import enum

import aiopg

from monitor.serializers import DbConnectionSettings, MonitoringResult, DbWorkerSettings
from monitor.utils import logger
from .worker import Worker

TABLE_NAME = 'monitoring'


class Columns(enum.StrEnum):
    URL = enum.auto()
    TIME_STAMP = enum.auto()
    STATUS_CODE = enum.auto()
    RESPONSE_TIME = enum.auto()
    REGEXP_MATCH = enum.auto()


class DbWorker(Worker):
    def __init__(
            self,
            connection_settings: DbConnectionSettings,
            worker_settings: DbWorkerSettings,
            queue: asyncio.Queue,
            name: str = 'DBWorker'
    ):
        super().__init__(period=worker_settings.period, name=name)
        self._queue = queue
        self._dsn = connection_settings.dsn
        self._max_batch_size = worker_settings.max_batch_size

    async def run(self):
        logger.info('Running db worker')
        await self._setup_db()
        await super().run()

    async def _setup_db(self):
        async with aiopg.connect(dsn=self._dsn) as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                f'''
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    {Columns.URL} VARCHAR(256),
                    {Columns.TIME_STAMP} timestamp,
                    {Columns.STATUS_CODE} INT,
                    {Columns.RESPONSE_TIME} FLOAT,
                    {Columns.REGEXP_MATCH} BOOLEAN
                )
                '''
            )

    async def task(self):
        entries = []
        logger.debug('Extracting entries from queue. Entries %s', self._queue.qsize())
        for _ in range(self._max_batch_size):
            if self._queue.empty():
                break
            entry: MonitoringResult = await self._queue.get()
            entries.append(entry)
        logger.debug('Extracted %s entries from queue', len(entries))

        if not entries:
            return
        rows = []
        for entry in entries:
            # Can't do much about postgres syntax, so convert None/True/False to NULL/TRUE/FALSE
            regexp_match = 'NULL' if entry.regexp_match is None else str(entry.regexp_match).upper()
            # pylint: disable = invalid-string-quote
            rows.append(
                f"('{entry.url}', '{entry.timestamp}',{entry.status_code},{entry.response_time},{regexp_match})"
            )

        rows_to_insert = ','.join(rows)
        command = f'''
        INSERT INTO
            {TABLE_NAME} ({",".join(Columns)})
        VALUES
        '''
        command += rows_to_insert
        async with aiopg.connect(dsn=self._dsn) as conn:
            cursor = await conn.cursor()
            await cursor.execute(command)
