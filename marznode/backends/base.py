"""What a vpn server should do"""

from abc import ABC, abstractmethod

from marznode.models import User, Inbound


class VPNBackend(ABC):
    @abstractmethod
    async def run(self):
        raise NotImplementedError

    @abstractmethod
    async def restart(self):
        raise NotImplementedError

    @abstractmethod
    async def add_user(self, user: User, inbound: Inbound):
        raise NotImplementedError

    @abstractmethod
    async def remove_user(self, user: User, inbound: Inbound):
        raise NotImplementedError

    @abstractmethod
    async def get_logs(self):
        raise NotImplementedError
