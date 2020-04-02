""" Pagermaid plugin base. """
import json, requests
from pagermaid import bot, log
from pagermaid.listener import listener


@listener(outgoing=True, command="guess",
          description="能不能好好说话？ - 拼音首字母缩写释义工具 (需要回复一句话)")
async def guess(context):
    reply = await context.get_reply_message()
    await context.edit("获取中 . . .")
    if reply:
        reply_id = reply.id
    else:
        return True
    text = {'text': str(reply.message.replace("/guess ", "").replace(" ", ""))}
    guess_json = json.loads(
        requests.post("https://lab.magiconch.com/api/nbnhhsh/guess", data=text, verify=False).content.decode("utf-8"))
    guess_res = []
    if not len(guess_json) == 0:
        for num in range(0, len(guess_json)):
            guess_res1 = json.loads(json.dumps(guess_json[num]))
            guess_res1_name = guess_res1['name']
            try:
                guess_res1_ans = ", ".join(guess_res1['trans'])
            except:
                try:
                    guess_res1_ans = ", ".join(guess_res1['inputting'])
                except:
                    guess_res1_ans = "尚未录入"
            guess_res.extend(["词组：" + guess_res1_name + "\n释义：" + guess_res1_ans])
        await context.edit("\n\n".join(guess_res))
    else:
        await context.edit("没有匹配到拼音首字母缩写")
