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
from marznode.storage import BaseStorage
from marznode.utils.key_gen import generate_password
from marznode.utils.network import find_free_port

logger = logging.getLogger(__name__)


class HysteriaBackend(VPNBackend):
    def __init__(self, executable_path: str, storage: BaseStorage):
        self._executable_path = executable_path
        self._storage = storage
        self._inbounds = ["hysteria2"]
        self._users = {}
        self._auth_site = None
        self._runner = Hysteria(self._executable_path)
        self._stats_secret = None
        self._stats_port = None

    def contains_tag(self, tag: str) -> bool:
        return bool(tag == "hysteria2")

    async def start(self, config_path: str) -> None:
        api_port = find_free_port()
        self._stats_port = find_free_port()
        self._stats_secret = token_hex(16)
        if self._auth_site:
            await self._auth_site.stop()
        app = web.Application()
        app.router.add_post("/", self._auth_callback)
        app_runner = web.AppRunner(app)
        await app_runner.setup()

        self._auth_site = web.TCPSite(app_runner, "127.0.0.1", api_port)

        await self._auth_site.start()
        with open(config_path) as f:
            config = f.read()
        cfg = HysteriaConfig(config, api_port, self._stats_port, self._stats_secret)
        cfg.register_inbounds(self._storage)
        await self._runner.start(cfg.render())

    async def stop(self):
        await self._auth_site.stop()
        self._storage.remove_inbound("hysteria2")
        self._runner.stop()

    async def restart(self, backend_config: Any) -> None:
        await self.stop()
        await self.start(backend_config)

    async def add_user(self, user: User, inbound: Inbound) -> None:
        password = generate_password(user.key)
        self._users.update({password: user})

    async def remove_user(self, user: User, inbound: Inbound) -> None:
        self._users.pop(user.key)
        url = "http://127.0.0.1:" + str(self._stats_port) + "/kick"
        headers = {"Authorization": self._stats_secret}

        payload = json.dumps([str(user.id) + "." + user.username])
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload, headers=headers):
                pass

    async def get_logs(self, include_buffer: bool) -> AsyncIterator:
        if include_buffer:
            buffer = self._runner.get_buffer()
            for line in buffer:
                yield line
        log_stm = self._runner.get_logs_stm()
        async with log_stm:
            async for line in log_stm:
                yield line

    async def get_usages(self):
        url = "http://127.0.0.1:" + str(self._stats_port) + "/traffic?clear=1"
        headers = {"Authorization": self._stats_secret}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
        usages = {}
        for user_identifier, usage in data.items():
            uid = int(user_identifier.split(".")[0])
            usages[uid] = usage["tx"] + usage["rx"]
        return usages

    async def _auth_callback(self, request: web.Request):
        user_key = (await request.json())["auth"]
        if user := self._users.get(user_key):
            return web.Response(
                body=json.dumps({"ok": True, "id": str(user.id) + "." + user.username}),
            )
        return web.Response(status=404)
