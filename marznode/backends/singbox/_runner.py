"""run xray and capture the logs"""

import asyncio
import atexit
import logging
import signal
from collections import deque

from anyio import create_memory_object_stream, ClosedResourceError, BrokenResourceError
from anyio.streams.memory import MemoryObjectReceiveStream

from ._utils import get_version

logger = logging.getLogger(__name__)


class SingBoxRunner:
    """runs and captures sing-box logs"""

    def __init__(self, executable_path: str):
        self.executable_path = executable_path

        self.version = get_version(executable_path)
        self._process = None
        self.restarting = False

        self._snd_streams = []
        self._logs_buffer = deque(maxlen=100)
        self.stop_event = asyncio.Event()

        self._logs_task = None
        atexit.register(lambda: self.stop() if self.running else None)

    async def start(self, config_path: str):
        if self.running is True:
            raise RuntimeError("Sing-box is started already")

        cmd = [self.executable_path, "run", "--disable-color", "-c", config_path]
        self._process = await asyncio.create_subprocess_shell(
            " ".join(cmd),
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
        logger.info("sing-box %s started", self.version)

        self._logs_task = asyncio.create_task(self.__capture_process_logs())

    async def stop(self):
        """stops xray if it is started"""
        if not self.running:
            return

        self._process.terminate()
        self._process = None
        await self._logs_task

    async def restart(self, config_path: str):
        """restart sing-box"""
        if self.restarting is True:
            return

        try:
            self.restarting = True
            logger.warning("Restarting sing-box")
            self.stop()
            await self._logs_task
            await self.start(config_path)
        finally:
            self.restarting = False

    async def reload(self):
        try:
            self._process.send_signal(signal.SIGHUP)
        except OSError:
            pass

    async def __capture_process_logs(self):
        """capture the logs, push it into the stream, and store it in the deck
        note that the stream blocks sending if it's full, so a deck is necessary"""

        async def capture_stream(stream):
            while True:
                output = await stream.readline()
                for stm in self._snd_streams:
                    try:
                        await stm.send(output)
                    except (ClosedResourceError, BrokenResourceError):
                        try:
                            self._snd_streams.remove(stm)
                        except ValueError:
                            pass
                        continue
                self._logs_buffer.append(output)
                if output == b"":
                    """break in case of eof"""
                    return

        await asyncio.gather(
            capture_stream(self._process.stderr), capture_stream(self._process.stdout)
        )
        logger.warning("Sing-box stopped/died")
        self.stop_event.set()
        self.stop_event.clear()

    def get_logs_stm(self) -> MemoryObjectReceiveStream:
        new_snd_stm, new_rcv_stm = create_memory_object_stream()
        self._snd_streams.append(new_snd_stm)
        return new_rcv_stm

    def get_buffer(self):
        """makes a copy of the buffer, so it could be read multiple times
        the buffer is never cleared in case logs from xray's exit are useful"""
        return self._logs_buffer.copy()

    @property
    def running(self):
        return self._process and self._process.returncode is None
