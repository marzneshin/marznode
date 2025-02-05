"""loads config files from environment and env file"""

from enum import Enum

from decouple import config
from dotenv import load_dotenv

load_dotenv()

SERVICE_ADDRESS = config("SERVICE_ADDRESS", default="0.0.0.0")
SERVICE_PORT = config("SERVICE_PORT", cast=int, default=53042)
INSECURE = config("INSECURE", cast=bool, default=False)

XRAY_ENABLED = config("XRAY_ENABLED", cast=bool, default=True)
XRAY_EXECUTABLE_PATH = config("XRAY_EXECUTABLE_PATH", default="/usr/bin/xray")
XRAY_ASSETS_PATH = config("XRAY_ASSETS_PATH", default="/usr/share/xray")
XRAY_CONFIG_PATH = config("XRAY_CONFIG_PATH", default="/etc/xray/config.json")
XRAY_VLESS_REALITY_FLOW = config("XRAY_VLESS_REALITY_FLOW", default="xtls-rprx-vision")
XRAY_RESTART_ON_FAILURE = config("XRAY_RESTART_ON_FAILURE", cast=bool, default=False)
XRAY_RESTART_ON_FAILURE_INTERVAL = config(
    "XRAY_RESTART_ON_FAILURE_INTERVAL", cast=int, default=0
)

HYSTERIA_ENABLED = config("HYSTERIA_ENABLED", cast=bool, default=False)
HYSTERIA_EXECUTABLE_PATH = config(
    "HYSTERIA_EXECUTABLE_PATH", default="/usr/bin/hysteria"
)
HYSTERIA_CONFIG_PATH = config(
    "HYSTERIA_CONFIG_PATH", default="/etc/hysteria/config.yaml"
)

SING_BOX_ENABLED = config("SING_BOX_ENABLED", cast=bool, default=False)
SING_BOX_EXECUTABLE_PATH = config(
    "SING_BOX_EXECUTABLE_PATH", default="/usr/bin/sing-box"
)
SING_BOX_CONFIG_PATH = config(
    "SING_BOX_CONFIG_PATH", default="/etc/sing-box/config.json"
)
SING_BOX_RESTART_ON_FAILURE = config(
    "SING_BOX_RESTART_ON_FAILURE", cast=bool, default=False
)
SING_BOX_RESTART_ON_FAILURE_INTERVAL = config(
    "SING_BOX_RESTART_ON_FAILURE_INTERVAL", cast=int, default=0
)
SING_BOX_USER_MODIFICATION_INTERVAL = config(
    "SING_BOX_USER_MODIFICATION_INTERVAL", cast=int, default=30
)


SSL_CERT_FILE = config("SSL_CERT_FILE", default="./ssl_cert.pem")
SSL_KEY_FILE = config("SSL_KEY_FILE", default="./ssl_key.pem")
SSL_CLIENT_CERT_FILE = config("SSL_CLIENT_CERT_FILE", default="")

DEBUG = config("DEBUG", cast=bool, default=False)


class AuthAlgorithm(Enum):
    PLAIN = "plain"
    XXH128 = "xxh128"


AUTH_GENERATION_ALGORITHM = config(
    "AUTH_GENERATION_ALGORITHM", cast=AuthAlgorithm, default=AuthAlgorithm.XXH128
)
