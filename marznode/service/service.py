"""
The grpc Service to add/update/delete users
Right now it only supports Xray but that is subject to change
"""

import json
import logging

from grpclib.server import Stream

from marznode.backends.base import VPNBackend
from marznode.storage import BaseStorage
from .service_grpc import MarzServiceBase
from .service_pb2 import (
    UserData,
    UsersData,
    Empty,
    InboundsResponse,
    Inbound,
    UsersStats,
    LogLine,
)
from .service_pb2 import XrayConfig as XrayConfig_pb2
from .. import config
from ..models import User, Inbound as InboundModel

logger = logging.getLogger(__name__)


class MarzService(MarzServiceBase):
    """Add/Update/Delete users based on calls from the client"""

    def __init__(self, storage: BaseStorage, backends: list[VPNBackend]):
        self._backends = backends
        self._storage = storage

    def _resolve_tag(self, inbound_tag: str) -> VPNBackend:
        for backend in self._backends:
            if backend.contains_tag(inbound_tag):
                return backend
        raise

    async def _add_user(self, user: User, inbounds: list[Inbound]):
        for inbound in inbounds:
            backend = self._resolve_tag(inbound.tag)
            logger.debug("adding user `%s` to inbound `%s`", user.username, inbound.tag)
            await backend.add_user(user, inbound)

    async def _remove_user(self, user: User, inbounds: list[InboundModel]):
        for inbound in inbounds:
            backend = self._resolve_tag(inbound.tag)
            logger.debug(
                "removing user `%s` from inbound `%s`", user.username, inbound.tag
            )
            await backend.remove_user(user, inbound)

    async def _update_user(self, user_data: UserData):
        user = user_data.user
        user = User(id=user.id, username=user.username, key=user.key)
        storage_user = await self._storage.list_users(user.id)
        if not storage_user and len(user_data.inbounds) > 0:
            """add the user in case there isn't any currently
            and the inbounds is non-empty"""
            inbound_tags = [i.tag for i in user_data.inbounds]
            inbound_additions = await self._storage.list_inbounds(tag=inbound_tags)
            await self._add_user(user, inbound_additions)
            await self._storage.update_user_inbounds(
                user,
                [i for i in inbound_additions],
            )
            return
        elif not user_data.inbounds and storage_user:
            """remove in case we have the user but client has sent
            us an empty list of inbounds"""
            await self._remove_user(storage_user, storage_user.inbounds)
            return await self._storage.remove_user(user)
        elif not user_data.inbounds and not storage_user:
            """we're asked to remove a user which we don't have, just pass."""
            return
        
        """otherwise synchronize the user with what 
        the client has sent us"""
        storage_tags = {i.tag for i in storage_user.inbounds}
        new_tags = {i.tag for i in user_data.inbounds}
        added_tags = new_tags - storage_tags
        removed_tags = storage_tags - new_tags
        new_inbounds = await self._storage.list_inbounds(tag=list(new_tags))
        added_inbounds = await self._storage.list_inbounds(tag=list(added_tags))
        removed_inbounds = await self._storage.list_inbounds(tag=list(removed_tags))
        await self._remove_user(storage_user, removed_inbounds)
        await self._add_user(storage_user, added_inbounds)
        await self._storage.update_user_inbounds(storage_user, new_inbounds)

    async def SyncUsers(self, stream: "Stream[UserData," "Empty]") -> None:
        async for user_data in stream:
            await self._update_user(user_data)

    async def FetchInbounds(
        self,
        stream: Stream[Empty, InboundsResponse],
    ) -> None:
        await stream.recv_message()
        stored_inbounds = await self._storage.list_inbounds()
        inbounds = [
            Inbound(tag=i.tag, config=json.dumps(i.config)) for i in stored_inbounds
        ]
        await stream.send_message(InboundsResponse(inbounds=inbounds))

    async def RepopulateUsers(
        self,
        stream: Stream[UsersData, Empty],
    ) -> None:
        users_data = (await stream.recv_message()).users_data
        for user_data in users_data:
            await self._update_user(user_data)
        user_ids = {user_data.user.id for user_data in users_data}
        for storage_user in await self._storage.list_users():
            if storage_user.id not in user_ids:
                await self._remove_user(storage_user, storage_user.inbounds)
        await stream.send_message(Empty())

    async def FetchUsersStats(self, stream: Stream[Empty, UsersStats]) -> None:
        await stream.recv_message()
        stats = await self._backends[0].get_usages()
        logger.debug(stats)
        user_stats = [
            UsersStats.UserStats(uid=uid, usage=usage) for uid, usage in stats.items()
        ]
        await stream.send_message(UsersStats(users_stats=user_stats))

    async def StreamXrayLogs(self, stream: Stream[Empty, LogLine]) -> None:
        req = await stream.recv_message()
        async for line in self._backends[0].get_logs(req.include_buffer):
            await stream.send_message(LogLine(line=line))

    async def FetchXrayConfig(self, stream: Stream[Empty, XrayConfig_pb2]) -> None:
        await stream.recv_message()
        with open(config.XRAY_CONFIG_PATH) as f:
            content = f.read()
        await stream.send_message(XrayConfig_pb2(configuration=content))

    async def RestartXray(
        self, stream: Stream[XrayConfig_pb2, InboundsResponse]
    ) -> None:
        message = await stream.recv_message()

        await self._storage.flush_users()
        inbounds = await self._backends[0].restart(message.configuration)
        logger.debug(inbounds)
        if inbounds:
            self._storage.set_inbounds(inbounds)
        pb2_inbounds = [
            Inbound(tag=i.tag, config=json.dumps(i.config)) for i in inbounds
        ]
        await stream.send_message(InboundsResponse(inbounds=pb2_inbounds))
        with open(config.XRAY_CONFIG_PATH, "w") as f:
            f.write(json.dumps(json.loads(message.configuration), indent=2))
