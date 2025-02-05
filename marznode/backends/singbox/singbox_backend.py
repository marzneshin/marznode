"""handles sb"""

import asyncio
import json
import logging
from collections import defaultdict

from marznode.backends.abstract_backend import VPNBackend
from marznode.backends.singbox._config import SingBoxConfig
from marznode.backends.singbox._runner import SingBoxRunner
from marznode.backends.singbox._stats import SingBoxAPI
from marznode.config import (
    SING_BOX_RESTART_ON_FAILURE,
    SING_BOX_RESTART_ON_FAILURE_INTERVAL,
    SING_BOX_USER_MODIFICATION_INTERVAL,
)
from marznode.models import User, Inbound
from marznode.storage import BaseStorage
from marznode.utils.network import find_free_port

logger = logging.getLogger(__name__)


class SingBoxBackend(VPNBackend):
    backend_type = "sing-box"
    config_format = 1

    def __init__(
        self,
        executable_path: str,
        config_path: str,
        storage: BaseStorage,
    ):
        self._config = None
        self._config_update_event = asyncio.Event()
        self._inbound_tags = set()
        self._inbounds = list()
        self._api = None
        self._runner = SingBoxRunner(executable_path)
        self._storage = storage
        self._config_path = config_path
        self._full_config_path = self._config_path + ".full"
        self._restart_lock = asyncio.Lock()
        self._config_modification_lock = asyncio.Lock()
        asyncio.create_task(self._restart_on_failure())
        asyncio.create_task(self._user_update_handler())

    @property
    def running(self) -> bool:
        return self._runner.running

    @property
    def version(self):
        return self._runner.version

    async def _user_update_handler(self):
        while True:
            await asyncio.sleep(SING_BOX_USER_MODIFICATION_INTERVAL)

            logger.debug("checking for sing-box user modifications")
            async with self._config_modification_lock:
                if self._config_update_event.is_set():
                    logger.debug("updating sing-box users")
                    self._save_config(self._config.to_json(), full=True)
                    await self._runner.reload()
                    self._config_update_event.clear()

    def contains_tag(self, tag: str) -> bool:
        return tag in self._inbound_tags

    def list_inbounds(self) -> list:
        return self._inbounds

    def get_config(self) -> str:
        with open(self._config_path) as f:
            return f.read()

    def _save_config(self, config: str, full=False) -> None:
        path = self._full_config_path if full else self._config_path
        with open(path, "w") as f:
            f.write(config)

    async def add_storage_users(self):
        for inbound in self._inbounds:
            for user in await self._storage.list_inbound_users(inbound.tag):
                self._config.append_user(user, inbound)

    async def _restart_on_failure(self):
        while True:
            await self._runner.stop_event.wait()
            if self._restart_lock.locked():
                logger.debug("Sing-box restarting as planned")
            else:
                logger.debug("Sing-box stopped unexpectedly")
                if SING_BOX_RESTART_ON_FAILURE:
                    await asyncio.sleep(SING_BOX_RESTART_ON_FAILURE_INTERVAL)
                    await self.start()

    async def start(self, backend_config: str | None = None):
        if backend_config is None:
            with open(self._config_path) as f:
                backend_config = f.read()
        else:
            self._save_config(json.dumps(json.loads(backend_config), indent=2))
        api_port = find_free_port()
        self._config = SingBoxConfig(backend_config, api_port=api_port)
        self._config.register_inbounds(self._storage)
        self._inbound_tags = {i["tag"] for i in self._config.inbounds}
        self._inbounds = list(self._config.list_inbounds())
        await self.add_storage_users()
        self._save_config(self._config.to_json(), full=True)
        self._api = SingBoxAPI("127.0.0.1", api_port)
        await self._runner.start(self._full_config_path)

    async def stop(self):
        await self._runner.stop()
        for tag in self._inbound_tags:
            self._storage.remove_inbound(tag)
        self._inbound_tags = set()
        self._inbounds = set()

    async def restart(self, backend_config: str | None) -> list[Inbound] | None:
        async with self._restart_lock:
            if not backend_config:
                return await self._runner.restart(self._config)
            await self.stop()
            await self.start(backend_config)

    async def add_user(self, user: User, inbound: Inbound):
        async with self._config_modification_lock:
            self._config.append_user(user, inbound)
            self._config_update_event.set()

    async def remove_user(self, user: User, inbound: Inbound):
        async with self._config_modification_lock:
            self._config.pop_user(user, inbound)
            self._config_update_event.set()

    async def get_usages(self, reset: bool = True) -> dict[int, int]:
        try:
            api_stats = await asyncio.wait_for(
                self._api.get_users_stats(reset=reset), 3
            )
        except OSError:
            api_stats = []
        stats = defaultdict(int)
        for stat in api_stats:
            uid = int(stat.name.split(".")[0])
            stats[uid] += stat.value

        return stats

    async def get_logs(self, include_buffer: bool = True):
        if include_buffer:
            for line in self._runner.get_buffer():
                yield line
        log_stm = self._runner.get_logs_stm()
        async with log_stm:
            async for line in log_stm:
                yield line
