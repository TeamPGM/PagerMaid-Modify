""" Pagermaid plugin base. """

from os import remove
from os.path import exists
from youtube_dl import YoutubeDL
from re import compile as regex_compile
from pagermaid import bot, log
from pagermaid.listener import listener


@listener(outgoing=True, command="ytdl",
          description="YouTube downloader.",
          parameters="<url>.")
async def ytdl(context):
    url = context.arguments
    reply = await context.get_reply_message()
    reply_id = None
    await context.edit("正在拉取视频 . . .")
    if reply:
        reply_id = reply.id
    if url is None:
        await context.edit("出错了呜呜呜 ~ 无效的参数。")
        return

    youtube_pattern = regex_compile(r"^(http(s)?://)?((w){3}.)?youtu(be|.be)?(\.com)?/.+")
    if youtube_pattern.match(url):
        if not await fetch_youtube_video(url, context.chat_id, reply_id):
            await context.edit("出错了呜呜呜 ~ 视频下载失败。")
        await log(f"已拉取UTB视频，地址： {url}.")


async def fetch_youtube_video(url, chat_id, reply_id):
    """ Extracts and uploads YouTube video. """
    youtube_dl_options = {
        'format': 'bestvideo[height=720]+bestaudio/best',
        'outtmpl': "video.%(ext)s",
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4'
        }]
    }
    YoutubeDL(youtube_dl_options).download([url])
    if not exists("video.mp4"):
        return False
    await bot.send_file(
         chat_id,
         "video.mp4",
         reply_to=reply_id
    )
    remove("video.mp4")
    return True
