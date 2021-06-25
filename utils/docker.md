## 特点

- 容器在启动或重启时，将自动更新脚本并安装pip依赖。

- 包括redis缓存数据和插件在内，全部数据支持数据持久化，更新镜像或重建容器数据不丢失。

- 有些插件额外需要一些未安装的依赖，支持用户自己定义`requirements2.txt`，创建容器时即自动安装好，这样更新镜像或重建容器不影响这些插件的使用。

- 由用户自己选择以root权限还是以普通用户权限来运行pagermaid，以普通用户权限运行时更安全，但需要用户具有解决权限问题的能力。

## 一键脚本安装

```
wget https://raw.githubusercontent.com/Xtao-Labs/PagerMaid-Modify/master/utils/docker.sh
bash docker.sh
```

*注：一键脚本安装的Docker将以root权限运行，在使用pagermaid时最方便。如需要自定义，请使用docker-compose安装。*

## docker-compose安装

1. 准备脚本

```
git clone https://github.com/Xtao-Labs/PagerMaid-Modify pagermaid
cd pagermaid
cp docker-compose.gen.yml docker-compose.yml
```

2. 编辑刚刚复制的`docker-compose.yml`为你自己的信息，如不想解决权限问题，建议`RUN_AS_ROOT=true`。

3. 有些插件还额外需要安装依赖包，这些依赖包初始状态是没有安装的，例如`neteasemusic`插件的依赖`eyed3` `pycryptodome`，`coin`插件的依赖`python-binance` `xmltodict`等等，你如果需要用到这些插件，并且希望容器自动将依赖安装好，可以将依赖列在当前目录下的`requirements2.txt`中（没有这个文件，需要你自己建立）。容器将在启动时自动安装这些依赖。有此`requirements2.txt`文件以后，重新部署容器或者更新镜像，都将自动安装这些依赖，不再需要重复地手动安装。

4. 启动容器`docker-compose up -d`。

5. 运行`docker exec -it pagermaid bash utils/docker-config.sh`进行配置。

