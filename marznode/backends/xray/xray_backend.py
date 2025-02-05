"""What a vpn server should do"""

import asyncio
import json
import logging
from collections import defaultdict

from marznode.backends.abstract_backend import VPNBackend
from marznode.backends.xray._config import XrayConfig
from marznode.backends.xray._runner import XrayCore
from marznode.backends.xray.api import XrayAPI
from marznode.backends.xray.api.exceptions import (
    EmailExistsError,
    EmailNotFoundError,
    TagNotFoundError,
)
from marznode.backends.xray.api.types.account import accounts_map
from marznode.config import XRAY_RESTART_ON_FAILURE, XRAY_RESTART_ON_FAILURE_INTERVAL
from marznode.models import User, Inbound
from marznode.storage import BaseStorage
from marznode.utils.network import find_free_port

logger = logging.getLogger(__name__)


class XrayBackend(VPNBackend):
    backend_type = "xray"
    config_format = 1

    def __init__(
        self,
        executable_path: str,
        assets_path: str,
        config_path: str,
        storage: BaseStorage,
    ):
        self._config = None
        self._inbound_tags = set()
        self._inbounds = list()
        self._api = None
        self._runner = XrayCore(executable_path, assets_path)
        self._storage = storage
        self._config_path = config_path
        self._restart_lock = asyncio.Lock()
        asyncio.create_task(self._restart_on_failure())

    @property
    def running(self) -> bool:
        return self._runner.running

    @property
    def version(self):
        return self._runner.version

    def contains_tag(self, tag: str) -> bool:
        return tag in self._inbound_tags

    def list_inbounds(self) -> list:
        return self._inbounds

    def get_config(self) -> str:
        with open(self._config_path) as f:
            return f.read()

    def save_config(self, config: str) -> None:
        with open(self._config_path, "w") as f:
            f.write(config)

    async def add_storage_users(self):
        for inbound in self._inbounds:
            for user in await self._storage.list_inbound_users(inbound.tag):
                await self.add_user(user, inbound)

    async def _restart_on_failure(self):
        while True:
            await self._runner.stop_event.wait()
            self._runner.stop_event.clear()
            if self._restart_lock.locked():
                logger.debug("Xray restarting as planned")
            else:
                logger.debug("Xray stopped unexpectedly")
                if XRAY_RESTART_ON_FAILURE:
                    await asyncio.sleep(XRAY_RESTART_ON_FAILURE_INTERVAL)
                    await self.start()
                    await self.add_storage_users()

    async def start(self, backend_config: str | None = None):
        if backend_config is None:
            with open(self._config_path) as f:
                backend_config = f.read()
        else:
            self.save_config(json.dumps(json.loads(backend_config), indent=2))
        xray_api_port = find_free_port()
        self._config = XrayConfig(backend_config, api_port=xray_api_port)
        self._config.register_inbounds(self._storage)
        self._inbound_tags = {i["tag"] for i in self._config.inbounds}
        self._inbounds = list(self._config.list_inbounds())
        self._api = XrayAPI("127.0.0.1", xray_api_port)
        await self._runner.start(self._config)

    async def stop(self):
        await self._runner.stop()
        for tag in self._inbound_tags:
            self._storage.remove_inbound(tag)
        self._inbound_tags = set()
        self._inbounds = set()

    async def restart(self, backend_config: str | None) -> list[Inbound] | None:
        # xray_config = backend_config if backend_config else self._config
        await self._restart_lock.acquire()
        try:
            if not backend_config:
                return await self._runner.restart(self._config)
            await self.stop()
            await self.start(backend_config)
        finally:
            self._restart_lock.release()

    async def add_user(self, user: User, inbound: Inbound):
        email = f"{user.id}.{user.username}"

        account_class = accounts_map[inbound.protocol]
        flow = inbound.config["flow"] or ""
        logger.debug(flow)
        user_account = account_class(
            email=email,
            seed=user.key,
            flow=flow,
        )

        try:
            await self._api.add_inbound_user(inbound.tag, user_account)
        except (EmailExistsError, TagNotFoundError):
            raise
        except OSError:
            logger.warning("user addition requested when xray api is down")

    async def remove_user(self, user: User, inbound: Inbound):
        email = f"{user.id}.{user.username}"
        try:
            await self._api.remove_inbound_user(inbound.tag, email)
        except (EmailNotFoundError, TagNotFoundError):
            raise
        except OSError:
            logger.warning("user removal requested when xray api is down")

    async def get_usages(self, reset: bool = True) -> dict[int, int]:
        try:
            api_stats = await self._api.get_users_stats(reset=reset)
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
