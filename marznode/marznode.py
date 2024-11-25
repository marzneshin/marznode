"""start up and run marznode"""

import logging
import os
import sys

from grpclib.health.service import Health
from grpclib.server import Server
from grpclib.utils import graceful_exit

from marznode import config
from marznode.backends.hysteria2.hysteria2_backend import HysteriaBackend
from marznode.backends.singbox.singbox_backend import SingBoxBackend
from marznode.backends.xray.xray_backend import XrayBackend
from marznode.config import (
    HYSTERIA_EXECUTABLE_PATH,
    HYSTERIA_CONFIG_PATH,
    XRAY_CONFIG_PATH,
    HYSTERIA_ENABLED,
    XRAY_ENABLED,
    XRAY_EXECUTABLE_PATH,
    XRAY_ASSETS_PATH,
    SING_BOX_ENABLED,
    SING_BOX_EXECUTABLE_PATH,
    SING_BOX_CONFIG_PATH,
)
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
            logger.info("Generating a keypair for Marznode.")
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
    backends = dict()
    if XRAY_ENABLED:
        xray_backend = XrayBackend(
            XRAY_EXECUTABLE_PATH,
            XRAY_ASSETS_PATH,
            XRAY_CONFIG_PATH,
            storage,
        )
        await xray_backend.start()
        backends.update({"xray": xray_backend})
    if HYSTERIA_ENABLED:
        hysteria_backend = HysteriaBackend(
            HYSTERIA_EXECUTABLE_PATH, HYSTERIA_CONFIG_PATH, storage
        )
        await hysteria_backend.start()
        backends.update({"hysteria2": hysteria_backend})
    if SING_BOX_ENABLED:
        sing_box_backend = SingBoxBackend(
            SING_BOX_EXECUTABLE_PATH, SING_BOX_CONFIG_PATH, storage
        )
        await sing_box_backend.start()
        backends.update({"sing-box": sing_box_backend})

    server = Server([MarzService(storage, backends), Health()])

    with graceful_exit([server]):
        await server.start(config.SERVICE_ADDRESS, config.SERVICE_PORT, ssl=ssl_context)
        logger.info(
            "Node service running on %s:%i", config.SERVICE_ADDRESS, config.SERVICE_PORT
        )
        await server.wait_closed()
