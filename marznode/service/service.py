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

    async def AddUser(self,
                      stream: Stream[UserUpdate, Empty]
                      ) -> None:
        user_update = await stream.recv_message()
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
                               user.username, inbound_tag)
            else:
                logger.debug("User `%s` added to inbound `%s`", user.username, inbound_tag)
        if not await self.storage.list_users(user.id):
            await self.storage.add_user({"id": user.id,
                                         "username": user.username,
                                         "key": user.key},
                                        [i["tag"] for i in inbound_additions])

        await stream.send_message(Empty())

    async def RemoveUser(self,
                         stream: Stream[UserUpdate, Empty]):
        user_update = await stream.recv_message()
        user = user_update.user
        inbound_reduction_list = [i.tag for i in user_update.inbound_reductions]
        logger.debug("Request to remove user `%s` from inbounds `%s`",
                     user.username, str(inbound_reduction_list))
        inbounds = await self.storage.list_inbounds(tag=inbound_reduction_list)
        email = f"{user.id}.{user.username}"
        for i in inbounds:
            tag = i["tag"]
            try:
                await self.api.remove_inbound_user(tag, email)
            except EmailNotFoundError:
                logger.warning("Request to remove non existing user `%s` from tag `%s`",
                               user.username, tag)
            else:
                logger.debug("User `%s` removed from inbound `%s`", user.username, tag)
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
        pass

    async def FetchUsersStats(self,
                              stream: 'grpclib.server.Stream[marznode.service.service_pb2.Empty, '
                                      'marznode.service.service_pb2.UsersStats]') -> None:
        pass
