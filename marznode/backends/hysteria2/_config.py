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

        self._inbound = {"tag": "hysteria2", "protocol": "hysteria2", "port": 443}

    def register_inbounds(self, storage: BaseStorage):
        inbound = self._inbound
        storage.register_inbound(
            Inbound(tag=inbound["tag"], protocol=inbound["protocol"], config=inbound)
        )

    def render(self):
        return self._config
