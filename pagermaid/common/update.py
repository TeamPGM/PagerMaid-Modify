from pagermaid.utils import execute, package_install_shell_command


async def update(force: bool = False):
    await execute("git fetch --all")
    if force:
        await execute("git reset --hard origin/master")
    await execute("git pull --all")
    await execute(
        package_install_shell_command(["--upgrade", "-r", "requirements.txt"])
    )
    await execute(package_install_shell_command(["-r", "requirements.txt"]))
