"""Defines a class to return typed message for xray api"""

# pylint: disable=E0611
from ..proto.common.serial.typed_message_pb2 import TypedMessage


class Message:
    def __new__(cls, message) -> TypedMessage:
        return TypedMessage(
            type=message.DESCRIPTOR.full_name, value=message.SerializeToString()
        )
