import yaml

from marznode.models import Inbound
from marznode.storage import BaseStorage


class HysteriaConfig:
    def __init__(
        self,
        config: str,
        api_port: int = 9090,
        stats_port: int = 9999,
        stats_secret: str = "pretty_secret",
    ):
        loaded_config = yaml.safe_load(config)
        loaded_config["auth"] = {
            "type": "http",
            "http": {"url": "http://127.0.0.1:" + str(api_port)},
        }
        loaded_config["trafficStats"] = {
            "listen": "127.0.0.1:" + str(stats_port),
            "secret": stats_secret,
        }
        self._config = loaded_config

        port = 443
        if "listen" in loaded_config:
            try:
                port = int(loaded_config.get("listen").split(":")[-1])
            except ValueError:
                pass
        obfs_type, obfs_password = None, None

        if "obfs" in loaded_config:
            try:
                obfs_type = loaded_config["obfs"]["type"]
                obfs_password = loaded_config["obfs"][obfs_type]["password"]
            except:
                pass

        self._inbound = {
            "tag": "hysteria2",
            "protocol": "hysteria2",
            "port": port,
            "tls": "tls",
        }
        if obfs_type and obfs_password:
            self._inbound.update({"path": obfs_password, "header_type": obfs_type})

    def register_inbounds(self, storage: BaseStorage):
        storage.register_inbound(self.get_inbound())

    def get_inbound(self):
        return Inbound(
            tag=self._inbound["tag"],
            protocol=self._inbound["protocol"],
            config=self._inbound,
        )

    def render(self):
        return self._config
