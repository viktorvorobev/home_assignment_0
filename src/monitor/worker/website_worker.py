import asyncio
import datetime
import re
import time
from typing import Optional

import aiohttp

from monitor.serializers import WebsiteSetting, MonitoringResult
from monitor.utils import logger
from .worker import Worker


class WebsiteWorker(Worker):
    def __init__(self, settings: WebsiteSetting, queue: asyncio.Queue, name: str = 'BaseWorker'):
        super().__init__(period=settings.period, name=name)
        self._url = str(settings.url)
        self._regexp = re.compile(settings.regexp) if settings.regexp else None
        self._queue = queue

    async def task(self):
        result = await self._check_website_status()
        logger.debug('Monitoring result for %s: %s', self._url, result.model_dump())
        try:
            self._queue.put_nowait(result)
        except asyncio.QueueFull as error:
            logger.error('Queue overflow! %s: %s', error.__class__.__name__, error)

    async def _check_website_status(self) -> MonitoringResult:
        timestamp = datetime.datetime.now()
        start_time = time.time()
        status_code, text = await self._get_url_status()
        response_time = time.time() - start_time
        regexp_match = await self._parse_by_regexp(text)
        return MonitoringResult(
            timestamp=timestamp,
            status_code=status_code,
            response_time=response_time,
            regexp_match=regexp_match,
        )

    async def _get_url_status(self) -> tuple[int, str]:
        async with aiohttp.ClientSession() as session:
            try:
                # timeout for cases when site doesn't respond for too long
                async with session.get(self._url, timeout=self._period) as response:
                    status_code = response.status
                    text = await response.text()
                    return status_code, text
            except (aiohttp.ClientConnectionError, asyncio.TimeoutError) as error:
                logger.error('Failed to get status for %s. %s: %s', self._url, error.__class__.__name__, error)
                # assume that connection error is not our fault, but the error log should give a clue
                return 500, ''

    async def _parse_by_regexp(self, text) -> Optional[bool]:
        if not self._regexp:
            return None
        loop = asyncio.get_running_loop()

        # in case there are some heavy calculations
        if await loop.run_in_executor(None, self._regexp.search, text):
            return True

        return False
