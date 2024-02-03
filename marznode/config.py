"""loads config files from environment and env file"""
from decouple import config
from dotenv import load_dotenv

load_dotenv()

SERVICE_ADDRESS = config("SERVICE_ADDRESS", default="0.0.0.0")
SERVICE_PORT = config("SERVICE_PORT", cast=int, default=62050)

XRAY_EXECUTABLE_PATH = config("XRAY_EXECUTABLE_PATH", default="/usr/bin/xray")
XRAY_ASSETS_PATH = config("XRAY_ASSETS_PATH", default="/usr/share/xray")
XRAY_CONFIG_PATH = config("XRAY_CONFIG_PATH", default="/etc/xray/config.json")

SSL_CERT_FILE = config("SSL_CERT_FILE", default="/etc/marzneshin/ssl_cert.pem")
SSL_KEY_FILE = config("SSL_KEY_FILE", default="/etc/marzneshin/ssl_key.pem")
SSL_CLIENT_CERT_FILE = config("SSL_CLIENT_CERT_FILE", default="")

DEBUG = config("DEBUG", cast=bool, default=False)
