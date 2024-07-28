import asyncio
import atexit
import logging
import tempfile

import yaml

logger = logging.getLogger(__name__)


class Hysteria:
    def __init__(self, executable_path: str):
        self._executable_path = executable_path
        self._process = None
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
        """        while output := await self._process.stderr.readline():
            print()
            print(output)"""

    def stop(self):
        if self._process:
            self._process.terminate()

    @property
    def started(self):
        if not self._process or self._process.returncode is not None:
            return False
        return True
