""" Message related utilities. """

from telethon.tl.functions.messages import DeleteChatUserRequest
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.errors.rpcerrorlist import ChatIdInvalidError
from distutils2.util import strtobool
from pagermaid import bot, log, config
from pagermaid.listener import listener


@listener(outgoing=True, command="userid",
          description="查询您回复消息的发送者的用户ID。")
async def userid(context):
    """ Query the UserID of the sender of the message you replied to. """
    message = await context.get_reply_message()
    if message:
        if not message.forward:
            user_id = message.sender.id
            if message.sender.username:
                target = "@" + message.sender.username
            else:
                try:
                    target = "**" + message.sender.first_name + "**"
                except TypeError:
                    target = "**" + "死号" + "**"

        else:
            user_id = message.forward.sender.id
            if message.forward.sender.username:
                target = "@" + message.forward.sender.username
            else:
                target = "*" + message.forward.sender.first_name + "*"
        await context.edit(
            f"**道纹:** {target} \n"
            f"**用户ID:** `{user_id}`"
        )
    else:
        await context.edit("出错了呜呜呜 ~ 无法获取目标消息的信息。")


@listener(outgoing=True, command="chatid",
          description="查询当前会话的 chatid 。")
async def chatid(context):
    """ Queries the chatid of the chat you are in. """
    await context.edit("ChatID: `" + str(context.chat_id) + "`")


@listener(outgoing=True, command="log",
          description="转发一条消息到日志。",
          parameters="<string>")
async def log(context):
    """ Forwards a message into log group """
    if strtobool(config['log']):
        if context.reply_to_msg_id:
            reply_msg = await context.get_reply_message()
            await reply_msg.forward_to(int(config['log_chatid']))
        elif context.arguments:
            await log(context.arguments)
        else:
            await context.edit("出错了呜呜呜 ~ 无效的参数。")
            return
        await context.edit("已记录。")
    else:
        await context.edit("出错了呜呜呜 ~ 日志记录已禁用。")


@listener(outgoing=True, command="leave",
          description="说 再见 然后离开会话。")
async def leave(context):
    """ It leaves you from the group. """
    if context.is_group:
        await context.edit("贵群真是浪费我的时间，再见。")
        try:
            await bot(DeleteChatUserRequest(chat_id=context.chat_id,
                                            user_id=context.sender_id
                                            ))
        except ChatIdInvalidError:
            await bot(LeaveChannelRequest(chatid))
    else:
        await context.edit("出错了呜呜呜 ~ 当前聊天不是群聊。")


@listener(outgoing=True, command="meter2feet",
          description="将米转换为英尺。",
          parameters="<meters>")
async def meter2feet(context):
    """ Convert meter to feet. """
    if not len(context.parameter) == 1:
        await context.edit("出错了呜呜呜 ~ 无效的参数。")
        return
    meter = float(context.parameter[0])
    feet = meter / .3048
    await context.edit(f"将 {str(meter)} 米装换为了 {str(feet)} 英尺。")


@listener(outgoing=True, command="feet2meter",
          description="将英尺转换为米。",
          parameters="<feet>")
async def feet2meter(context):
    """ Convert feet to meter. """
    if not len(context.parameter) == 1:
        await context.edit("出错了呜呜呜 ~ 无效的参数。")
        return
    feet = float(context.parameter[0])
    meter = feet * .3048
    await context.edit(f"将 {str(feet)} 英尺转换为了 {str(meter)} 米。")


@listener(outgoing=True, command="source",
          description="显示原始 PagerMaid git 存储库的URL。")
async def source(context):
    """ Outputs the git repository URL. """
    await context.edit("https://git.stykers.moe/scm/~stykers/pagermaid.git")


@listener(outgoing=True, command="site",
          description="显示原始 PagerMaid 项目主页的URL。")
async def site(context):
    """ Outputs the site URL. """
    await context.edit("https://katonkeyboard.moe/pagermaid.html")

@listener(outgoing=True, command="sources",
          description="显示 PagerMaid-Modify 存储库的URL。")
async def sources(context):
    """ Outputs the repository URL. """
    await context.edit("https://github.com/xtaodada/PagerMaid-Modify/")