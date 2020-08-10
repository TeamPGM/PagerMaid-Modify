#!/bin/bash
if [[ $EUID -ne 0 ]]; then
    clear
    echo "错误：本脚本需要 root 权限执行。" 1>&2
    exit 1
fi


welcome() {
  echo ""
  echo "欢迎使用 PagerMaid-Modify 一键安装程序。"
  echo "安装即将开始"
  echo "如果您想取消安装，"
  echo "请在 5 秒钟内按 Ctrl+C 终止此脚本。"
  echo ""
  sleep 5
}


docker_check() {
  echo "正在检查 Docker 安装情况 . . ."
  if command -v docker >> /dev/null 2>&1;
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
  if command -v git >> /dev/null 2>&1;
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
    echo "该用户无权访问 Docker，或者 Docker 没有运行。 请添加自己到 Docker 分组并重新运行此脚本。"
    exit 1
  fi
}

build_docker() {
  printf "请输入 PagerMaid 容器的名称："
  read -r container_name <&1
  echo "正在构建 Docker 镜像 . . ."
  docker rm -f "$container_name" > /dev/null 2>&1
  docker build - --force-rm --no-cache -t pagermaid_"$container_name" < Dockerfile.persistant
}

start_docker() {
  echo "正在启动 Docker 容器 . . ."
  echo "在登录后，请按 Ctrl + C 使容器在后台模式下重新启动。"
  sleep 3
  docker run -it --restart=always --name="$container_name" --hostname="$container_name" pagermaid_"$container_name" <&1
  docker restart $container_name > /dev/null 2>&1
}

cleanup() {
  echo "正在清理临时文件 . . ."
  rm -rf /tmp/pagermaid
}

start_installation() {
  check_sys
  welcome
  docker_check
  git_check
  access_check
  build_docker
  start_docker
  cleanup
}

start_installation
