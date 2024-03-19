from pydantic import BaseModel


class Protocol(BaseModel):
    name: str


class Inbound(BaseModel):
    tag: str
    protocol: str
