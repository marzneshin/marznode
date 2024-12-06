"""run xray and capture the logs"""

import asyncio
import atexit
import logging
import re
from collections import deque
import os

from anyio import create_memory_object_stream, ClosedResourceError, BrokenResourceError, open_file
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

        self.error_log = None
        self.error_pipe = None

        atexit.register(lambda: self.stop() if self.running else None) 

    async def start(self, config: XrayConfig):
        if self.running is True:
            raise RuntimeError("Xray is started already")
        if config.get("log", {}).get("loglevel") in ("none", "error"):
            config["log"]["loglevel"] = "warning"
        cmd = [self.executable_path, "run", "-config", "stdin:"]

        if "error" in config["log"]:
            try:
                self.error_pipe = "/var/lib/marznode/error_pipe"
                if not os.path.exists(self.error_pipe):
                    os.mkfifo(self.error_pipe)
                self.error_log = open(config["log"]["error"], mode="ab", buffering=0)
                config["log"]["error"] = self.error_pipe
            except OSError as e:
                logger.error(f"Unable to open file {config['log']['error']}")
                raise e

        print(config["log"])
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
        async for line in logs_stm:
            if line == b"" or re.match(
                r".*\[Warning] core: Xray \d+\.\d+\.\d+ started", line.decode()
            ):  # either start or die
                logs_stm.close()
                return

    def stop(self):
        """stops xray if it is started"""
        if not self.running:
            return

        self._process.terminate()
        if self.error_log != None:
            self.error_log.close()
        if os.path.exists(self.error_pipe):
            os.remove(self.error_pipe)
        self._process = None

    async def restart(self, config: XrayConfig):
        """restart xray"""
        if self.restarting is True:
            return

        try:
            self.restarting = True
            logger.warning("Restarting Xray core")
            self.stop()
            await self.start(config)
        finally:
            self.restarting = False

    async def __capture_process_logs(self):
        """capture the logs, push it into the stream, and store it in the deck
        note that the stream blocks sending if it's full, so a deck is necessary"""
        async def capture_stream(stream, file=None):
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
        
        async def fifo_stream(fifo_path, file):
            with open(fifo_path, "rb") as fifo:
                while True:
                    output = await asyncio.to_thread(fifo.readline)
                    if output:
                        file.write(output)
                        for stm in self._snd_streams:
                            try:
                                await stm.send(output)
                            except (ClosedResourceError, BrokenResourceError):
                                try:
                                    self._snd_streams.remove(stm)
                                except ValueError:
                                    pass
                                continue
                    else:
                        await asyncio.sleep(0.1)

                    self._logs_buffer.append(output)
                    if output == b"":
                        """break in case of eof"""
                        return
        tasks = [
            capture_stream(self._process.stderr),
            capture_stream(self._process.stdout)
        ]
        if self.error_log is not None:
            tasks.append(fifo_stream(self.error_pipe, self.error_log))

        await asyncio.gather(*tasks)

        logger.warning("Xray stopped/died")
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
