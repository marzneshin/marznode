"""Implements accounts for different protocols in Xray-core"""

# pylint: disable=E0611,C0115
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator, ValidationInfo, ValidationError, Field

from .message import Message
from ..proto.common.serial.typed_message_pb2 import TypedMessage
from ..proto.proxy.shadowsocks.config_pb2 import Account as ShadowsocksAccountPb2

# from ..proto.proxy.shadowsocks.config_pb2 import \
#    CipherType as ShadowsocksCiphers
from ..proto.proxy.trojan.config_pb2 import Account as TrojanAccountPb2
from ..proto.proxy.vless.account_pb2 import Account as VLESSAccountPb2
from ..proto.proxy.vmess.account_pb2 import Account as VMessAccountPb2
from marznode.utils.key_gen import generate_uuid, generate_password


class Account(BaseModel, ABC):
    email: str
    seed: Optional[str] = None
    level: int = 0

    @property
    @abstractmethod
    def message(self) -> TypedMessage:
        pass

    @field_validator("id", "password", check_fields=False)
    @classmethod
    def generate_creds(cls, v: str, info: ValidationInfo):
        if v:
            return v
        if "seed" in info.data:
            seed = info.data["seed"]
            if info.field_name == "id":
                return generate_uuid(seed)
            elif info.field_name == "password":
                return generate_password(seed)
        raise ValidationError("Both password/id and seed are empty")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.email}>"


class VMessAccount(Account):
    id: Optional[UUID] = Field(None, validate_default=True)

    @property
    def message(self):
        return Message(VMessAccountPb2(id=str(self.id)))


class XTLSFlows(str, Enum):
    NONE = ""
    VISION = "xtls-rprx-vision"


class VLESSAccount(Account):
    id: Optional[UUID] = Field(None, validate_default=True)
    flow: XTLSFlows = XTLSFlows.NONE

    @property
    def message(self):
        return Message(VLESSAccountPb2(id=str(self.id), flow=self.flow.value))


class TrojanAccount(Account):
    password: Optional[str] = Field(None, validate_default=True)

    @property
    def message(self):
        return Message(TrojanAccountPb2(password=self.password))


class ShadowsocksMethods(str, Enum):
    AES_128_GCM = "aes-128-gcm"
    AES_256_GCM = "aes-256-gcm"
    CHACHA20_POLY1305 = "chacha20-ietf-poly1305"


class ShadowsocksAccount(Account):
    password: Optional[str] = Field(None, validate_default=True)
    method: ShadowsocksMethods = ShadowsocksMethods.CHACHA20_POLY1305

    @property
    def cipher_type(self):
        return self.method.name

    @property
    def message(self):
        return Message(
            ShadowsocksAccountPb2(password=self.password, cipher_type=self.cipher_type)
        )


accounts_map = {
    "shadowsocks": ShadowsocksAccount,
    "trojan": TrojanAccount,
    "vmess": VMessAccount,
    "vless": VLESSAccount,
}
