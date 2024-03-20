"""What a vpn server should do"""
from marznode import config
from marznode.backends.base import VPNBackend
from marznode.backends.xray._config import XrayConfig
from marznode.backends.xray._runner import XrayCore
from marznode.backends.xray.api import XrayAPI
from marznode.backends.xray.api.exceptions import EmailExistsError, EmailNotFoundError, TagNotFoundError
from marznode.backends.xray.api.types.account import accounts_map
from marznode.models import User, Inbound
from marznode.storage import BaseStorage
from marznode.utils.network import find_free_port


class XrayBackend(VPNBackend):
    def __init__(self, storage: BaseStorage):
        xray_api_port = find_free_port()
        self._config = XrayConfig(config.XRAY_CONFIG_PATH, storage, api_port=xray_api_port)
        self._api = XrayAPI("127.0.0.1", xray_api_port)
        self._runner = XrayCore(config.XRAY_EXECUTABLE_PATH, config.XRAY_ASSETS_PATH)

    async def start(self):
        await self._runner.start(self._config)

    async def restart(self, xconfig: XrayConfig | None):
        xconfig = xconfig if xconfig else self._config
        await self._runner.restart(xconfig)

    async def add_user(self, user: User, inbound: Inbound):
        email = f"{User.id}.{User.username}"

        account_class = accounts_map[inbound.protocol]
        user_account = account_class(email=email, seed=user.key)

        try:
            await self._api.add_inbound_user(inbound.tag, user_account)
        except (EmailExistsError, TagNotFoundError):
            raise

    async def remove_user(self, user: User, inbound: Inbound):
        email = f"{User.id}.{User.username}"
        try:
            await self._api.remove_inbound_user(inbound.tag, email)
        except (EmailNotFoundError, TagNotFoundError):
            raise

    async def get_logs(self):
        raise NotImplementedError
