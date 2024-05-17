"""Methods to update Xray-core users/inbounds"""

import grpclib

from .base import XrayAPIBase
from .exceptions import RelatedError
from .proto.app.proxyman.command import command_pb2, command_grpc
from .proto.common.protocol import user_pb2
from .types.account import Account
from .types.message import Message, TypedMessage


# pylint: disable=E1101

# try:
#    from .proto.core import config_pb2 as core_config_pb2
# except ModuleNotFoundError:
#    from .proto import config_pb2 as core_config_pb2


class Proxyman(XrayAPIBase):
    """Implements methods to update Xray-core users/inbounds"""

    async def __alter_inbound(self, tag: str, operation: TypedMessage) -> None:
        stub = command_grpc.HandlerServiceStub(self._channel)
        try:
            await stub.AlterInbound(
                command_pb2.AlterInboundRequest(tag=tag, operation=operation)
            )
        except grpclib.exceptions.GRPCError as error:
            raise RelatedError(error) from error

    async def add_inbound_user(self, tag: str, user: Account) -> None:
        """Adds a user to an inbound"""
        await self.__alter_inbound(
            tag=tag,
            operation=Message(
                command_pb2.AddUserOperation(
                    user=user_pb2.User(
                        level=user.level, email=user.email, account=user.message
                    )
                )
            ),
        )

    async def remove_inbound_user(self, tag: str, email: str) -> None:
        """Removes a user from an inbound"""
        await self.__alter_inbound(
            tag=tag, operation=Message(command_pb2.RemoveUserOperation(email=email))
        )

    # TODO: implement add/remove inbound/outbound if necessary
