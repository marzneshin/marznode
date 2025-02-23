import json
from collections import defaultdict

import commentjson

from marznode.config import XRAY_EXECUTABLE_PATH, XRAY_VLESS_REALITY_FLOW, DEBUG
from ._utils import get_x25519
from ...models import Inbound
from ...storage import BaseStorage

transport_map = defaultdict(
    lambda: "tcp",
    {
        "tcp": "tcp",
        "raw": "tcp",
        "splithttp": "splithttp",
        "xhttp": "splithttp",
        "grpc": "grpc",
        "kcp": "kcp",
        "mkcp": "kcp",
        "h2": "http",
        "h3": "http",
        "http": "http",
        "ws": "ws",
        "websocket": "ws",
        "httpupgrade": "httpupgrade",
        "quic": "quic",
    },
)

forced_policies = {
  "levels": {"0": {"statsUserUplink": True, "statsUserDownlink": True}},
  "system": {
    "statsInboundDownlink": False,
    "statsInboundUplink": False,
    "statsOutboundDownlink": True,
    "statsOutboundUplink": True
  }
}

def merge_dicts(a, b): # B overrides A dict
    for key, value in b.items():
        if isinstance(value, dict) and key in a and isinstance(a[key], dict):
            merge_dicts(a[key], value)
        else:
            a[key] = value
    return a

class XrayConfig(dict):
    def __init__(
        self,
        config: str,
        api_host: str = "127.0.0.1",
        api_port: int = 8080,
    ):
        try:
            # considering string as json
            config = commentjson.loads(config)
        except (json.JSONDecodeError, ValueError):
            # considering string as file path
            with open(config) as file:
                config = commentjson.loads(file.read())

        self.api_host = api_host
        self.api_port = api_port

        super().__init__(config)

        self.inbounds = []
        self.inbounds_by_tag = {}
        # self._fallbacks_inbound = self.get_inbound(XRAY_FALLBACKS_INBOUND_TAG)
        self._resolve_inbounds()

        self._apply_api()

    def _apply_api(self):
        self["api"] = {
            "services": ["HandlerService", "StatsService", "LoggerService"],
            "tag": "API",
        }
        self["stats"] = {}
        if self.get("policy"):
            self["policy"] = merge_dicts(self.get("policy"), forced_policies)
        else:
            self["policy"] = forced_policies
        inbound = {
            "listen": self.api_host,
            "port": self.api_port,
            "protocol": "dokodemo-door",
            "settings": {"address": self.api_host},
            "tag": "API_INBOUND",
        }
        if "inbounds" not in self:
            self["inbounds"] = []
        self["inbounds"].insert(0, inbound)

        rule = {"inboundTag": ["API_INBOUND"], "outboundTag": "API", "type": "field"}

        if "routing" not in self:
            self["routing"] = {"rules": []}
        self["routing"]["rules"].insert(0, rule)

    def _resolve_inbounds(self):
        for inbound in self["inbounds"]:
            if (
                inbound.get("protocol", "").lower()
                not in {
                    "vmess",
                    "trojan",
                    "vless",
                    "shadowsocks",
                }
                or "tag" not in inbound
            ):
                continue

            settings = {
                "tag": inbound["tag"],
                "protocol": inbound["protocol"],
                "port": inbound.get("port"),
                "network": "tcp",
                "tls": "none",
                "sni": [],
                "host": [],
                "path": None,
                "header_type": None,
                "flow": None,
                "is_fallback": False,
            }

            # port settings, TODO: fix port and stream settings for fallbacks

            # stream settings
            if stream := inbound.get("streamSettings"):
                net = stream.get("network", "tcp")
                net_settings = stream.get(f"{net}Settings", {})
                security = stream.get("security")
                tls_settings = stream.get(f"{security}Settings")

                settings["network"] = transport_map[net]

                if security == "tls":
                    settings["tls"] = "tls"
                elif security == "reality":
                    settings["fp"] = "chrome"
                    settings["tls"] = "reality"
                    settings["sni"] = tls_settings.get("serverNames", [])
                    if inbound["protocol"] == "vless" and transport_map[net] == "tcp":
                        settings["flow"] = XRAY_VLESS_REALITY_FLOW

                    pvk = tls_settings.get("privateKey")

                    x25519 = get_x25519(XRAY_EXECUTABLE_PATH, pvk)
                    settings["pbk"] = x25519["public_key"]

                    settings["sid"] = tls_settings.get("shortIds", [""])[0]

                if net in ["tcp", "raw"]:
                    header = net_settings.get("header", {})
                    request = header.get("request", {})
                    path = request.get("path")
                    host = request.get("headers", {}).get("Host")

                    settings["header_type"] = header.get("type")

                    if path and isinstance(path, list):
                        settings["path"] = path[0]

                    if host and isinstance(host, list):
                        settings["host"] = host

                elif net in ["ws", "websocket", "httpupgrade", "splithttp", "xhttp"]:
                    settings["path"] = net_settings.get("path")
                    settings["host"] = net_settings.get("host")

                elif net == "grpc":
                    settings["path"] = net_settings.get("serviceName")

                elif net in ["kcp", "mkcp"]:
                    settings["path"] = net_settings.get("seed")
                    settings["header_type"] = net_settings.get("header", {}).get("type")

                elif net == "quic":
                    settings["host"] = net_settings.get("security")
                    settings["path"] = net_settings.get("key")
                    settings["header_type"] = net_settings.get("header", {}).get("type")

                elif net == "http":
                    settings["path"] = net_settings.get("path")
                    settings["host"] = net_settings.get("host")

            if inbound["protocol"] == "shadowsocks":
                settings["network"] = None

            self.inbounds.append(settings)
            self.inbounds_by_tag[inbound["tag"]] = settings

    def register_inbounds(self, storage: BaseStorage):
        for inbound in self.list_inbounds():
            storage.register_inbound(inbound)

    def list_inbounds(self) -> list[Inbound]:
        return [
            Inbound(tag=i["tag"], protocol=i["protocol"], config=i)
            for i in self.inbounds_by_tag.values()
        ]

    def to_json(self, **json_kwargs):
        if DEBUG:
            with open('xray_config_debug.json', 'w') as f:
                f.write(json.dumps(self, indent=4))
        return json.dumps(self, **json_kwargs)
