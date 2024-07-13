# 使用官方的Ubuntu 22.04基础镜像
FROM hub.atomgit.com/arm64v8/ubuntu:23.10



 RUN echo 'deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ mantic main restricted universe multiverse'> /etc/apt/sources.list
# deb-src http://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ mantic main restricted universe multiverse
 RUN echo 'deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ mantic-updates main restricted universe multiverse'>> /etc/apt/sources.list
# deb-src http://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ mantic-updates main restricted universe multiverse
 RUN echo 'deb http://ports.ubuntu.com/ubuntu-ports/ mantic-security main restricted universe multiverse'>> /etc/apt/sources.list
 RUN echo 'deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ mantic-backports main restricted universe multiverse'>> /etc/apt/sources.list
# deb-src http://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ mantic-backports main restricted universe multiverse

# 以下安全更新软件源包含了官方源与镜像站配置，如有需要可自行修改注释切换
# deb-src http://ports.ubuntu.com/ubuntu-ports/ mantic-security main restricted universe multiverse

# 预发布软件源，不建议启用
# deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ mantic-proposed main restricted universe multiverse
# # deb-src http://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports/ mantic-proposed main restricted universe multiverse

# 设置作者信息
# 更新apt源并安装ssh-server和其他工具
RUN apt-get update
RUN apt-get upgrade  -y
RUN apt-get install python3 clangd pip -y
RUN apt-get install zsh fish -y
RUN apt-get install sudo -y
RUN apt-get install git -y

RUN apt install python3.11-venv -y
RUN apt install openssh-server -y
RUN apt install net-tools -y
RUN apt install inetutils-ping -y
RUN echo "ubuntu:1" | chpasswd

# 添加用户并设置密码
RUN useradd -ms /bin/bash z && echo "z:1" | chpasswd
ENTRYPOINT ["/usr/bin/zsh"]
