"""What a vpn server should do"""

from abc import ABC, abstractmethod

from marznode.backends.base import VPNBackend
from marznode.backends.xray.api.exceptions import EmailExistsError
from marznode.backends.xray.api.types.account import accounts_map
from marznode.models import User, Inbound


class XrayBackend(VPNBackend):
    async def run(self):
        raise NotImplementedError

    async def restart(self):
        raise NotImplementedError

    async def add_user(self, user: User, inbound: Inbound):
        email = f"{User.id}.{User.username}"

        account_class = accounts_map[inbound.protocol]
        user_account = account_class(email=email, seed=user.key)

        try:
            await self.api.add_inbound_user(Inbound.tag, user_account)
        except EmailExistsError:
            raise

    async def remove_user(self, user: User, inbound: Inbound):
        raise NotImplementedError

    async def get_logs(self):
        raise NotImplementedError
