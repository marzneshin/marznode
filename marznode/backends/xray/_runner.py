"""run xray and capture the logs"""

import asyncio
import atexit
import logging
import re
from collections import deque

from anyio import create_memory_object_stream, ClosedResourceError, BrokenResourceError
from anyio.streams.memory import MemoryObjectReceiveStream

from ._config import XrayConfig
from ._utils import get_version

logger = logging.getLogger(__name__)


class XrayCore:
    """runs and captures xray logs"""

    def __init__(self, executable_path: str, assets_path: str):
        self.executable_path = executable_path
        self.assets_path = assets_path

        self.version = get_version(executable_path)
        self._process = None
        self.restarting = False

        self._snd_streams = []
        self._logs_buffer = deque(maxlen=100)
        self._env = {"XRAY_LOCATION_ASSET": assets_path}
        self.stop_event = asyncio.Event()

        atexit.register(lambda: asyncio.run(self.stop()) if self.running else None)

    async def start(self, config: XrayConfig):
        if self.running is True:
            raise RuntimeError("Xray is started already")

        if config.get("log", {}).get("loglevel") in ("none", "error"):
            config["log"]["loglevel"] = "warning"

        cmd = [self.executable_path, "run", "-config", "stdin:"]
        self._process = await asyncio.create_subprocess_shell(
            " ".join(cmd),
            env=self._env,
            stdin=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
        self._process.stdin.write(str.encode(config.to_json()))
        await self._process.stdin.drain()
        self._process.stdin.close()
        await self._process.stdin.wait_closed()
        logger.info("Xray core %s started", self.version)

        logs_stm = self.get_logs_stm()
        asyncio.create_task(self.__capture_process_logs())

        async def reach_startup_result(stream):
            async for line in stream:
                if line == b"" or re.match(
                    r".*\[Warning] core: Xray \d+\.\d+\.\d+ started", line.decode()
                ):  # either start or die
                    logs_stm.close()
                    return

        try:
            await asyncio.wait_for(reach_startup_result(logs_stm), timeout=4)
        except asyncio.TimeoutError:
            pass

    async def stop(self):
        """stops xray if it is started"""
        if not self.running:
            return

        self._process.terminate()
        try:
            await asyncio.wait_for(self._process.wait(), timeout=3)
        except asyncio.TimeoutError:
            logger.debug("killing xray process")
            self._process.kill()
        self._process = None

    async def restart(self, config: XrayConfig):
        """restart xray"""
        if self.restarting is True:
            return

        try:
            self.restarting = True
            logger.warning("Restarting Xray core")
            await self.stop()
            await self.start(config)
        finally:
            self.restarting = False

    async def __capture_process_logs(self):
        """capture the logs, push it into the stream, and store it in the deck
        note that the stream blocks sending if it's full, so a deck is necessary"""
        process = self._process
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
            capture_stream(process.stderr), capture_stream(process.stdout)
        )

        await process.communicate()
        logger.warning("Xray stopped/died")
        self.stop_event.set()

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
