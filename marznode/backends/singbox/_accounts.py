"""Implements accounts for different protocols in sing-box"""

# pylint: disable=E0611,C0115
from abc import ABC
from enum import Enum
from typing import Optional

from pydantic import (
    BaseModel,
    field_validator,
    ValidationInfo,
    ValidationError,
    computed_field,
    Field,
)

from marznode.utils.key_gen import generate_password, generate_uuid


class SingBoxAccount(BaseModel, ABC):
    identifier: str
    seed: str

    @field_validator("uuid", "password", check_fields=False)
    @classmethod
    def generate_creds(cls, v: str, info: ValidationInfo):
        if v:
            return v
        if "seed" in info.data:
            seed = info.data["seed"]
            if info.field_name == "uuid":
                return str(generate_uuid(seed))
            elif info.field_name == "password":
                return generate_password(seed)
        raise ValidationError("Both password/id and seed are empty")

    def to_dict(self):
        return self.model_dump(exclude={"seed", "identifier"})

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.email}>"


class NamedAccount(SingBoxAccount):
    @computed_field
    @property
    def name(self) -> str:
        return self.identifier


class UserNamedAccount(SingBoxAccount):
    @computed_field
    @property
    def username(self) -> str:
        return self.identifier


class VMessAccount(NamedAccount, SingBoxAccount):
    uuid: Optional[str] = Field(None, validate_default=True)


class XTLSFlows(str, Enum):
    NONE = ""
    VISION = "xtls-rprx-vision"


class VLESSAccount(NamedAccount, SingBoxAccount):
    uuid: Optional[str] = Field(None, validate_default=True)
    flow: XTLSFlows = XTLSFlows.NONE


class TrojanAccount(NamedAccount, SingBoxAccount):
    password: Optional[str] = Field(None, validate_default=True)


class ShadowsocksAccount(NamedAccount, SingBoxAccount):
    password: Optional[str] = Field(None, validate_default=True)


class TUICAccount(NamedAccount, SingBoxAccount):
    uuid: Optional[str] = Field(None, validate_default=True)
    password: Optional[str] = Field(None, validate_default=True)


class Hysteria2Account(NamedAccount, SingBoxAccount):
    password: Optional[str] = Field(None, validate_default=True)


class NaiveAccount(UserNamedAccount, SingBoxAccount):
    password: Optional[str] = Field(None, validate_default=True)


class ShadowTLSAccount(NamedAccount, SingBoxAccount):
    password: Optional[str] = Field(None, validate_default=True)


class SocksAccount(UserNamedAccount, SingBoxAccount):
    password: Optional[str] = Field(None, validate_default=True)


class HTTPAccount(UserNamedAccount, SingBoxAccount):
    password: Optional[str] = Field(None, validate_default=True)


class MixedAccount(UserNamedAccount, SingBoxAccount):
    password: Optional[str] = Field(None, validate_default=True)


accounts_map = {
    "shadowsocks": ShadowsocksAccount,
    "trojan": TrojanAccount,
    "vmess": VMessAccount,
    "vless": VLESSAccount,
    "shadowtls": ShadowTLSAccount,
    "tuic": TUICAccount,
    "hysteria2": Hysteria2Account,
    "naive": NaiveAccount,
    "socks": SocksAccount,
    "mixed": MixedAccount,
    "http": HTTPAccount,
}
