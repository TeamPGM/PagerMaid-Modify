""" Pulls in the new version of PagerMaid from the git server. """

import platform
from datetime import datetime
from distutils.util import strtobool
from json import JSONDecodeError, loads, load
from os import remove
from os.path import exists
from subprocess import run, PIPE
from sys import executable

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError

from telethon.tl.functions.channels import GetFullChannelRequest

from pagermaid import log, config, silent, scheduler, bot, version, working_dir, logs, redis_status, redis
from pagermaid.listener import listener
from pagermaid.modules.plugin import remove_plugin, update_version, download
from pagermaid.utils import execute, lang, alias_command

try:
    git_ssh = config["git_ssh"]
    need_update_check = strtobool(config['update_check'])
except KeyError:
    git_ssh = "https://github.com/Xtao-Labs/PagerMaid-Modify.git"
    need_update_check = True


@scheduler.scheduled_job("cron", minute="*/30", id="0")
async def run_every_30_minute():
    try:
        await bot(GetFullChannelRequest("PGMUPD1"))
    except:  # noqa
        return

    need_restart = False
    async for msg in bot.iter_messages("PGMUPD1"):
        if msg.text:
            try:
                security_data = loads(msg.text.strip("`"))
            except JSONDecodeError:
                continue
            for data in security_data["data"]:
                if data["mode"] == "master":
                    if version < data["version"]:
                        logs.info(lang('update_master'))
                        await execute("git reset --hard")
                        await execute("git pull")
                        await execute(f"{executable} -m pip install -r requirements.txt --upgrade")
                        await execute(f"{executable} -m pip install -r requirements.txt")
                        need_restart = True
                        break
                elif data["mode"] == "plugins":
                    if not exists(f"{working_dir}/plugins/version.json"):
                        continue
                    with open(f"{working_dir}/plugins/version.json", 'r', encoding="utf-8") as f:
                        try:
                            version_json = load(f)
                        except JSONDecodeError:
                            continue
                    try:
                        plugin_version = version_json.get(data["name"])
                        if plugin_version is None:
                            continue
                    except AttributeError:
                        continue

                    if (float(data["version"]) - float(plugin_version)) > 0:
                        logs.info(lang('update_plugins'))
                        remove_plugin(data["name"])
                        await download(data["name"])
                        update_version(data["name"], data["version"])
                        need_restart = True

    if need_restart:
        await bot.disconnect()


@listener(is_plugin=False, outgoing=True, command=alias_command("update"),
          description=lang('update_des'),
          parameters="<true/debug>")
async def update(context):
    if len(context.parameter) > 1:
        await context.edit(lang('arg_error'))
        return
    if not silent:
        await context.edit(lang('update_processing'))
    parameter = None
    changelog = None
    if len(context.parameter) == 1:
        parameter = context.parameter[0]

    if parameter:
        if parameter == "debug":
            # Version info
            git_version = run("git --version", stdout=PIPE, shell=True).stdout.decode().strip().replace("git version ",
                                                                                                        "")
            git_change = bool(run("git diff-index HEAD --", stdout=PIPE, shell=True).stdout.decode().strip())
            git_change = "是" if git_change else "否"
            git_date = run("git log -1 --format='%at'", stdout=PIPE, shell=True).stdout.decode()
            git_date = datetime.utcfromtimestamp(int(git_date)).strftime("%Y/%m/%d %H:%M:%S")
            git_hash = run("git rev-parse --short HEAD", stdout=PIPE, shell=True).stdout.decode().strip()
            get_hash_link = f"https://github.com/Xtao-Labs/PagerMaid-Modify/commit/{git_hash}"
            # Generate the text
            text = f"{lang('status_platform')}: {str(platform.platform())}\n" \
                   f"{lang('update_platform_version')}: {str(platform.version())}\n" \
                   f"{lang('status_python')}: {str(platform.python_version())}\n" \
                   f"{lang('update_git_version')}: {git_version}\n" \
                   f"{lang('update_local_git_change')}: {git_change}\n" \
                   f"{lang('update_hash')}: [{git_hash}]({get_hash_link})\n" \
                   f"{lang('update_date')}: {git_date} "
            await context.edit(text)
            return

    try:
        repo = Repo()
    except NoSuchPathError as exception:
        await context.edit(f"{lang('update_NoSuchPathError')} {exception}")
        return
    except InvalidGitRepositoryError:
        await context.edit(lang('update_InvalidGitRepositoryError'))
        return
    except GitCommandError as exception:
        await context.edit(f'{lang("update_GitCommandError")} :`{exception}`')
        return

    active_branch = repo.active_branch.name
    if not await branch_check(active_branch):
        await context.edit(
            f"{lang('update_not_active_branch')}: {active_branch}.")
        return

    try:
        repo.create_remote('upstream', git_ssh)
    except BaseException:
        pass
    try:
        upstream_remote = repo.remote('upstream')
        upstream_remote.fetch(active_branch)
    except GitCommandError:
        await context.edit(lang('update_failed'))
        return
    try:
        changelog = await changelog_gen(repo, f'HEAD..upstream/{active_branch}')
    except:
        distribution = await execute('lsb_release -a')
        if distribution.find('Ubuntu') != -1 or distribution.find('Debain') != -1:
            try:
                await execute('apt-get install --upgrade git -y')
            except:
                await context.edit(lang('update_failed') + '\n' + lang('update_auto_upgrade_git_failed_ubuntu'))
                return
        elif distribution.find('Cent') != -1:
            try:
                await execute('yum install git -y')
            except:
                await context.edit(lang('update_failed') + '\n' + lang('update_auto_upgrade_git_failed_cent'))
                return
        else:
            try:
                await execute('apt-get install --upgrade git -y')
                await execute('yum install git -y')
            except:
                pass
        await context.edit(lang('update_auto_upgrade_git_hint'))

    if not parameter:
        if not changelog:
            await context.edit(
                f"`PagerMaid-Modify {lang('update_in_branch')} ` **{active_branch}**` {lang('update_is_updated')}`")
            return
        changelog_str = f'**{lang("update_found_update_in_branch")} {active_branch}.\n\n{lang("update_change_log")}:**\n`{changelog}`'
        if len(changelog_str) > 4096:
            await context.edit(lang('update_log_too_big'))
            file = open("output.log", "w+")
            file.write(changelog_str)
            file.close()
            await context.client.send_file(
                context.chat_id,
                "output.log",
                reply_to=context.id,
            )
            remove("output.log")
        else:
            await context.edit(changelog_str + f"\n**{lang('update_hint')}**\n`-update true`")
        return

    await context.edit(lang('update_found_pulling'))

    try:
        try:
            upstream_remote.pull(active_branch)
        except:
            await execute("""git status | grep modified | sed -r "s/ +/ /" | cut -f2 | awk -F " " '{print "mkdir -p 
            $(dirname ../for-update/" $2 ") && mv " $2 " ../for-update/" $2}' | sh""")
            await execute("git pull")
            await execute("""cd ../for-update/ && find -H . -type f | awk '{print "cp " $1 " ../PagerMaid-Modify/" 
            $1}' | sh && cd ../PagerMaid-Modify""")
            await execute("rm -rf ../for-update/")
        await execute(f"{executable} -m pip install -r requirements.txt --upgrade")
        await execute(f"{executable} -m pip install -r requirements.txt")
        await log(f"PagerMaid-Modify {lang('update_is_updated')}")
        result = await context.edit(lang('update_success') + lang('apt_reboot'))
        if redis_status():
            redis.set("restart_edit", f"{result.id}|{result.chat_id}")
        await context.client.disconnect()
    except GitCommandError:
        upstream_remote.git.reset('--hard')
        await log(lang('update_failed'))
        result = await context.edit(lang('update_failed') + lang('apt_reboot'))
        if redis_status():
            redis.set("restart_edit", f"{result.id}|{result.chat_id}")
        await context.client.disconnect()


async def changelog_gen(repo, diff):
    result = ''
    d_form = "%d/%m/%y"
    for c in repo.iter_commits(diff):
        result += f'•[{c.committed_datetime.strftime(d_form)}]: {c.summary} <{c.author}>\n'
    return result


async def branch_check(branch):
    official = ['master', 'dev']
    for k in official:
        if k == branch:
            return 1
    return
