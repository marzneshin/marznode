"""Construct types and a class for getting statistics from Xray-core"""

# pylint: disable=E1101
from dataclasses import dataclass

import grpclib

from .base import XrayAPIBase
from .exceptions import RelatedError
from .proto.app.stats.command import command_pb2, command_grpc


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


class Stats(XrayAPIBase):
    """Xray-core stat commands"""

    # TODO: refactor and remove duplicate methods using an string enum class for pattern
    async def get_sys_stats(self) -> SysStatsResponse:
        """Get System stats from Xray-core"""
        try:
            stub = command_grpc.StatsServiceStub(self._channel)
            response = await stub.GetSysStats(command_pb2.SysStatsRequest())

        except grpclib.exceptions.GRPCError as error:
            raise RelatedError(error) from error

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
        """Get statistics from Xray-core

        Args:
            pattern: the pattern given directly to xray e.g. `user>>>`
            reset: whether to reset xray statistics or not."""
        try:
            stub = command_grpc.StatsServiceStub(self._channel)
            response = await stub.QueryStats(
                command_pb2.QueryStatsRequest(pattern=pattern, reset=reset)
            )

        except grpclib.exceptions.GRPCError as error:
            raise RelatedError(error) from error
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
