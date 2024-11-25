import atexit
from dataclasses import dataclass

from grpclib import client

from .sb_stats_grpc import StatsServiceStub
from .sb_stats_pb2 import SysStatsRequest, QueryStatsRequest


@dataclass
class SysStatsResponse:
    """Stores system statistics"""

    num_goroutine: int
    num_gc: int
    alloc: int
    total_alloc: int
    sys: int
    mallocs: int
    frees: int
    live_objects: int
    pause_total_ns: int
    uptime: int


@dataclass
class StatResponse:
    """Stores xray statistics"""

    name: str
    type: str
    link: str
    value: int


@dataclass
class UserStatsResponse:
    """Stores statistics of a user"""

    email: str
    uplink: int
    downlink: int


@dataclass
class InboundStatsResponse:
    """Stores statistics of an inbound"""

    tag: str
    uplink: int
    downlink: int


@dataclass
class OutboundStatsResponse:
    """Stores statistics of an outbound"""

    tag: str
    uplink: int
    downlink: int


class SingBoxAPIBase:
    """Base for sb api connections"""

    def __init__(self, address: str, port: int):
        """Initializes data for creating a grpc channel"""
        self.address = address
        self.port = port
        self._channel = client.Channel(self.address, self.port)
        atexit.register(self._channel.close)


class SingBoxAPI(SingBoxAPIBase):
    """Sing-box stat commands"""

    # TODO: refactor and remove duplicate methods using an string enum class for pattern
    async def get_sys_stats(self) -> SysStatsResponse:
        """Get System stats from Xray-core"""
        stub = StatsServiceStub(self._channel)
        response = await stub.GetSysStats(SysStatsRequest())

        return SysStatsResponse(
            num_goroutine=response.NumGoroutine,
            num_gc=response.NumGC,
            alloc=response.Alloc,
            total_alloc=response.TotalAlloc,
            sys=response.Sys,
            mallocs=response.Mallocs,
            frees=response.Frees,
            live_objects=response.LiveObjects,
            pause_total_ns=response.PauseTotalNs,
            uptime=response.Uptime,
        )

    async def __query_stats(
        self, pattern: str, reset: bool = False
    ) -> list[StatResponse]:
        """Get statistics from sing-box

        Args:
            pattern: the pattern given directly to sing-box e.g. `user>>>`
            reset: whether to reset sing-box statistics or not."""
        stub = StatsServiceStub(self._channel)
        response = await stub.QueryStats(
            QueryStatsRequest(pattern=pattern, reset=reset)
        )
        results = []
        for stat in response.stat:
            type_, name, _, link = stat.name.split(">>>")
            results.append(StatResponse(name, type_, link, stat.value))
        return results

    async def get_users_stats(self, reset: bool = False) -> list[StatResponse]:
        """returns statistics of all users"""
        return await self.__query_stats("user>>>", reset=reset)

    async def get_inbounds_stats(self, reset: bool = False) -> list[StatResponse]:
        """returns statistics of all inbounds"""
        return await self.__query_stats("inbound>>>", reset=reset)

    async def get_outbounds_stats(self, reset: bool = False) -> list[StatResponse]:
        """returns statistics of all outbounds"""
        return await self.__query_stats("outbound>>>", reset=reset)

    async def get_user_stats(
        self, email: str, reset: bool = False
    ) -> UserStatsResponse:
        """returns statistics of a specific user"""
        uplink, downlink = 0, 0
        for stat in await self.__query_stats(f"user>>>{email}>>>", reset=reset):
            if stat.link == "uplink":
                uplink = stat.value
            elif stat.link == "downlink":
                downlink = stat.value

        return UserStatsResponse(email=email, uplink=uplink, downlink=downlink)

    async def get_inbound_stats(
        self, tag: str, reset: bool = False
    ) -> InboundStatsResponse:
        """returns statistics of an inbound"""
        uplink, downlink = 0, 0
        for stat in await self.__query_stats(f"inbound>>>{tag}>>>", reset=reset):
            if stat.link == "uplink":
                uplink = stat.value
            elif stat.link == "downlink":
                downlink = stat.value
        return InboundStatsResponse(tag=tag, uplink=uplink, downlink=downlink)

    async def get_outbound_stats(
        self, tag: str, reset: bool = False
    ) -> OutboundStatsResponse:
        """returns statistics of an outbound"""
        uplink, downlink = 0, 0
        for stat in await self.__query_stats(f"outbound>>>{tag}>>>", reset=reset):
            if stat.link == "uplink":
                uplink = stat.value
            elif stat.link == "downlink":
                downlink = stat.value
        return OutboundStatsResponse(tag=tag, uplink=uplink, downlink=downlink)
