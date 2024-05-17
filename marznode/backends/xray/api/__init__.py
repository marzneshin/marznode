"""Implementation of xray's API to alter xray users/inbounds"""

from . import exceptions
from . import exceptions as exc
from . import types
from .proxyman import Proxyman
from .stats import Stats


class XrayAPI(Proxyman, Stats):
    """XRay api methods, containing both stats and proxyman commands"""


__all__ = ["XrayAPI", "exceptions", "exc", "types"]
