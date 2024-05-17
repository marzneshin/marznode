"""run xray and capture the logs"""

import asyncio
import atexit
import logging
from collections import deque

from anyio import create_memory_object_stream, ClosedResourceError, BrokenResourceError

from ._config import XrayConfig
from ._utils import get_version

logger = logging.getLogger(__name__)


class XrayCore:
    """runs and captures xray logs"""

    def __init__(self, executable_path: str, assets_path: str):
        self.executable_path = executable_path
        self.assets_path = assets_path

        self.version = get_version(executable_path)
        self.process = None
        self.restarting = False

        self._snd_streams, self._rcv_streams = [], []
        self._logs_buffer = deque(maxlen=100)
        self._env = {"XRAY_LOCATION_ASSET": assets_path}

        atexit.register(lambda: self.stop() if self.started else None)

    async def start(self, config: XrayConfig):
        if self.started is True:
            raise RuntimeError("Xray is started already")

        if config.get("log", {}).get("logLevel") in ("none", "error"):
            config["log"]["logLevel"] = "warning"

        cmd = [self.executable_path, "run", "-config", "stdin:"]
        self.process = await asyncio.create_subprocess_shell(
            " ".join(cmd),
            env=self._env,
            stdin=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
        self.process.stdin.write(str.encode(config.to_json()))
        await self.process.stdin.drain()
        self.process.stdin.close()
        await self.process.stdin.wait_closed()
        logger.info("Xray core %s started", self.version)

        asyncio.create_task(self.__capture_process_logs())

    def stop(self):
        """stops xray if it is started"""
        if not self.started:
            return

        self.process.terminate()
        self.process = None
        logger.warning("Xray core stopped")

    async def restart(self, config: XrayConfig):
        """restart xray"""
        if self.restarting is True:
            return

        try:
            self.restarting = True
            logger.warning("Restarting Xray core...")
            self.stop()
            await self.start(config)
        finally:
            self.restarting = False

    async def __capture_process_logs(self):
        """capture the logs, push it into the stream, and store it in the deck
        note that the stream blocks sending if it's full, so a deck is necessary"""
        while output := await self.process.stdout.readline():
            for stm in self._snd_streams:
                try:
                    await stm.send(output)
                except (ClosedResourceError, BrokenResourceError):
                    self._snd_streams.remove(stm)
                    continue
            self._logs_buffer.append(output)

    def get_logs_stm(self):
        new_snd_stm, new_rcv_stm = create_memory_object_stream()
        self._snd_streams.append(new_snd_stm)
        return new_rcv_stm

    def get_buffer(self):
        """makes a copy of the buffer, so it could be read multiple times
        the buffer is never cleared in case logs from xray's exit are useful"""
        return self._logs_buffer.copy()

    @property
    def started(self):
        if not self.process or self.process.returncode is not None:
            return False
        return True
