#!/bin/sh

welcome() {
  echo ""
  echo "欢迎使用 PagerMaid-Modify Docker 安装程序。"
  echo "安装即将开始"
  echo "在5秒钟内，如果您想取消，"
  echo "请在5秒钟内终止此脚本。"
  echo ""
  sleep 5
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

start_installation() {
  welcome
  configure
}

start_installation
