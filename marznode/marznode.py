"""start up and run marznode"""

import logging
import os
import sys

from grpclib.health.service import Health
from grpclib.server import Server
from grpclib.utils import graceful_exit

from marznode import config
from marznode.service import MarzService
from marznode.storage import MemoryStorage
from marznode.utils.ssl import generate_keypair, create_secure_context
from marznode.utils.network import find_free_port
from marznode.backends.xray.base import XrayCore
from marznode.backends.xray.config import XrayConfig
from marznode.backends.xray.api import XrayAPI

logger = logging.getLogger(__name__)


async def main():
    """start up and run xray and the service"""
    if config.INSECURE:
        ssl_context = None
    else:
        if not all(
            (os.path.isfile(config.SSL_CERT_FILE), os.path.isfile(config.SSL_KEY_FILE))
        ):
            logger.info("Generating a keypair for Marz-node.")
            generate_keypair(config.SSL_KEY_FILE, config.SSL_CERT_FILE)

        if not os.path.isfile(config.SSL_CLIENT_CERT_FILE):
            logger.error("No certificate provided for the client; exiting.")
            sys.exit(1)
        ssl_context = create_secure_context(
            config.SSL_CERT_FILE,
            config.SSL_KEY_FILE,
            trusted=config.SSL_CLIENT_CERT_FILE,
        )

    xray_api_port = find_free_port()

    storage = MemoryStorage()
    xray_config = XrayConfig(config.XRAY_CONFIG_PATH, storage, api_port=xray_api_port)
    xray = XrayCore(config.XRAY_EXECUTABLE_PATH, config.XRAY_ASSETS_PATH)
    await xray.start(xray_config)
    xray_api = XrayAPI("127.0.0.1", xray_api_port)
    server = Server([MarzService(xray_api, storage, xray), Health()])

    with graceful_exit([server]):
        await server.start(config.SERVICE_ADDRESS, config.SERVICE_PORT, ssl=ssl_context)
        logger.info(
            "Node service running on %s:%i", config.SERVICE_ADDRESS, config.SERVICE_PORT
        )
        await server.wait_closed()
