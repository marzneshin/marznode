import json

import commentjson

from marznode.backends.singbox._accounts import accounts_map
from marznode.backends.xray._utils import get_x25519
from marznode.config import XRAY_EXECUTABLE_PATH
from marznode.models import User, Inbound
from marznode.storage import BaseStorage


class SingBoxConfig(dict):
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
        self._resolve_inbounds()

        self._apply_api()

    def _apply_api(self):
        if not self.get("experimental"):
            self["experimental"] = {}
        self["experimental"]["v2ray_api"] = {
            "listen": self.api_host + ":" + str(self.api_port),
            "stats": {"enabled": True, "users": []},
        }

    def _resolve_inbounds(self):
        for inbound in self.get("inbounds", []):
            if inbound.get("type") not in {
                "shadowsocks",
                "vmess",
                "trojan",
                "vless",
                "hysteria2",
                "tuic",
                "shadowtls",
            } or not inbound.get("tag"):
                continue

            settings = {
                "tag": inbound["tag"],
                "protocol": inbound["type"],
                "port": inbound.get("listen_port"),
                "network": None,
                "tls": "none",
                "sni": [],
                "host": [],
                "path": None,
                "header_type": None,
                "flow": None,
            }

            if "tls" in inbound and inbound["tls"].get("enabled") == True:
                settings["tls"] = "tls"
                if sni := inbound["tls"].get("server_name"):
                    settings["sni"].append(sni)
                if inbound["tls"].get("reality", {}).get("enabled"):
                    settings["tls"] = "reality"
                    pvk = inbound["tls"]["reality"].get("private_key")

                    x25519 = get_x25519(XRAY_EXECUTABLE_PATH, pvk)
                    settings["pbk"] = x25519["public_key"]

                    settings["sid"] = inbound["tls"]["reality"].get("short_id", [""])[0]

            if "transport" in inbound:
                settings["network"] = inbound["transport"].get("type")
                if settings["network"] == "ws":
                    settings["path"] = inbound["transport"].get("path")
                elif settings["network"] == "http":
                    settings["path"] = inbound["transport"].get("path")
                    settings["network"] = "tcp"
                    settings["header_type"] = "http"
                    settings["host"] = inbound["transport"].get("host", [])
                elif settings["network"] == "grpc":
                    settings["path"] = inbound["transport"].get("service_name")
                elif settings["network"] == "httpupgrade":
                    settings["path"] = inbound["transport"].get("path")

            if inbound["type"] == "shadowtls" and "version" in inbound:
                settings["shadowtls_version"] = inbound["version"]
            elif inbound["type"] == "hysteria2" and "obfs" in inbound:
                try:
                    settings["header_type"], settings["path"] = (
                        inbound["obfs"]["type"],
                        inbound["obfs"]["password"],
                    )
                except KeyError:
                    pass

            self.inbounds.append(settings)
            self.inbounds_by_tag[inbound["tag"]] = settings

    def append_user(self, user: User, inbound: Inbound):
        identifier = str(user.id) + "." + user.username
        account = accounts_map[inbound.protocol](identifier=identifier, seed=user.key)
        for i in self.get("inbounds", []):
            if i.get("tag") == inbound.tag:
                if not i.get("users"):
                    i["users"] = []
                i["users"].append(account.to_dict())
                if (
                    identifier
                    not in self["experimental"]["v2ray_api"]["stats"]["users"]
                ):
                    self["experimental"]["v2ray_api"]["stats"]["users"].append(
                        identifier
                    )
                break

    def pop_user(self, user: User, inbound: Inbound):
        identifier = str(user.id) + "." + user.username
        for i in self.get("inbounds", []):
            if i.get("tag") != inbound.tag or not i.get("users"):
                continue
            i["users"] = [
                user
                for user in i["users"]
                if user.get("name") != identifier and user.get("username") != identifier
            ]
            break

    def register_inbounds(self, storage: BaseStorage):
        for inbound in self.list_inbounds():
            storage.register_inbound(inbound)

    def list_inbounds(self) -> list[Inbound]:
        return [
            Inbound(tag=i["tag"], protocol=i["protocol"], config=i)
            for i in self.inbounds_by_tag.values()
        ]

    def to_json(self, **json_kwargs):
        return json.dumps(self, **json_kwargs)
