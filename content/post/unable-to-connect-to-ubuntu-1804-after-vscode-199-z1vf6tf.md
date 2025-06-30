---
title: vscode 1.99 后无法连接到 ubuntu 18.04
slug: unable-to-connect-to-ubuntu-1804-after-vscode-199-z1vf6tf
date: '2025-05-29 16:44:14+08:00'
lastmod: '2025-06-11 09:32:57+08:00'
tags:
  - vscode
  - 远程开发
  - ubuntu
  - glibc
  - patchelf
keywords: vscode,远程开发,ubuntu,glibc,patchelf
description: >-
  VS Code 官方放弃了对Ubuntu
  18.04等旧版Linux系统的支持。本文提供了一个比官方更简单的解决方案，无需手动编译可绕过系统限制继续使用远程开发功能。
toc: true
isCJKLanguage: true
---





## 背景

vscode 远程开发出现报错 The remote host doesn't meet the prerequisites for running VS Code Server（远程主机不满足运行VS Code服务器的先决条件）

## 根本原因

早在2023年还是2024年初，vscode 就出过一次这种问题，官方的主要目的是放弃对低版本系统的支持。不过当时没有任何通知，比较突然，后续官方发了一个修复版本，让大家可以继续使用低版本系统到 2025 年第一季度，给了大家一定的时间去升级系统。

然后官方在 1.97 的 changelog 中决定在 1.99 后将不允许连接到低版本系统进行远程开发。

不过官方也给出了解决方案

参见 https://aka.ms/vscode-remote/faq/old-linux

## 250622 之后的解决方案

现在似乎又出问题了，最稳定的还是使用 linuxbrew。这里给出基于 linuxbrew 的解决方案，此处使用 bash 举例，如果你是 zsh 等环境，可以参见 [homebrew | 镜像站使用帮助 | 清华大学开源软件镜像站 | Tsinghua Open Source Mirror](https://mirrors.tuna.tsinghua.edu.cn/help/homebrew/)

```bash
export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.aliyun.com/homebrew/brew.git"
export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.aliyun.com/homebrew/homebrew-core.git"
export HOMEBREW_INSTALL_FROM_API=1
# 从阿里云下载安装脚本并安装 Homebrew 
git clone https://mirrors.aliyun.com/homebrew/install.git brew-install
/bin/bash brew-install/install.sh
rm -rf brew-install
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
echo >> /home/CORP/songhao.lin/.bashrc
echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> /home/CORP/songhao.lin/.bashrc
echo '# Set non-default Git remotes for Homebrew/brew and Homebrew/homebrew-core.' >> /home/CORP/songhao.lin/.bashrc
echo 'export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.aliyun.com/homebrew/brew.git"' >> /home/CORP/songhao.lin/.bashrc
echo 'export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.aliyun.com/homebrew/homebrew-core.git"' >> /home/CORP/songhao.lin/.bashrc
```

如果是海外环境，直接使用 `/bin/bash -c "$(curl -fsSL https://github.com/Homebrew/install/raw/master/install.sh)"`​ 即可

然后使用命令 `brew install patchelf`​ 安装 patchelf

然后执行如下命令

```bash
echo 'VSCODE_SERVER_CUSTOM_GLIBC_PATH=/home/linuxbrew/.linuxbrew/opt/glibc/lib' >> ~/.ssh/environment
echo 'VSCODE_SERVER_PATCHELF_PATH=/home/linuxbrew/.linuxbrew/bin/patchelf' >> ~/.ssh/environment
echo 'VSCODE_SERVER_CUSTOM_GLIBC_LINKER=/home/linuxbrew/.linuxbrew/opt/glibc/lib/ld-linux-x86-64.so.2' >> ~/.ssh/environment
sudo sed -i 's|#PermitUserEnvironment no|PermitUserEnvironment yes|g' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

## 旧版解决方案

官方给出的解决方案是先使用 crosstool 弄出一个高版本 glibc 的环境，然后使用 patchelf 来自动 patch

不过这个方案需要拿 crosstool 自己编译，也挺麻烦

有人给出了可以使用 brew 安装 glibc 和 patchelf，参见 [Connect to Unsupported Older Linux servers with VS Code Remote-SSH using Custom glibc &amp; libstdc++ - DEV Community](https://dev.to/subrata/connect-to-unsupported-older-linux-servers-with-vs-code-remote-ssh-using-custom-glibc-libstdc-m63)

但是 brew 是一个 ruby 工具，安装也挺麻烦。

下面给出一种更简单的方案

### 下载 glibc

```bash
# 下载 glibc bottle
curl --disable --cookie /dev/null --globoff --show-error --fail --progress-bar --retry 3 --header 'Authorization: Bearer QQ==' --location --remote-time --output glibc.bottle.tar.gz "https://ghcr.io/v2/homebrew/core/glibc/blobs/sha256:91e866deda35d20e5e5e7a288ae0902b7692ec4398d4267c74c84a6ebcc7cdd9"
# 将 glibc/2.35_1 放到 /opt 下
sudo tar -xzf glibc.bottle.tar.gz -C /opt

```

### 下载 patchelf

打开 [Releases · NixOS/patchelf](https://github.com/NixOS/patchelf/releases) 下载合适的 patchelf

然后解压出来，将 bin/patchelf 放置到主机上的 /usr/local/bin/patchelf

### 配置环境变量

然后将以下内容写入到 ~/.ssh/environment 中

```bash
VSCODE_SERVER_CUSTOM_GLIBC_LINKER=/opt/glibc/2.35_1/lib/ld-linux-x86-64.so.2
VSCODE_SERVER_CUSTOM_GLIBC_PATH=/opt/glibc/2.35_1/lib:/usr/lib/x86_64-linux-gnu:/lib/x86_64-linux-gnu
VSCODE_SERVER_PATCHELF_PATH=/usr/local/bin/patchelf
```

然后执行如下命令开启 ssh 环境变量

```bash
sudo sed -i 's|#PermitUserEnvironment no|PermitUserEnvironment yes|g' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

### 构造搜索路径

注意该步骤是必要的，否则会出现终端无法打开的问题

```bash
sudo mkdir -p /home/linuxbrew/.linuxbrew/Cellar
sudo ln -s /opt/glibc /home/linuxbrew/.linuxbrew/Cellar/glibc
```

#### 重要的题外话

考虑到后面也可能出现同样的问题（linuxbrew 预编译的 glibc 有预置的库搜索路径）导致一些功能缺失，建议直接安装 linuxbrew + glibc 来使用。国内可参见 [homebrew | 镜像站使用帮助 | 清华大学开源软件镜像站 | Tsinghua Open Source Mirror](https://mirrors.tuna.tsinghua.edu.cn/help/homebrew/) 来安装，然后按照 [Connect to Unsupported Older Linux servers with VS Code Remote-SSH using Custom glibc &amp; libstdc++ - DEV Community](https://dev.to/subrata/connect-to-unsupported-older-linux-servers-with-vs-code-remote-ssh-using-custom-glibc-libstdc-m63) 中的来进行配置即可

## 重新测试

然后重新连接即可

如果不成功，请 ssh 登录到远程机器，执行 `env | grep VSCODE`​ 确认一下环境变量，如果不是这个，请检查你远程主机上的下列文件

- ​`~/.bashrc`​
- ​`/etc/environment`​
- ​`~/.profile`​
- ​`~/.zprofile`​
- ​`~/.bash_profile`​

查看是否有包含上述环境变量，如果存在就删除

## 参考链接

- [VS Code Server Not Detecting Custom Environment Variables for Old Linux Workaround · Issue #246375 · microsoft/vscode](https://github.com/microsoft/vscode/issues/246375#issuecomment-2883034221)
- [Connect to Unsupported Older Linux servers with VS Code Remote-SSH using Custom glibc &amp; libstdc++ - DEV Community](https://dev.to/subrata/connect-to-unsupported-older-linux-servers-with-vs-code-remote-ssh-using-custom-glibc-libstdc-m63)
- [Remote Development FAQ](https://code.visualstudio.com/docs/remote/faq#_can-i-run-vs-code-server-on-older-linux-distributions)
- [Allow connecting to unsupported Linux remotes, by use of custom glibc and stdc++ libraries · Issue #231623 · microsoft/vscode](https://github.com/microsoft/vscode/issues/231623)
- [How does homebrew store bottles? · Homebrew · Discussion #4335](https://github.com/orgs/Homebrew/discussions/4335#discussioncomment-5453917)
- [Package core/glibc](https://github.com/Homebrew/homebrew-core/pkgs/container/core%2Fglibc)

‍
