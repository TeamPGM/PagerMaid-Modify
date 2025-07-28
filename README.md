![pagermaid](pagermaid/assets/logo.jpg "pagermaid")

<h1 align="center"><a href="https://t.me/PagerMaid_Modify" target="_blank">PagerMaid</a></h1>

<div align="center">

一个人形自走 bot

<img alt="star" src="https://img.shields.io/github/stars/TeamPGM/PagerMaid-Modify.svg"/>
<img alt="fork" src="https://img.shields.io/github/forks/TeamPGM/PagerMaid-Modify.svg"/>
<img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/TeamPGM/PagerMaid-Modify.svg?label=commits">
<img alt="size" src="https://img.shields.io/github/repo-size/TeamPGM/PagerMaid-Modify?color=pink"/>
<img alt="issues" src="https://img.shields.io/github/issues/TeamPGM/PagerMaid-Modify.svg"/>
<img alt="docker" src="https://img.shields.io/docker/pulls/mrwangzhe/pagermaid_modify"/>
<a href="https://github.com/TeamPGM/PagerMaid-Modify/blob/master/LICENSE"><img alt="license" src="https://img.shields.io/github/license/TeamPGM/PagerMaid-Modify.svg"/></a>
<img alt="telethon" src="https://img.shields.io/badge/telethon-blue.svg"/>

</div>

## 简介

Pagermaid 是一个用在 Telegram 的实用工具。

它通过响应账号通过其他客户端发出的命令来自动执行一系列任务。

更新频道：https://t.me/PagerMaid_Modify

## 安装

[Ubuntu 16.04 手动搭建教程](https://github.com/TeamPGM/PagerMaid-Modify/wiki/Ubuntu-16.04-%E5%AE%89%E8%A3%85%E8%AF%A6%E8%A7%A3)

[一键脚本](https://t.me/PagerMaid_Modify/58)

[Docker安装](utils/docker.md)

# Session

> 这是您账户的授权文件，请妥善保管

获得 `API_ID` 和 `API_HASH` 后，你可以通过下面两种方式获取 `SESSION`：

* 在线获取：[![Repl.it](https://replit.com/badge/github/TeamPGM/PagerMaid-Modify)](https://replit.com/@mrwangzhe/gensession)
* 本地获取：`cd utils && python3 -m pip install telethon && python3 gensession.py`

# 对存在使用本项目用户群组的提醒

由于本项目需要响应账号通过其他客户端发出的命令，所以在本项目正常运行时，可能使用下列信息：

- 用户信息
  - 姓
  - 名
  - 简介
  - 头像以及历史头像
  - 用户名
  - 用户id
  - 共同群组
  - 官方认证状态
  - 受限制状态
  - 用户类型
- 群组信息
  - 标题
  - 群组类型
  - 群组id
  - 回复消息id
  - 用户名
- 频道信息
  - 标题
  - 用户名
  - 频道id
  - 消息id
  - 消息发送者（如果有的话）
- 文本
- 文件
- 图片
- 贴纸

以及会污染群组的操作记录，请群主或管理员提前声明禁止使用。如提醒不听，本项目组也没有办法，谁让这代码是开源的呢（

# 隐私政策

您在使用本项目代码时即表示您已经同意本隐私协议并且允许我们以评估负载和修复代码的目的记录您 bot 的在线状态和报错文件。

除可能使用的信息之外，我们不会记录与收集任何信息。

本项目代码完全遵循此隐私政策，您可以随时在此项目中审查我们的源代码。

# 免责声明

本项目无法承诺 `userbot` 行为不会被 `telegram` 官方滥权，也无法承诺所有功能能在自建项目上成功运行。

使用 `userbot` 所带来的损失或可能产生的任何责任由搭建者自行承担。

# 建议

欢迎您加入 [本项目支持群](https://t.me/PagerMaid_Modify) ，对于本项目用户，我们通常情况下可在支持群中予以提供搭建和使用帮助。

# 特别提醒

由于 userbot 的特殊性，请不要相信任何能够免费提供服务器给您搭建的人。

尤其是需要保护好 `pagermaid.session` ，任何拥有此文件的人都可以进行包括修改二次验证密码、更改手机号等操作。
