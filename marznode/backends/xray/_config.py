import json

import commentjson

from marznode.config import XRAY_EXECUTABLE_PATH
from ._utils import get_x25519


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
        self.inbounds_by_protocol = {}
        self.inbounds_by_tag = {}
        # self._fallbacks_inbound = self.get_inbound(XRAY_FALLBACKS_INBOUND_TAG)
        self._addr_clients_by_tag = {}
        self._resolve_inbounds()

        self._apply_api()

    def _apply_api(self):
        self["api"] = {
            "services": ["HandlerService", "StatsService", "LoggerService"],
            "tag": "API",
        }
        self["stats"] = {}
        self["policy"] = {
            "levels": {"0": {"statsUserUplink": True, "statsUserDownlink": True}},
            "system": {
                "statsInboundDownlink": False,
                "statsInboundUplink": False,
                "statsOutboundDownlink": True,
                "statsOutboundUplink": True,
            },
        }
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
                inbound["protocol"].lower()
                not in {
                    "vmess",
                    "trojan",
                    "vless",
                    "shadowsocks",
                }
                or "tag" not in inbound
            ):
                continue

            if not inbound.get("settings"):
                inbound["settings"] = {}
            if not inbound["settings"].get("clients"):
                inbound["settings"]["clients"] = []
            self._addr_clients_by_tag[inbound["tag"]] = inbound["settings"]["clients"]

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
                "is_fallback": False,
            }

            # port settings, TODO: fix port and stream settings for fallbacks

            # stream settings
            if stream := inbound.get("streamSettings"):
                net = stream.get("network", "tcp")
                net_settings = stream.get(f"{net}Settings", {})
                security = stream.get("security")
                tls_settings = stream.get(f"{security}Settings")

                settings["network"] = net

                if security == "tls":
                    settings["tls"] = "tls"
                elif security == "reality":
                    settings["fp"] = "chrome"
                    settings["tls"] = "reality"
                    settings["sni"] = tls_settings.get("serverNames", [])

                    try:
                        settings["pbk"] = tls_settings["publicKey"]
                    except KeyError:
                        pvk = tls_settings.get("privateKey")
                        if not pvk:
                            raise ValueError(
                                f"You need to provide privateKey in realitySettings of {inbound['tag']}"
                            )
                        x25519 = get_x25519(XRAY_EXECUTABLE_PATH, pvk)
                        settings["pbk"] = x25519["public_key"]

                    try:
                        settings["sid"] = tls_settings.get("shortIds")[0]
                    except (IndexError, TypeError):
                        raise ValueError(
                            f"You need to define at least one shortID in realitySettings of {inbound['tag']}"
                        )

                if net == "tcp":
                    header = net_settings.get("header", {})
                    request = header.get("request", {})
                    path = request.get("path")
                    host = request.get("headers", {}).get("Host")

                    settings["header_type"] = header.get("type")

                    if path and isinstance(path, list):
                        settings["path"] = path[0]

                    if host and isinstance(host, list):
                        settings["host"] = host

                elif net in ["ws", "httpupgrade"]:
                    settings["path"] = net_settings.get("path")
                    settings["host"] = net_settings.get("host")

                elif net == "grpc":
                    settings["path"] = net_settings.get("serviceName")

                elif net == "kcp":
                    settings["path"] = net_settings.get("seed")
                    settings["header_type"] = net_settings.get("header", {}).get("type")

                elif net == "quic":
                    settings["host"] = net_settings.get("security")
                    settings["path"] = net_settings.get("key")
                    settings["header_type"] = net_settings.get("header", {}).get("type")

                elif net == "http":
                    settings["path"] = net_settings.get("path")
                    settings["host"] = net_settings.get("host")

            self.inbounds.append(settings)
            self.inbounds_by_tag[inbound["tag"]] = settings

            try:
                self.inbounds_by_protocol[inbound["protocol"]].append(settings)
            except KeyError:
                self.inbounds_by_protocol[inbound["protocol"]] = [settings]

    def get_inbound(self, tag) -> dict:
        for inbound in self["inbounds"]:
            if inbound["tag"] == tag:
                return inbound

    def get_outbound(self, tag) -> dict:
        for outbound in self["outbounds"]:
            if outbound["tag"] == tag:
                return outbound

    def to_json(self, **json_kwargs):
        return json.dumps(self, **json_kwargs)
