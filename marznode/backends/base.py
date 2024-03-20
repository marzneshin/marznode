"""What a vpn server should do"""

from abc import ABC, abstractmethod
from typing import Any

from marznode.models import User, Inbound


class VPNBackend(ABC):
    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def restart(self, config: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    async def add_user(self, user: User, inbound: Inbound) -> None:
        raise NotImplementedError

    @abstractmethod
    async def remove_user(self, user: User, inbound: Inbound) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_logs(self):
        raise NotImplementedError
