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

    async def add_user(self, user: User, inbounds: list[Inbound]) -> None:
        self.storage["users"][user["id"]] = {**user, "inbound_tags": inbounds}

    async def remove_user(self, user_id: int) -> None:
        del self.storage["users"][user_id]

    async def update_user_inbounds(self, user: User, inbounds: list[Inbound]) -> None:
        self.storage["users"][user].inbounds = inbounds

    def set_inbounds(self, inbounds: dict[str, dict]) -> None:
        self.storage["inbounds"] = inbounds

    async def flush_users(self):
        self.storage["users"] = {}
