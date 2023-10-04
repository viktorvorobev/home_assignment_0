import asyncio
import datetime

import aiopg
import pytest
from pytest_postgresql.janitor import DatabaseJanitor

from monitor.serializers import DbConnectionSettings, DbWorkerSettings, MonitoringResult
from monitor.worker.db_worker import DbWorker, TABLE_NAME


@pytest.fixture(name='db_connection_settings', scope='session')
def db_connection_settings_fixture(postgresql_proc):
    with DatabaseJanitor(
            user=postgresql_proc.user,
            host=postgresql_proc.host,
            port=postgresql_proc.port,
            dbname=postgresql_proc.dbname,
            version=postgresql_proc.version,
            password=postgresql_proc.password,
    ):
        yield DbConnectionSettings(
            host=postgresql_proc.host,
            port=str(postgresql_proc.port),
            username=postgresql_proc.user,
            password=postgresql_proc.password,
            db=postgresql_proc.dbname,
            ssl=False,
        )


@pytest.mark.asyncio
async def test_worker_creates_table(db_connection_settings):
    worker_settings = DbWorkerSettings(period=0.1, max_batch_size=1)
    queue = asyncio.Queue()
    worker = DbWorker(connection_settings=db_connection_settings, worker_settings=worker_settings, queue=queue)

    loop = asyncio.get_event_loop()
    worker_task = loop.create_task(worker.run())

    async def stop_test():
        await asyncio.sleep(worker_settings.period + 0.1)
        worker_task.cancel()

    test_task = loop.create_task(stop_test())

    await asyncio.gather(worker_task, test_task)
    async with aiopg.connect(dsn=db_connection_settings.dsn) as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            f'''
            SELECT EXISTS (
                SELECT FROM
                    pg_tables
                WHERE
                    schemaname = 'public' AND
                    tablename  = '{TABLE_NAME}'
                );
            '''
        )
        ret = []
        async for row in cursor:
            ret.append(row)
    assert ret == [(True,)]


@pytest.mark.asyncio
async def test_worker_creates_entries(db_connection_settings):
    worker_settings = DbWorkerSettings(period=0.1, max_batch_size=100)
    queue = asyncio.Queue()
    worker = DbWorker(connection_settings=db_connection_settings, worker_settings=worker_settings, queue=queue)

    loop = asyncio.get_event_loop()
    worker_task = loop.create_task(worker.run())

    async def stop_test():
        await asyncio.sleep(worker_settings.period + 0.1)
        worker_task.cancel()

    test_task = loop.create_task(stop_test())

    entries_count = 3

    monitor_results = (
        MonitoringResult(
            url='https://foo.com',
            timestamp=datetime.datetime.now(),
            status_code=200,
            response_time=0.1,
            regexp_match=None
        )
        for _ in range(entries_count)
    )

    for item in monitor_results:
        await queue.put(item)

    await asyncio.gather(worker_task, test_task)

    async with aiopg.connect(dsn=db_connection_settings.dsn) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f'SELECT count(*) FROM {TABLE_NAME};')
        ret = []
        async for row in cursor:
            ret.append(row)
    assert ret[0][0] == entries_count
