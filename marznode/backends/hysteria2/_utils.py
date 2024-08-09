import re
import subprocess


def get_version(hysteria_path: str) -> str | None:
    """
    get xray version by running its executable
    :param hysteria_path:
    :return: xray version
    """
    cmd = [hysteria_path, "version"]
    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
    pattern = r"Version:\s*v(\d+\.\d+\.\d+)"
    match = re.search(pattern, output)
    if match:
        return match.group(1)
    else:
        return None
