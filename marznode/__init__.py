"""Initiate logger for marznode"""

import logging

from marznode import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if config.DEBUG else logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
