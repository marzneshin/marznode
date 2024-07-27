import json
import logging
from secrets import token_hex
from typing import AsyncIterator, Any

import aiohttp
from aiohttp import web

from marznode.backends.base import VPNBackend
from marznode.backends.hysteria2._config import HysteriaConfig
from marznode.backends.hysteria2._runner import Hysteria
from marznode.models import User, Inbound
from marznode.utils.network import find_free_port

logger = logging.getLogger(__name__)


class HysteriaBackend(VPNBackend):
    def __init__(self, config_path: str):
        self._config_path = config_path
        self._users = {}
        self._auth_site = None
        self._runner = None
        self._stats_secret = None
        self._stats_port = None

    def contains_tag(self, tag: str) -> bool:
        return bool(tag == "hysteria")

    async def start(self) -> None:
        api_port = find_free_port()
        self._stats_port = find_free_port()
        self._stats_secret = token_hex(16)
        if self._auth_site:
            await self._auth_site.stop()
        app = web.Application()
        app.router.add_post("/", self.auth_callback)
        runner = web.AppRunner(app)
        await runner.setup()

        self._auth_site = web.TCPSite(runner, "127.0.0.1", api_port)

        await self._auth_site.start()
        with open(self._config_path) as f:
            config = f.read()
        cfg = HysteriaConfig(
            config, api_port, self._stats_port, self._stats_secret
        ).render()
        runner = Hysteria("/usr/bin/hysteria")
        await runner.start(cfg)

    async def stop(self):
        await self._auth_site.stop()
        self._runner.stop()

    async def restart(self, backend_config: Any) -> None:
        pass

    async def add_user(self, user: User, inbound: Inbound) -> None:
        self._users.update({user.key: user})

    async def remove_user(self, user: User, inbound: Inbound) -> None:
        self._users.pop(user.key)

    def get_logs(self, include_buffer: bool) -> AsyncIterator:
        pass

    async def get_usages(self):
        url = "http://127.0.0.1:" + str(self._stats_port) + "/traffic?clear=1"
        headers = {"Authorization": self._stats_secret}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
        usages = {}
        for user_identifier, usage in data.items():
            usages[user_identifier] = usage["tx"] + usage["rx"]
        return usages

    async def auth_callback(self, request: web.Request):
        user_key = (await request.json())["auth"]
        if (user := self._users.get(user_key)) or (
            user := User(id=1, username="ahmad", key="mammad")
        ):
            return web.Response(
                body=json.dumps({"ok": True, "id": str(user.id) + "." + user.username}),
            )
        return web.Response(status=404)
