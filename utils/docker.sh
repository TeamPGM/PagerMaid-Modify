#!/bin/sh

welcome() {
  echo ""
  echo "Welcome to PagerMaid docker installer."
  echo "The installation process will begin"
  echo "in 5 seconds, if you wish to cancel,"
  echo "please abort within 5 seconds."
  echo ""
  sleep 5
}

docker_check() {
  echo "Checking for docker . . ."
  if command -v docker;
  then
    echo "Docker appears to be present, moving on . . ."
  else
    echo "Docker is not installed on this system, please"
    echo "install docker and add yourself to the docker"
    echo "group and re-run this script."
    exit 1
  fi
}

git_check() {
  echo "Checking for git . . ."
  if command -v git;
  then
    echo "Git appears to be present, moving on . . ."
  else
    echo "Git is not installed on this system, please"
    echo "install git and re-run this script."
    exit 1
  fi
}

access_check() {
  echo "Testing for docker access . . ."
  if [ -w /var/run/docker.sock ]
  then
    echo "This user can access docker, moving on . . ."
  else
    echo "This user has no access to docker, or docker is"
    echo "not running. Please add yourself to the docker"
    echo "group or run the script as superuser."
    exit 1
  fi
}

download_repo() {
  echo "Downloading repository . . ."
  rm -rf /tmp/pagermaid
  git clone https://git.stykers.moe/scm/~stykers/pagermaid.git /tmp/pagermaid
  cd /tmp/pagermaid || exit
}

configure() {
  config_file=config.yml
  echo "Generating config file . . ."
  cp config.gen.yml config.yml
  printf "Please enter application API Key: "
  read -r api_key <&1
  sed -i "s/KEY_HERE/$api_key/" $config_file
  printf "Please enter application API Hash: "
  read -r api_hash <&1
  sed -i "s/HASH_HERE/$api_hash/" $config_file
  printf "Please enter application language (Example: en): "
  read -r application_language <&1
  sed -i "s/en/$application_language/" $config_file
  printf "Please enter application region (Example: United States): "
  read -r application_region <&1
  sed -i "s/United States/$application_region/" $config_file
  printf "Enable logging? [Y/n] "
  read -r logging_confirmation <&1
  case $logging_confirmation in
      [yY][eE][sS]|[yY])
		    printf "Please enter your logging group/channel ChatID (press Enter if you want to log into Kat): "
		    read -r log_chatid <&1
		    if [ -z "$log_chatid" ]
		    then
		      echo "Setting log target to Kat."
		    else
		      sed -i "s/503691334/$log_chatid/" $config_file
		    fi
		    sed -i "s/log: False/log: True/" $config_file
		    ;;
      [nN][oO]|[nN])
		    echo "Moving on . . ."
        ;;
      *)
	  echo "Invalid choice . . ."
	  exit 1
	  ;;
  esac
}

build_docker() {
  printf "Please enter the name of the PagerMaid container: "
  read -r container_name <&1
  echo "Building docker image . . ."
  docker rm -f "$container_name" > /dev/null 2>&1
  docker build - --force-rm --no-cache -t pagermaid_"$container_name < Dockerfile.persistant"
}

start_docker() {
  echo "Starting docker container . . ."
  echo "After logging in, press Ctrl + C to make the container restart in background mode."
  sleep 3
  docker run -it --restart=always --name="$container_name" --hostname="$container_name" pagermaid_"$container_name" <&1
}

cleanup() {
  echo "Cleaning up . . ."
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
