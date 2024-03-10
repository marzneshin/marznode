# Generated by the Protocol Buffers compiler. DO NOT EDIT!
# source: marznode/service/service.proto
# plugin: grpclib.plugin.main
import abc
import typing

import grpclib.const
import grpclib.client
if typing.TYPE_CHECKING:
    import grpclib.server

import marznode.service.service_pb2


class MarzServiceBase(abc.ABC):

    @abc.abstractmethod
    async def SyncUsers(self, stream: 'grpclib.server.Stream[marznode.service.service_pb2.UserData, marznode.service.service_pb2.Empty]') -> None:
        pass

    @abc.abstractmethod
    async def RepopulateUsers(self, stream: 'grpclib.server.Stream[marznode.service.service_pb2.UsersData, marznode.service.service_pb2.Empty]') -> None:
        pass

    @abc.abstractmethod
    async def FetchInbounds(self, stream: 'grpclib.server.Stream[marznode.service.service_pb2.Empty, marznode.service.service_pb2.InboundsResponse]') -> None:
        pass

    @abc.abstractmethod
    async def FetchUsersStats(self, stream: 'grpclib.server.Stream[marznode.service.service_pb2.Empty, marznode.service.service_pb2.UsersStats]') -> None:
        pass

    @abc.abstractmethod
    async def FetchXrayConfig(self, stream: 'grpclib.server.Stream[marznode.service.service_pb2.Empty, marznode.service.service_pb2.XrayConfig]') -> None:
        pass

    @abc.abstractmethod
    async def RestartXray(self, stream: 'grpclib.server.Stream[marznode.service.service_pb2.XrayConfig, marznode.service.service_pb2.InboundsResponse]') -> None:
        pass

    @abc.abstractmethod
    async def StreamXrayLogs(self, stream: 'grpclib.server.Stream[marznode.service.service_pb2.XrayLogsRequest, marznode.service.service_pb2.LogLine]') -> None:
        pass

    def __mapping__(self) -> typing.Dict[str, grpclib.const.Handler]:
        return {
            '/marznode.MarzService/SyncUsers': grpclib.const.Handler(
                self.SyncUsers,
                grpclib.const.Cardinality.STREAM_UNARY,
                marznode.service.service_pb2.UserData,
                marznode.service.service_pb2.Empty,
            ),
            '/marznode.MarzService/RepopulateUsers': grpclib.const.Handler(
                self.RepopulateUsers,
                grpclib.const.Cardinality.UNARY_UNARY,
                marznode.service.service_pb2.UsersData,
                marznode.service.service_pb2.Empty,
            ),
            '/marznode.MarzService/FetchInbounds': grpclib.const.Handler(
                self.FetchInbounds,
                grpclib.const.Cardinality.UNARY_UNARY,
                marznode.service.service_pb2.Empty,
                marznode.service.service_pb2.InboundsResponse,
            ),
            '/marznode.MarzService/FetchUsersStats': grpclib.const.Handler(
                self.FetchUsersStats,
                grpclib.const.Cardinality.UNARY_UNARY,
                marznode.service.service_pb2.Empty,
                marznode.service.service_pb2.UsersStats,
            ),
            '/marznode.MarzService/FetchXrayConfig': grpclib.const.Handler(
                self.FetchXrayConfig,
                grpclib.const.Cardinality.UNARY_UNARY,
                marznode.service.service_pb2.Empty,
                marznode.service.service_pb2.XrayConfig,
            ),
            '/marznode.MarzService/RestartXray': grpclib.const.Handler(
                self.RestartXray,
                grpclib.const.Cardinality.UNARY_UNARY,
                marznode.service.service_pb2.XrayConfig,
                marznode.service.service_pb2.InboundsResponse,
            ),
            '/marznode.MarzService/StreamXrayLogs': grpclib.const.Handler(
                self.StreamXrayLogs,
                grpclib.const.Cardinality.UNARY_STREAM,
                marznode.service.service_pb2.XrayLogsRequest,
                marznode.service.service_pb2.LogLine,
            ),
        }


class MarzServiceStub:

    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.SyncUsers = grpclib.client.StreamUnaryMethod(
            channel,
            '/marznode.MarzService/SyncUsers',
            marznode.service.service_pb2.UserData,
            marznode.service.service_pb2.Empty,
        )
        self.RepopulateUsers = grpclib.client.UnaryUnaryMethod(
            channel,
            '/marznode.MarzService/RepopulateUsers',
            marznode.service.service_pb2.UsersData,
            marznode.service.service_pb2.Empty,
        )
        self.FetchInbounds = grpclib.client.UnaryUnaryMethod(
            channel,
            '/marznode.MarzService/FetchInbounds',
            marznode.service.service_pb2.Empty,
            marznode.service.service_pb2.InboundsResponse,
        )
        self.FetchUsersStats = grpclib.client.UnaryUnaryMethod(
            channel,
            '/marznode.MarzService/FetchUsersStats',
            marznode.service.service_pb2.Empty,
            marznode.service.service_pb2.UsersStats,
        )
        self.FetchXrayConfig = grpclib.client.UnaryUnaryMethod(
            channel,
            '/marznode.MarzService/FetchXrayConfig',
            marznode.service.service_pb2.Empty,
            marznode.service.service_pb2.XrayConfig,
        )
        self.RestartXray = grpclib.client.UnaryUnaryMethod(
            channel,
            '/marznode.MarzService/RestartXray',
            marznode.service.service_pb2.XrayConfig,
            marznode.service.service_pb2.InboundsResponse,
        )
        self.StreamXrayLogs = grpclib.client.UnaryStreamMethod(
            channel,
            '/marznode.MarzService/StreamXrayLogs',
            marznode.service.service_pb2.XrayLogsRequest,
            marznode.service.service_pb2.LogLine,
        )
