"""
The grpc Service to add/update/delete users
Right now it only supports Xray but that is subject to change
"""
import json
import logging
from collections import defaultdict

from grpclib.server import Stream

from marznode.storage import BaseStorage
from marznode.xray_api import XrayAPI
from marznode.xray_api.exceptions import EmailExistsError, EmailNotFoundError
from marznode.xray_api.types.account import accounts_map
from .service_grpc import MarzServiceBase
from .service_pb2 import UserData, Empty, InboundsResponse, Inbound, UsersStats, LogLine
from .service_pb2 import XrayConfig as XrayConfig_pb2
from .. import config
from ..xray.base import XrayCore
from ..xray.config import XrayConfig

logger = logging.getLogger(__name__)


class MarzService(MarzServiceBase):
    """Add/Update/Delete users based on calls from the client"""
    def __init__(self, api: XrayAPI, storage: BaseStorage, xray: XrayCore):
        self.api = api
        self.storage = storage
        self.xray = xray

    async def _add_user(self, user_data: UserData):
        user = user_data.user
        inbound_addition_list = [i.tag for i in user_data.inbounds]
        inbound_additions = await self.storage.list_inbounds(tag=inbound_addition_list)
        await self.storage.add_user({"id": user.id,
                                     "username": user.username,
                                     "key": user.key},
                                    [i["tag"] for i in inbound_additions])
        storage_user = await self.storage.list_users(user.id)
        await self._add_user_to_inbounds(storage_user, set(inbound_addition_list))

    async def _add_user_to_inbounds(self, storage_user, inbounds: set[str]):
        logger.info("Adding user `%s` to inbounds `%s`", storage_user["username"], str(inbounds))
        inbound_additions = await self.storage.list_inbounds(tag=inbounds)
        email = f"{storage_user['id']}.{storage_user['username']}"
        key = storage_user['key']
        for i in inbound_additions:
            account_class = accounts_map[i["protocol"]]
            user_account = account_class(email=email, seed=key)
            inbound_tag = i["tag"]
            try:
                await self.api.add_inbound_user(inbound_tag, user_account)
            except EmailExistsError:
                logger.warning("Request to add an already existing user `%s` to tag `%s`.",
                               email, inbound_tag)
            else:
                logger.debug("User `%s` added to inbound `%s`", email, inbound_tag)

    async def _remove_user(self, user):
        tags = user["inbound_tags"]
        email = f"{user['id']}.{user['username']}"

        await self._remove_email_from_inbounds(email, tags)
        await self.storage.remove_user(user["id"])

    async def _remove_email_from_inbounds(self, email, tags: list[str]):
        for tag in tags:
            try:
                await self.api.remove_inbound_user(tag, email)
            except EmailNotFoundError:
                logger.warning("Request to remove non existing user `%s` from tag `%s`",
                               email, tag)
            else:
                logger.debug("User `%s` removed from inbound `%s`", email, tag)

    async def _update_user(self, user_data: UserData):
        logger.debug(user_data)
        user = user_data.user
        storage_user = await self.storage.list_users(user.id)
        if not storage_user:
            return await self._add_user(user_data)
        elif not user_data.inbounds:
            return await self._remove_user(storage_user)

        storage_inbounds = set(storage_user["inbound_tags"])
        new_inbounds = {i.tag for i in user_data.inbounds}
        added_inbounds = new_inbounds - storage_inbounds
        removed_inbounds = storage_inbounds - new_inbounds
        email = f"{storage_user['id']}.{storage_user['username']}"
        await self._remove_email_from_inbounds(email, removed_inbounds)
        await self._add_user_to_inbounds(storage_user, added_inbounds)
        self.storage.storage["users"][user.id]["inbound_tags"] = new_inbounds

    async def SyncUsers(self,
                        stream: 'Stream[UserData,'
                                'Empty]') -> None:
        async for user_data in stream:
            await self._update_user(user_data)

    async def FetchInbounds(self,
                            stream: 'grpclib.server.Stream[marznode.service.service_pb2.Empty, '
                                    'marznode.service.service_pb2.InboundsResponse]') -> None:
        await stream.recv_message()
        stored_inbounds = await self.storage.list_inbounds()
        inbounds = [Inbound(tag=i["tag"], config=json.dumps(i)) for i in stored_inbounds]
        await stream.send_message(InboundsResponse(inbounds=inbounds))

    async def RepopulateUsers(self,
                              stream: 'grpclib.server.Stream[marznode.service.service_pb2.UsersData, '
                                      'marznode.service.service_pb2.Empty]') -> None:
        users_data = (await stream.recv_message()).users_data
        for user_data in users_data:
            await self._update_user(user_data)
        user_ids = {user_data.user.id for user_data in users_data}
        for storage_user in await self.storage.list_users():
            if storage_user["id"] not in user_ids:
                await self._remove_user(storage_user)
        await stream.send_message(Empty())

    async def FetchUsersStats(self,
                              stream: Stream[Empty, UsersStats]) -> None:
        await stream.recv_message()
        api_stats = await self.api.get_users_stats(reset=True)
        stats = defaultdict(int)
        for stat in api_stats:
            uid = int(stat.name.split(".")[0])
            stats[uid] += stat.value
        user_stats = [UsersStats.UserStats(uid=uid, usage=usage) for uid, usage in stats.items()]
        await stream.send_message(UsersStats(users_stats=user_stats))

    async def StreamXrayLogs(self,
                             stream: Stream[Empty, LogLine]) -> None:
        req = await stream.recv_message()
        if req.include_buffer:
            for line in self.xray.get_buffer():
                await stream.send_message(LogLine(line=line))
        log_stm = await self.xray.get_logs_stm()
        async with log_stm:
            async for line in log_stm:
                await stream.send_message(LogLine(line=line))

    async def FetchXrayConfig(self, stream: Stream[Empty, XrayConfig_pb2]) -> None:
        await stream.recv_message()
        with open(config.XRAY_CONFIG_PATH, 'r') as f:
            content = f.read()
        await stream.send_message(XrayConfig_pb2(configuration=content))

    async def RestartXray(self, stream: Stream[XrayConfig_pb2, InboundsResponse]) -> None:
        message = await stream.recv_message()
        xconfig = XrayConfig(message.configuration, storage=self.storage)
        await self.storage.flush_users()
        await self.xray.restart(xconfig)
        stored_inbounds = await self.storage.list_inbounds()
        inbounds = [Inbound(tag=i["tag"], config=json.dumps(i)) for i in stored_inbounds]
        await stream.send_message(InboundsResponse(inbounds=inbounds))
        with open(config.XRAY_CONFIG_PATH, 'w') as f:
            f.write(message.configuration)
