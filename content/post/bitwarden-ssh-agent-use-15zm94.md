---
title: bitwarden ssh agent 使用
slug: bitwarden-ssh-agent-use-15zm94
date: '2026-03-27 16:48:38+08:00'
lastmod: '2026-03-31 17:45:58+08:00'
tags:
  - 工具
categories:
  - 技术分享
keywords: 工具
description: 本文介绍了如何使用 Bitwarden 密码管理器来管理SSH密钥，并通过其SSH代理功能在各种操作系统和终端环境下安全、方便地使用这些密钥进行认证。
toc: true
isCJKLanguage: true
---





## 背景

最近 apifox 的安全事件，让我想用密码管理器管理 ssh 密钥了。

以前也考虑过一次，但由于 bitwarden 不支持，就作罢了。

现在发现 bitwarden 在 2025 年已经支持了 ssh 密钥。

## 使用

### 导入密钥

具体可参见 [Bitwarden SSH Agent | Bitwarden](https://bitwarden.com/help/ssh-agent/)

这里说说我遇到的情况：

1. 似乎无法导入自己现有的密钥，只能生成

这个解决方案是：先新建，让它随机生成一个，然后再打开这个条目重新编辑，就能在私钥右边看到一个从剪贴板导入，复制你的密钥即可

2. 某些 rsa 的私钥似乎不支持，无法导入

这是因为旧版 OpenSSH 和大多数 TLS 库（例如 OpenSSH）使用的标准 PEM 格式，经典的 id_rsa 文件通常采用这种格式 。它是一个 ASN.1 编码结构，采用 base64 编码，并放置在 PEM 头部之间。

我们可以先备份，然后使用下面的命令进行转换

```bash
cp ~/.ssh/id_rsa ~/.ssh/id_rsa.bak
ssh-keygen -p -f ~/.ssh/id_rsa
```

转换后放到 windows 主机，使用时（比如测试 `ssh -p 443 -T git@ssh.github.com`）可能会报错

```bash
Load key "/c/Users/Administrator/.ssh/id_rsa": error in libcrypto
git@ssh.github.com: Permission denied (publickey).
```

这个错误大概率是换行格式不对，需要将 CRLF 转换成 LF

如果你是在 git bash 中生成，或者是直接从 linux 下载文件到本地，大概率没问题。

如果你是在 windows 上创建文件然后拷贝进去，大概率存在问题

拷贝进去默认是这样

![image](/images/uploads/image-20260327173206-3pk5n06.png)

我们需要执行 `dos2unix.exe ~/.ssh/id_rsa` 来进行转换

转换后会是这个样子

![image](/images/uploads/image-20260327173321-kna1o6k.png)

注意，这些行尾都必须存在，格式必须一致，不然就会报错 `Load key ...: error in libcrypto`

转换后，这个 id_rsa 就可以导入 bitwarden 了

### 启动 ssh agent

打开 bitwarden desktop 客户端

打开设置 -> 启用 ssh 代理

### Windows 上的使用

此时你直接在 windows 终端中执行 `ssh-add -l` 应该能看到了。

#### mobaxterm

但是对于 mobaxterm 这种使用 putty pageant 协议的，使用不了

此处使用 mobaxterm 举例

[Windows] + [R]，打开 services.msc

从服务列表中停止 OpenSSH Authentication Agent ，然后将其禁用

然后去 [ndbeals/winssh-pageant: Bridge to Windows OpenSSH agent from Pageant. This means the openssh agent has the keys and this proxies pageant requests to it.](https://github.com/ndbeals/winssh-pageant) 下载 winssh-pageant

然后双击运行，打开任务管理器，你应该能看到这个程序正在运行

![image](/images/uploads/image-20260331171755-yahg7b8.png)

然后再在 mobaxterm 本地终端中执行 `ssh-add -l` 应该能看到了

#### Git

如果此时你使用 git for windows，你可能会得到 `Could not open a connection to your authentication agent.` 的错误

这是因为 git for windows 有自己的一套 msys 环境。简而言之：

你可以执行 `git config --global core.sshCommand "C:/Windows/System32/OpenSSH/ssh.exe"` 来强制 git ssh 使用 windows 自带的 ssh 即可。

如果你想使用 git bash，在其中正常使用 ssh 等命令，你需要在 git bash 中编辑 .bashrc，补充如下内容

```bash
alias ssh='/c/Windows/System32/OpenSSH/ssh.exe'
alias ssh-add='/c/Windows/System32/OpenSSH/ssh-add.exe'
alias ssh-keygen='/c/Windows/System32/OpenSSH/ssh-keygen.exe'
```

来自 [How do i set up Bitwarden ssh-agent within git-bash? : r/Bitwarden](https://www.reddit.com/r/Bitwarden/comments/1l5aw67/how_do_i_set_up_bitwarden_sshagent_within_gitbash/)

### MacOS 的使用

这部分来自官方文档 [Bitwarden SSH Agent | Bitwarden](https://bitwarden.com/help/ssh-agent/#tab-macos-6VN1DmoAVFvm7ZWD95curS)

#### 如果从 App Store 安装

```bash
export SSH_AUTH_SOCK=/Users/<user>/Library/Containers/com.bitwarden.desktop/Data/.bitwarden-ssh-agent.sock
```

#### 如果从 dmg 文件安装

```bash
export SSH_AUTH_SOCK=/Users/<user>/.bitwarden-ssh-agent.sock
#或者
launchctl setenv "SSH_AUTH_SOCK" "/Users/<user>/.bitwarden-ssh-agent.sock"
```

### Linux 的使用

这部分来自官方文档 [Bitwarden SSH Agent | Bitwarden](https://bitwarden.com/help/ssh-agent/#tab-linux-6VN1DmoAVFvm7ZWD95curS)

#### 如果使用常规方法（deb/rpm/AppImage）安装

```bash
export SSH_AUTH_SOCK=/home/<user>/.bitwarden-ssh-agent.sock
```

#### 如果您通过 Snap 或 Flatpak 安装

```bash
# Snap
export SSH_AUTH_SOCK=/home/<user>/snap/bitwarden/current/.bitwarden-ssh-agent.sock

# Flatpak: 有时会出现无法正常运行的情况
# https://github.com/bitwarden/clients/issues/13166#issuecomment-2755659475
export SSH_AUTH_SOCK=/home/<user>/.var/app/com.bitwarden.desktop/data/.bitwarden-ssh-agent.sock
```

根据您的环境，将上面的内容添加到您的 \~/.zshrc 或 \~/.bashrc 文件中
