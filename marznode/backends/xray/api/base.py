"""Implements initiation method to connect to xray api address"""

import atexit
import ssl

from grpclib import client


class XrayAPIBase:
    """Base for all Xray connections"""

    def __init__(
        self, address: str, port: int, ssl_cert: str = None, ssl_target_name: str = None
    ):
        """Initializes data for creating a grpc channel"""
        self.ssl_context = None
        if ssl_cert:
            self.ssl_context = ssl.create_default_context(cadata=ssl_cert)
            self.ssl_context.check_hostname = False
        self.address = address
        self.port = port
        self._channel = client.Channel(self.address, self.port, ssl=self.ssl_context)
        atexit.register(self._channel.close)
