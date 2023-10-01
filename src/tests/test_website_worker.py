# When testing, we can do all sort of weird stuff
# pylint: disable = protected-access
import asyncio
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from monitor.serializers import WebsiteSetting, MonitoringResult
from monitor.worker import WebsiteWorker


class CallCounter:
    def __init__(self):
        self.value = 0

    def increase(self):
        self.value += 1

    def reset(self):
        self.value = 0


server_call_counter = CallCounter()


class MockServerRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):  # pylint: disable = invalid-name
        if self.path == '/ok':
            self.send_response(200)
            self.end_headers()
        elif self.path == '/regexp':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Dummy data')
        elif self.path == '/not_found':
            self.send_response(404)
            self.end_headers()
        elif self.path == '/server_error':
            self.send_response(500)
            self.end_headers()
        server_call_counter.increase()


def get_free_port():
    server_socket = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    server_socket.bind(('localhost', 0))
    _, port = server_socket.getsockname()
    server_socket.close()
    return port


FREE_PORT = get_free_port()


class TestMockServer:
    @classmethod
    def setup_class(cls):
        # Configure mock server
        mock_server_port = get_free_port()
        mock_server = HTTPServer(('localhost', mock_server_port), MockServerRequestHandler)
        cls.mock_server = mock_server
        cls.mock_server_port = mock_server_port

        # Start running mock server in a separate thread
        # Daemon threads automatically shut down when the main process exits.
        mock_server_thread = threading.Thread(target=mock_server.serve_forever)
        mock_server_thread.daemon = True
        mock_server_thread.start()

    @pytest.mark.asyncio
    async def test_worker_creates(self):
        url = f'http://localhost:{self.mock_server_port}/ok'
        period = 5.0
        name = 'TestWorker'

        settings = WebsiteSetting(url=url, period=period)
        queue = asyncio.Queue()
        worker = WebsiteWorker(settings=settings, queue=queue, name=name)
        assert worker._name == name
        assert worker._period == period
        assert worker._url == url
        assert worker._regexp is None
        await queue.join()

    @pytest.mark.asyncio
    async def test_worker_runs(self):
        settings = WebsiteSetting(
            url=f'http://localhost:{self.mock_server_port}/ok',
            period=5.0
        )
        queue = asyncio.Queue()
        worker = WebsiteWorker(settings=settings, queue=queue)
        period = 0.1
        calls = 2

        worker._period = period

        loop = asyncio.get_event_loop()
        worker_task = loop.create_task(worker.run())

        async def stop_test():
            await asyncio.sleep(period * calls)
            worker_task.cancel()

        test_task = loop.create_task(stop_test())

        await asyncio.gather(worker_task, test_task)

        assert server_call_counter.value == calls
        server_call_counter.reset()

        assert queue.qsize() == calls
        while not queue.empty():
            result: MonitoringResult = await queue.get()
            assert result.status_code == 200
            queue.task_done()
        await queue.join()

    @pytest.mark.asyncio
    @pytest.mark.parametrize('regexp,regexp_found', (
            pytest.param('Dummy data', True, id='regexp_found'),
            pytest.param('Data dummy', False, id='regexp_not_found'),
    ))
    async def test_worker_parses_regexp_found(self, regexp: str, regexp_found: bool):
        settings = WebsiteSetting(
            url=f'http://localhost:{self.mock_server_port}/regexp',
            period=5.0,
            regexp=regexp
        )
        period = 0.1
        queue = asyncio.Queue()
        worker = WebsiteWorker(settings=settings, queue=queue)
        worker._period = period

        loop = asyncio.get_event_loop()
        worker_task = loop.create_task(worker.run())

        async def stop_test():
            await asyncio.sleep(period)
            worker_task.cancel()

        test_task = loop.create_task(stop_test())

        await asyncio.gather(worker_task, test_task)

        assert server_call_counter.value == 1
        server_call_counter.reset()

        assert queue.qsize() == 1
        result: MonitoringResult = await queue.get()
        assert result.status_code == 200
        assert result.regexp_match is regexp_found
        queue.task_done()

        await queue.join()

    @pytest.mark.asyncio
    async def test_worker_not_found(self):
        settings = WebsiteSetting(
            url=f'http://localhost:{self.mock_server_port}/not_found',
            period=5.0
        )
        queue = asyncio.Queue()
        worker = WebsiteWorker(settings=settings, queue=queue)
        period = 0.1
        calls = 2

        worker._period = period

        loop = asyncio.get_event_loop()
        worker_task = loop.create_task(worker.run())

        async def stop_test():
            await asyncio.sleep(period * calls)
            worker_task.cancel()

        test_task = loop.create_task(stop_test())

        await asyncio.gather(worker_task, test_task)

        assert server_call_counter.value == calls
        server_call_counter.reset()

        assert queue.qsize() == calls
        while not queue.empty():
            result: MonitoringResult = await queue.get()
            assert result.status_code == 404
            queue.task_done()
        await queue.join()

    @pytest.mark.asyncio
    async def test_worker_server_error(self):
        settings = WebsiteSetting(
            url=f'http://localhost:{self.mock_server_port}/server_error',
            period=5.0
        )
        queue = asyncio.Queue()
        worker = WebsiteWorker(settings=settings, queue=queue)
        period = 0.1
        calls = 2

        worker._period = period

        loop = asyncio.get_event_loop()
        worker_task = loop.create_task(worker.run())

        async def stop_test():
            await asyncio.sleep(period * calls)
            worker_task.cancel()

        test_task = loop.create_task(stop_test())

        await asyncio.gather(worker_task, test_task)

        assert server_call_counter.value == calls
        server_call_counter.reset()

        assert queue.qsize() == calls
        while not queue.empty():
            result: MonitoringResult = await queue.get()
            assert result.status_code == 500
            queue.task_done()
        await queue.join()

    @pytest.mark.asyncio
    async def test_worker_server_queue_overflow(self):
        settings = WebsiteSetting(
            url=f'http://localhost:{self.mock_server_port}/ok',
            period=5.0
        )
        queue = asyncio.Queue(maxsize=1)
        worker = WebsiteWorker(settings=settings, queue=queue)
        period = 0.1
        calls = 2

        worker._period = period

        loop = asyncio.get_event_loop()
        worker_task = loop.create_task(worker.run())

        async def stop_test():
            await asyncio.sleep(period * calls)
            worker_task.cancel()

        test_task = loop.create_task(stop_test())

        await asyncio.gather(worker_task, test_task)

        assert server_call_counter.value == 2
        server_call_counter.reset()

        assert queue.qsize() == 1
        while not queue.empty():
            result: MonitoringResult = await queue.get()
            assert result.status_code == 200
            queue.task_done()
        await queue.join()

    @pytest.mark.asyncio
    async def test_worker_connection_error(self):
        settings = WebsiteSetting(
            url='http://localhost:80/ok',  # we shouldn't be able to connect here
            period=5.0
        )
        queue = asyncio.Queue()
        worker = WebsiteWorker(settings=settings, queue=queue)
        period = 0.1
        calls = 1
        worker._period = period

        loop = asyncio.get_event_loop()
        worker_task = loop.create_task(worker.run())

        async def stop_test():
            await asyncio.sleep(period * calls)
            worker_task.cancel()

        test_task = loop.create_task(stop_test())

        await asyncio.gather(worker_task, test_task)

        assert server_call_counter.value == 0
        server_call_counter.reset()

        assert queue.qsize() == 1
        while not queue.empty():
            result: MonitoringResult = await queue.get()
            assert result.status_code == 500
            queue.task_done()
        await queue.join()
