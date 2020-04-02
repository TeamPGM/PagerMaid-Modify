""" Pagermaid plugin base. """
import json, requests
from pagermaid import bot, log
from pagermaid.listener import listener
from telethon.tl.types import MessageEntityTextUrl


@listener(outgoing=True, command="guess",
          description="能不能好好说话？ - 拼音首字母缩写释义工具 (需要回复一句话)")
async def guess(context):
    reply = await context.get_reply_message()
    await context.edit("获取中 . . .")
    if reply:
        reply_id = reply.id
    else:
        context.edit("宁需要回复一句话")
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


@listener(outgoing=True, command="ip",
          description="IPINFO (需要回复一句话)")
async def ipinfo(context):
    reply = await context.get_reply_message()
    context.edit('正在查询中...')
    try:
        url = reply.message[reply.entities[0].offset:reply.entities[0].offset + reply.entities[0].length]
    except:
        context.edit('没有找到要查询的 ip/域名 ...')
    ipinfo_json = json.loads(requests.get("http://ip-api.com/json/" + url + "?fields=status,message,country,regionName,city,lat,lon,isp,org,as,mobile,proxy,hosting,query").content.decode("utf-8"))
    if ipinfo_json['status'] == 'fail':
        context.edit('地址不正确，再试试？')
    elif ipinfo_json['status'] == 'success':
        ipinfo_list = []
        ipinfo_list.extend(["查询目标： `" + url + "`"])
        if ipinfo_json['query'] == url:
            pass
        else:
            ipinfo_list.extend(["解析地址： `" + ipinfo_json['query'] + "`"])
        ipinfo_list.extend(["地区： `" + ipinfo_json['country'] + ' - ' + ipinfo_json['regionName'] + ' - ' +
                            ipinfo_json['city'] + "`"])
        ipinfo_list.extend(["经纬度： `" + str(ipinfo_json['lat']) + ',' + str(ipinfo_json['lon']) + "`"])
        ipinfo_list.extend(["ISP： `" + ipinfo_json['isp'] + "`"])
        if not ipinfo_json['org'] == '':
            ipinfo_list.extend(["组织： `" + ipinfo_json['org'] + "`"])
        ipinfo_list.extend([ipinfo_json['as']])
        if ipinfo_json['mobile']:
            ipinfo_list.extend(['此 IP 可能为**蜂窝移动数据 IP**'])
        if ipinfo_json['proxy']:
            ipinfo_list.extend(['此 IP 可能为**代理 IP**'])
        if ipinfo_json['hosting']:
            ipinfo_list.extend(['此 IP 可能为**数据中心 IP**'])
        await context.edit('\n'.join(ipinfo_list))
