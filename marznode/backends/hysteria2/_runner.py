import asyncio
import atexit
import logging
import tempfile
from collections import deque

import yaml
from anyio import BrokenResourceError, ClosedResourceError, create_memory_object_stream

logger = logging.getLogger(__name__)


class Hysteria:
    def __init__(self, executable_path: str):
        self._executable_path = executable_path
        self._process = None
        self._snd_streams = []
        self._logs_buffer = deque(maxlen=100)
        self._capture_task = None
        atexit.register(lambda: self.stop() if self.started else None)

    async def start(self, config: dict):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as temp_file:
            yaml.dump(config, temp_file)
        cmd = [self._executable_path, "server", "-c", temp_file.name]

        self._process = await asyncio.create_subprocess_shell(
            " ".join(cmd),
            stdin=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
        logger.info("Hysteria has started")
        asyncio.create_task(self.__capture_process_logs())

    def stop(self):
        if self.started:
            self._process.terminate()

    @property
    def started(self):
        return self._process and self._process.returncode is None

    async def __capture_process_logs(self):
        """capture the logs, push it into the stream, and store it in the deck
        note that the stream blocks sending if it's full, so a deck is necessary"""

        async def capture_stream(stream):
            while True:
                output = await stream.readline()
                if output == b"":
                    """break in case of eof"""
                    return
                for stm in self._snd_streams:
                    try:
                        await stm.send(output)
                    except (ClosedResourceError, BrokenResourceError):
                        self._snd_streams.remove(stm)
                        continue
                self._logs_buffer.append(output)

        await asyncio.gather(
            capture_stream(self._process.stderr), capture_stream(self._process.stdout)
        )

    def get_logs_stm(self):
        new_snd_stm, new_rcv_stm = create_memory_object_stream()
        self._snd_streams.append(new_snd_stm)
        return new_rcv_stm

    def get_buffer(self):
        """makes a copy of the buffer, so it could be read multiple times
        the buffer is never cleared in case logs from xray's exit are useful"""
        return self._logs_buffer.copy()
