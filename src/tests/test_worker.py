# When testing, we can do all sort of weird stuff
# pylint: disable = protected-access
import asyncio
from unittest import mock

import pytest

from monitor.worker.worker import Worker


def test_create_worker():
    period = 2.0
    name = 'TestWorkerName'
    worker = Worker(period=period, name=name)
    assert worker._period == period
    assert worker._name == name


@pytest.mark.asyncio
async def test_worker_runs():
    period = 0.1
    calls = 2

    worker = Worker(period=period)
    worker.task = mock.AsyncMock()
    loop = asyncio.get_event_loop()
    worker_task = loop.create_task(worker.run())

    async def stop_test():
        await asyncio.sleep(period * calls - 0.1)  # it may be fast enough to call more times
        worker_task.cancel()

    test_task = loop.create_task(stop_test())

    await asyncio.gather(worker_task, test_task)

    assert worker.task.call_count == calls
