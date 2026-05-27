import shlex
import shutil
import subprocess
from sys import executable
from typing import Iterable, List


def package_install_command(args: Iterable[str], python: str = executable) -> List[str]:
    """Build a package install command, preferring uv when available."""
    args = list(args)
    if shutil.which("uv"):
        return ["uv", "pip", "install", "--python", python, *args]
    return [python, "-m", "pip", "install", *args]


def package_install_shell_command(args: Iterable[str], python: str = executable) -> str:
    return " ".join(shlex.quote(part) for part in package_install_command(args, python))


def install_package(args: Iterable[str], python: str = executable) -> int:
    command = package_install_command(args, python)
    try:
        subprocess.check_call(command)  # nosec B603 - command is built from a controlled allow-list
    except subprocess.CalledProcessError as exc:
        return exc.returncode or 1
    return 0
