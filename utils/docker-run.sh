#!/bin/bash

welcome() {
  echo ""
  echo "欢迎进入 PagerMaid-Modify Docker 。"
  echo "配置即将开始"
  echo ""
  sleep 2
}

configure() {
  cd /pagermaid/workdir
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

login() {
  echo ""
  echo "下面进行程序试运行。"
  echo "请在账户授权完毕后按 Ctrl + C 退出"
  echo ""
  sleep 2
  /pagermaid/workdir/venv/bin/python -m pagermaid
  echo ""
  echo "程序试运行完毕。"
  echo ""
}

systemctl_reload(){
  echo "正在写入系统进程守护 . . ."
  sudo -i
    echo "[Unit]
    Description=PagerMaid-Modify telegram utility daemon
    After=network.target
    [Install]
    WantedBy=multi-user.target
    [Service]
    Type=simple
    WorkingDirectory=/pagermaid/workdir
    ExecStart=/pagermaid/workdir/venv/bin/python -m pagermaid
    Restart=always
    ">/etc/systemd/system/pagermaid.service
    chmod 755 pagermaid.service >> /dev/null 2>&1
    systemctl daemon-reload >> /dev/null 2>&1
    systemctl enable pagermaid >> /dev/null 2>&1
    su pagermaid
    echo ""
    echo "请在脚本退出后输入 exit 退出 Docker"
    echo ""
    exit
}

start_installation() {
  welcome
  configure
  login
  systemctl_reload
}

start_installation
