"""start up and run marznode"""

import logging
import os
import sys

from grpclib.health.service import Health
from grpclib.server import Server
from grpclib.utils import graceful_exit

from marznode import config
from marznode.backends.hysteria2.interface import HysteriaBackend
from marznode.backends.xray.interface import XrayBackend
from marznode.service import MarzService
from marznode.storage import MemoryStorage
from marznode.utils.ssl import generate_keypair, create_secure_context

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

    storage = MemoryStorage()
    xray_backend = XrayBackend(storage)
    hysteria_backend = HysteriaBackend("./hysteria.yaml")
    await hysteria_backend.start()
    await xray_backend.start()
    backends = [xray_backend]
    server = Server([MarzService(storage, backends), Health()])

    with graceful_exit([server]):
        await server.start(config.SERVICE_ADDRESS, config.SERVICE_PORT, ssl=ssl_context)
        logger.info(
            "Node service running on %s:%i", config.SERVICE_ADDRESS, config.SERVICE_PORT
        )
        await server.wait_closed()
