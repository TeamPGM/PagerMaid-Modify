#!/bin/sh

welcome() {
  echo ""
  echo "欢迎使用PagerMaid-Modify Docker 安装程序。"
  echo "安装即将开始"
  echo "在5秒钟内，如果您想取消，"
  echo "请在5秒钟内终止此脚本。"
  echo ""
  sleep 5
}

docker_check() {
  echo "正在检查 Docker 安装情况 . . ."
  if command -v docker;
  then
    echo "Docker 似乎存在, 安装过程继续 . . ."
  else
    echo "Docker 未安装在此系统上"
    echo "请安装 Docker 并将自己添加到 Docker"
    echo "分组并重新运行此脚本。"
    exit 1
  fi
}

git_check() {
  echo "正在检查 Git 安装情况 . . ."
  if command -v git;
  then
    echo "Git 似乎存在, 安装过程继续 . . ."
  else
    echo "Git 未安装在此系统上"
    echo "请安装 Git 并重新运行此脚本。"
    exit 1
  fi
}

access_check() {
  echo "测试 Docker 环境 . . ."
  if [ -w /var/run/docker.sock ]
  then
    echo "该用户可以使用 Docker , 安装过程继续 . . ."
  else
    echo "该用户无权访问 Docker，或者 Docker"
    echo "没有运行。 请添加自己到 Docker"
    echo "分组并重新运行此脚本。"
    exit 1
  fi
}

download_repo() {
  echo "下载 repository 中. . ."
  rm -rf /tmp/pagermaid
  git clone https://github.com/xtaodada/PagerMaid-Modify.git /tmp/pagermaid
  cd /tmp/pagermaid || exit
}

configure() {
  config_file=config.yml
  echo "生成配置文件中 . . ."
  cp config.gen.yml config.yml
  printf "请输入应用程序 api_key："
  read -r api_key <&1
  sed -i "s/KEY_HERE/$api_key/" $config_file
  printf "请输入应用程序 api_hash："
  read -r api_hash <&1
  sed -i "s/HASH_HERE/$api_hash/" $config_file
  printf "请输入应用程序语言（示例：zh-cn）："
  read -r application_language <&1
  sed -i "s/zh-cn/$application_language/" $config_file
  printf "请输入应用程序地区（例如：China）："
  read -r application_region <&1
  sed -i "s/China/$application_region/" $config_file
   printf "请输入 Google TTS 后缀（例如：cn）："
  read -r application_tts <&1
  sed -i "s/cn/$application_tts/" $config_file
  printf "启用日志记录？ [Y/n]"
  read -r logging_confirmation <&1
  case $logging_confirmation in
      [yY][eE][sS]|[yY])
		    printf "请输入您的日志记录群组/频道的 ChatID （如果要发送给 Kat ，请按Enter）："
		    read -r log_chatid <&1
		    if [ -z "$log_chatid" ]
		    then
		      echo "LOG 将发送到 Kat."
		    else
		      sed -i "s/503691334/$log_chatid/" $config_file
		    fi
		    sed -i "s/log: False/log: True/" $config_file
		    ;;
      [nN][oO]|[nN])
		    echo "安装过程继续 . . ."
        ;;
      *)
	  echo "输入错误 . . ."
	  exit 1
	  ;;
  esac
}

build_docker() {
  printf "请输入 PagerMaid 容器的名称："
  read -r container_name <&1
  echo "正在构建 Docker 镜像 . . ."
  docker rm -f "$container_name" > /dev/null 2>&1
  docker build - --force-rm --no-cache -t pagermaid_"$container_name < Dockerfile.persistant"
}

start_docker() {
  echo "正在启动 Docker 容器 . . ."
  echo "在登录后，请按 Ctrl + C 使容器在后台模式下重新启动。"
  sleep 3
  docker run -it --restart=always --name="$container_name" --hostname="$container_name" pagermaid_"$container_name" <&1
}

cleanup() {
  echo "正在清理临时文件 . . ."
  rm -rf /tmp/pagermaid
}

start_installation() {
  welcome
  docker_check
  git_check
  access_check
  download_repo
  configure
  build_docker
  start_docker
  cleanup
}

start_installation
