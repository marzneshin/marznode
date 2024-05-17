from pydantic import BaseModel


class Inbound(BaseModel):
    tag: str
    protocol: str
    config: dict
