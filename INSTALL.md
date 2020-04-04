# 安装

这是开始使用 `PagerMaid` 所需的说明，支持各种初始化系统。

## 要求

您需要 `Linux` 或 `*BSD` 系统，并且您的系统应该至少运行 `python 3.6` ，推荐虚拟环境运行。

为确保 Bug reporter 的正常进行可能您需要手动私聊 [@KatOnKeyboard](https://t.me/KatOnKeyboard) 一次。

## 快速开始

如果您的系统与docker兼容，并且您想要快速且受支持的安装，Docker 将帮助您快速入门。尽管很方便，但这种安装方法将系统范围的包限制在容器内。

在 https://my.telegram.org/ 上创建您的应用程序，然后运行以下命令：


```
curl -fsSL https://raw.githubusercontent.com/xtaodada/PagerMaid-Modify/master/utils/docker.sh | sh
```

如果您想在运行之前检查脚本内容：

```
curl https://raw.githubusercontent.com/xtaodada/PagerMaid-Modify/master/utils/docker.sh -o docker.sh
vim docker.sh
chmod 0755 docker.sh
./docker.sh
```

## 配置

将文件 `config.gen.yml` 复制一份到 `config.yml` ，并使用您最喜欢的文本编辑器，编辑配置文件，直到您满意为止。

## 从源代码安装

将 `PagerMaid-Modify` 工作目录复制到 `/var/lib` ，然后输入 `/var/lib/pagermaid` ，激活虚拟环境（如果需要），并从 `requirements.txt` 安装所有依赖项

```
python3 -m pagermaid
```

现在确保 `zbar` ， `neofetch` ， `tesseract` 和 `ImageMagick` 软件包是通过软件包管理器安装的，并且您已经准备好启动 `PagerMaid` 。

```
python3 -m pagermaid
```

## 从PyPi安装

为 `PagerMaid` 创建一个工作目录，通常为 `/var/lib/pagermaid` ，建议设置虚拟环境。

安装PagerMaid模块：

```
pip3 install pagermaid
```

现在确保 `zbar` ， `neofetch` ， `tesseract` 和 `ImageMagick` 软件包是通过软件包管理器安装的，并且您已经准备好启动 `PagerMaid` 。

```
pagermaid
```

## 进程守护

确保您至少手动运行过 `PagerMaid` 一次，或者已经存在 session 文件。
- Runit：在 `/etc/sv/pagermaid` 中创建一个目录，然后将 `utils/run` 复制到其中
- SystemD：将 `utils/pagermaid.service` 复制到 `/ var/lib/systemd/system` 中
- 直接：运行 `utils/start.sh`

## 身份验证

有时（或大部分时间），当您在服务器部署 `PagerMaid` 时，登录会有问题，当出现了问题，请在应用程序的配置步骤配置唯一的 `application key` 和 `hash` ，然后在您的PC上运行 `utils/mksession.py` ，将 `pagermaid.session` 复制到服务器。

## 插件

`some-plugins` 已经内置了部分插件，请根据需要复制到 plugins 启用。