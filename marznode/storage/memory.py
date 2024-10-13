"""Storage backend for storing marznode data in memory"""

from .base import BaseStorage
from ..models import User, Inbound


class MemoryStorage(BaseStorage):
    """A storage backend for marznode.
    note that this isn't fit to use in production since data gets wiped on restarts
    so if Marzneshin is down users are lost until it gets back up
    """

    def __init__(self):
        self.storage = dict({"users": {}, "inbounds": {}})

    async def list_users(self, user_id: int | None = None) -> list[User] | User | None:
        if user_id:
            return self.storage["users"].get(user_id)
        return list(self.storage["users"].values())

    async def list_inbounds(
        self, tag: list[str] | str | None = None, include_users: bool = False
    ) -> list[Inbound] | Inbound | None:
        if tag is not None:
            if isinstance(tag, str):
                return self.storage["inbounds"][tag]
            return [
                self.storage["inbounds"][t]
                for t in tag
                if t in self.storage["inbounds"]
            ]
            # return [i for i in self.storage["inbounds"].values() if i.tag in tag]
        return list(self.storage["inbounds"].values())

    async def list_inbound_users(self, tag: str) -> list[User]:
        users = []
        for user in self.storage["users"].values():
            for inbound in user.inbounds:
                if inbound.tag == tag:
                    users.append(user)
                    break
        return users

    async def remove_user(self, user: User) -> None:
        del self.storage["users"][user.id]

    async def update_user_inbounds(self, user: User, inbounds: list[Inbound]) -> None:
        if self.storage["users"].get(user.id):
            self.storage["users"][user.id].inbounds = inbounds
        user.inbounds = inbounds
        self.storage["users"][user.id] = user

    def register_inbound(self, inbound: Inbound) -> None:
        self.storage["inbounds"][inbound.tag] = inbound

    def remove_inbound(self, inbound: Inbound | str) -> None:
        tag = inbound if isinstance(inbound, str) else inbound.tag
        if tag in self.storage["inbounds"]:
            self.storage["inbounds"].pop(tag)
        for user_id, user in self.storage["users"].items():
            user.inbounds = list(filter(lambda inb: inb.tag != tag, user.inbounds))

    async def flush_users(self):
        self.storage["users"] = {}
