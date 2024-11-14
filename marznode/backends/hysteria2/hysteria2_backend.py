import asyncio
import json
import logging
from secrets import token_hex
from typing import AsyncIterator

import aiohttp
from aiohttp import web, ClientConnectorError

from marznode.backends.abstract_backend import VPNBackend
from marznode.backends.hysteria2._config import HysteriaConfig
from marznode.backends.hysteria2._runner import Hysteria
from marznode.models import User, Inbound
from marznode.storage import BaseStorage
from marznode.utils.key_gen import generate_password
from marznode.utils.network import find_free_port

logger = logging.getLogger(__name__)


class HysteriaBackend(VPNBackend):
    backend_type = "hysteria2"
    config_format = 2

    def __init__(self, executable_path: str, config_path: str, storage: BaseStorage):
        self._app_runner = None
        self._executable_path = executable_path
        self._storage = storage
        self._inbound_tags = ["hysteria2"]
        self._inbounds = list()
        self._users = {}
        self._auth_site = None
        self._runner = Hysteria(self._executable_path)
        self._stats_secret = None
        self._stats_port = None
        self._config_path = config_path
        self._restart_lock = asyncio.Lock()

    @property
    def running(self) -> bool:
        return self._runner.running

    @property
    def version(self):
        return self._runner.version

    def contains_tag(self, tag: str) -> bool:
        return bool(tag == "hysteria2")

    def list_inbounds(self) -> list:
        return self._inbounds

    def get_config(self) -> str:
        with open(self._config_path) as f:
            return f.read()

    def save_config(self, config: str) -> None:
        with open(self._config_path, "w") as f:
            f.write(config)

    async def start(self, config: str | None = None) -> None:
        if config is None:
            with open(self._config_path) as f:
                config = f.read()
        else:
            self.save_config(config)
        api_port = find_free_port()
        self._stats_port = find_free_port()
        self._stats_secret = token_hex(16)
        if self._auth_site:
            await self._app_runner.cleanup()
        app = web.Application()
        app.router.add_post("/", self._auth_callback)
        self._app_runner = web.AppRunner(app)
        await self._app_runner.setup()

        self._auth_site = web.TCPSite(self._app_runner, "127.0.0.1", api_port)

        await self._auth_site.start()
        cfg = HysteriaConfig(config, api_port, self._stats_port, self._stats_secret)
        cfg.register_inbounds(self._storage)
        self._inbounds = [cfg.get_inbound()]
        await self._runner.start(cfg.render())

    async def stop(self):
        await self._auth_site.stop()
        self._storage.remove_inbound("hysteria2")
        self._runner.stop()

    async def restart(self, backend_config: str | None) -> None:
        await self._restart_lock.acquire()
        try:
            await self.stop()
            await self.start(backend_config)
        finally:
            self._restart_lock.release()

    async def add_user(self, user: User, inbound: Inbound) -> None:
        password = generate_password(user.key)
        self._users.update({password: user})

    async def remove_user(self, user: User, inbound: Inbound) -> None:
        if not self._users.get(password := generate_password(user.key)):
            return
        self._users.pop(password)
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

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    data = await response.json()
        except ClientConnectorError:
            data = {}
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
