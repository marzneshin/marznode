"""
The grpc Service to add/update/delete users
Right now it only supports Xray but that is subject to change
"""
import json
import logging

from grpclib.server import Stream

from marznode.storage import BaseStorage
from marznode.xray_api import XrayAPI
from marznode.xray_api.exceptions import EmailExistsError, EmailNotFoundError
from marznode.xray_api.types.account import accounts_map
from .service_grpc import MarzServiceBase
from .service_pb2 import UserUpdate, Empty, InboundsResponse, Inbound

logger = logging.getLogger(__name__)


class XrayService(MarzServiceBase):
    """Add/Update/Delete users based on calls from the client"""
    def __init__(self, api: XrayAPI, storage: BaseStorage):
        self.api = api
        self.storage = storage

    async def _add_user(self, user_update: UserUpdate):
        user = user_update.user
        inbound_addition_list = [i.tag for i in user_update.inbound_additions]
        logger.debug("Request to add user `%s` to inbounds `%s`", user.username, str(inbound_addition_list))
        inbound_additions = await self.storage.list_inbounds(tag=inbound_addition_list)
        email = f"{user.id}.{user.username}"
        key = user.key
        for i in inbound_additions:
            account_class = accounts_map[i["protocol"]]
            user_account = account_class(email=email, seed=key)
            inbound_tag = i["tag"]
            try:
                await self.api.add_inbound_user(inbound_tag, user_account)
            except EmailExistsError:
                logger.warning("Request to add an already existing user `%s` to tagg `%s`.",
                               email, inbound_tag)
            else:
                logger.debug("User `%s` added to inbound `%s`", email, inbound_tag)
        if not await self.storage.list_users(user.id):
            await self.storage.add_user({"id": user.id,
                                         "username": user.username,
                                         "key": user.key},
                                        [i["tag"] for i in inbound_additions])

    async def _remove_user(self, email: str, tags: list[str]):
        for tag in tags:
            try:
                await self.api.remove_inbound_user(tag, email)
            except EmailNotFoundError:
                logger.warning("Request to remove non existing user `%s` from tag `%s`",
                               email, tag)
            else:
                logger.debug("User `%s` removed from inbound `%s`", email, tag)

    async def AddUser(self,
                      stream: Stream[UserUpdate, Empty]
                      ) -> None:
        user_update = await stream.recv_message()
        await self._add_user(user_update)

        await stream.send_message(Empty())

    async def RemoveUser(self,
                         stream: Stream[UserUpdate, Empty]):
        user_update = await stream.recv_message()
        user = user_update.user
        inbound_reduction_list = [i.tag for i in user_update.inbound_reductions]
        logger.debug("Request to remove user `%s` from inbounds `%s`",
                     user.username, str(inbound_reduction_list))
        storage_user = await self.storage.list_users(user.id)
        if not storage_user:
            logger.warning("Request to remove non existing user `%s`", user.username)
            await stream.send_message(Empty())
            return
        tags = storage_user["inbound_tags"]
        email = f"{user.id}.{user.username}"
        await self._remove_user(email, tags)

        if await self.storage.list_users(user.id):
            await self.storage.remove_user(user.id)
        await stream.send_message(Empty())

    async def UpdateUserInbounds(self,
                                 stream: 'grpclib.server.Stream['
                                         'marznode.service.service_pb2.UpdateUserInboundsRequest, '
                                         'marznode.service.service_pb2.Empty]') -> None:
        pass

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
        data = await stream.recv_message()
        storage_users = await self.storage.list_users()
        for u in storage_users:
            # remove all users from xray
            inbound_tags = u["inbound_tags"]
            await self._remove_user(f"{u['id']}.{u['username']}", inbound_tags)
        await self.storage.flush_users()

        for update in data.users_updates:
            await self._add_user(update)
        await stream.send_message(Empty())

    async def FetchUsersStats(self,
                              stream: 'grpclib.server.Stream[marznode.service.service_pb2.Empty, '
                                      'marznode.service.service_pb2.UsersStats]') -> None:
        pass
