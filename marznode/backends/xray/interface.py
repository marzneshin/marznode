"""What a vpn server should do"""

import asyncio
import logging
from collections import defaultdict

from marznode import config
from marznode.backends.base import VPNBackend
from marznode.backends.xray._config import XrayConfig
from marznode.backends.xray._runner import XrayCore
from marznode.backends.xray.api import XrayAPI
from marznode.backends.xray.api.exceptions import (
    EmailExistsError,
    EmailNotFoundError,
    TagNotFoundError,
)
from marznode.backends.xray.api.types.account import accounts_map
from marznode.models import User, Inbound
from marznode.storage import BaseStorage
from marznode.utils.network import find_free_port

logger = logging.getLogger(__name__)


class XrayBackend(VPNBackend):
    def __init__(self, storage: BaseStorage):
        xray_api_port = find_free_port()
        self._config = XrayConfig(config.XRAY_CONFIG_PATH, api_port=xray_api_port)
        xray_inbounds = [
            Inbound(tag=i["tag"], protocol=i["protocol"], config=i)
            for i in self._config.inbounds_by_tag.values()
        ]
        storage.set_inbounds(xray_inbounds)
        self._inbound_tags = {i.tag for i in xray_inbounds}
        self._api = XrayAPI("127.0.0.1", xray_api_port)
        self._runner = XrayCore(config.XRAY_EXECUTABLE_PATH, config.XRAY_ASSETS_PATH)

    def contains_tag(self, tag: str) -> bool:
        return tag in self._inbound_tags

    async def start(self):
        await self._runner.start(self._config)

    async def restart(self, backend_config: str | None) -> list[Inbound] | None:
        # xray_config = backend_config if backend_config else self._config
        if not backend_config:
            return await self._runner.restart(self._config)
        api_port = find_free_port()
        self._config = XrayConfig(backend_config, api_port=api_port)
        xray_inbounds = [
            Inbound(tag=i["tag"], protocol=i["protocol"], config=i)
            for i in self._config.inbounds_by_tag.values()
        ]
        await self._runner.restart(self._config)
        self._api = XrayAPI("127.0.0.1", api_port)
        self._inbound_tags = {i.tag for i in xray_inbounds}
        await asyncio.sleep(0.1)  # wait until xray api is up,
        # I'd rather check if the port is open manually but this is lazier. for now.
        return xray_inbounds

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

    async def remove_user(self, user: User, inbound: Inbound):
        email = f"{user.id}.{user.username}"
        try:
            await self._api.remove_inbound_user(inbound.tag, email)
        except (EmailNotFoundError, TagNotFoundError):
            raise

    async def get_usages(self, reset: bool = True) -> dict[int, int]:
        api_stats = await self._api.get_users_stats(reset=reset)
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
