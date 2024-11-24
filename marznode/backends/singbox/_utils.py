import re
import subprocess


def get_version(sing_box_path: str) -> str | None:
    """
    get sing-box version by running its executable
    :param sing_box_path:
    :return: xray version
    """
    cmd = [sing_box_path, "version"]
    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
    match = re.match(r"^sing-box version (\d+\.\d+\.\d+)", output)
    if match:
        return match.group(1)
    return None
