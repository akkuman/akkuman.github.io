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

**20260402 更新**：看了下最新版的 mobaxterm，已经内置支持 windows ssh agent，不再需要 winssh-pageant 了。

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

## 高级用法

### 代理转发

以下内容来自 [Sign Git commits with SSH | 1Password Developer](https://developer.1password.com/docs/ssh/agent/forwarding)

启用远程主机的代理转发后，远程主机上的 `SSH_AUTH_SOCK` 环境变量会自动设置，您在远程环境中发出的每个 SSH 请求都会被转发到本地的 ssh-agent

如果要为某个主机启用代理转发，可以在 ssh 带上 `-A` 参数

```bash
ssh -A user@example.com
```

要检查是否正常工作，可以在远程主机上执行 `ssh-add -l` 查看转发到远程主机的 SSH 密钥列表。

比如你本地有 github 的 ssh key，那么你可以在远程主机上执行 `ssh -T git@github.com` 来测试

如果你想落地成配置，按照如下样例对本地的 `~/.ssh/config` 进行配置

```bash
Host example.com
  ForwardAgent yes
```

## 问题

### 1. Too many authentication failures

这种情况发生在你在 bitwarden 里面添加了太多 ssh key，ssh 会挨个尝试，一般服务器定的尝试最大次数是 6，导致尝试次数超限

解决方案有如下几个方案（参考 [Advanced use cases | 1Password Developer](https://developer.1password.com/docs/ssh/agent/advanced/#ssh-server-six-key-limit)）：

1. 编辑对应服务器的 `/etc/ssh/sshd_config`，设置 MaxAuthTries 来增加此限制，但在许多情况下，无法（或不想）更改此设置。您可以改为指定哪个主机应与哪个 SSH 密钥匹配。
2. 为避免出现 `Too many authentication failures`​ 错误，您的 SSH 客户端需要知道哪个 SSH 公钥应该与哪个主机一起使用。这可以通过在 SSH 配置文件中设置 `Host`​ 块中的 `IdentityFile` 来配置，其值应为您希望与该主机一起使用的公钥。

   1. 复制 bitwarden 私钥所对应的公钥，然后写入 `~/.ssh/xxx.pub` 文件
   2. 在你的 `~/.ssh/config`​ 文件中，添加一个条目，指向你要连接的主机，并将 `IdentityFile` 设置为刚才创建的公钥路径  
      经过测试，IdentitiesOnly 配置项非必需

      ```bash
      Host github.com
        IdentityFile ~/.ssh/xxx.pub
        IdentitiesOnly yes
      ```
   3. 现在，您的 SSH 客户端将知道在连接到 SSH 服务器时要使用哪个密钥，因此将不会遇到这些身份验证限制
   4. **注意**：某些 SSH 客户端不支持在 `IdentityFile`​ 中指定公钥。请参阅 [SSH 客户端兼容性 ](https://developer.1password.com/docs/ssh/agent/compatibility/#identity-file)

### 2. 同一台服务器使用不同的身份

没有使用 ssh-agent 之前，你可能使用如下的手段来定义不同的 ssh 别名，以使用不同的身份登录远端 ssh

```bash
Host user1server
  HostName test.com
  User user1
  IdentityFile ~/.ssh/user1_id_rsa

Host user2server
  HostName test.com
  User user2
  IdentityFile ~/.ssh/user2_id_rsa
```

然后使用 `ssh user1server` 这种命令来以不同的身份登录服务器

现在要使用 ssh-agent，你只需要将 `IdentityFile` 按照上面的方式改为 pub key 即可。

例如在同一台机器上使用多个 Git 身份（来自 [Advanced use cases | 1Password Developer](https://developer.1password.com/docs/ssh/agent/advanced/#use-multiple-git-identities-on-the-same-machine)）

```bash
# Personal GitHub
Host personalgit
  HostName github.com
  User git
  IdentityFile ~/.ssh/personal_git.pub
  IdentitiesOnly yes

# Work GitHub
Host workgit
  HostName github.com
  User git
  IdentityFile ~/.ssh/work_git.pub
  IdentitiesOnly yes
```

对于每个 Git 存储库，将 `git` URL 更改为使用新的 SSH 主机别名之一，而不是默认主机 URL

```bash
git remote set-url origin <host>:<workplace>/<repo>.git
```

例如

```bash
git remote set-url origin personalgit:1password/1password-teams-open-source.git
```

这样 SSH 客户端将知道每个 Git 身份应该使用哪个 SSH 密钥

### 3. 普通 ssh 也会报错 Too many authentication failures

这个和第 1 个问题同源。

我们可以在 ssh 时添加 `IdentitiesOnly=yes` 来规避这个问题

例如

```bash
ssh -o IdentitiesOnly=yes ubuntu@192.168.1.1
```

如果你是想对特定网段启用全部启用该配置，可以将如下内容添加到 `~/.ssh/config`

```bash
Host 192.168.1.*
  IdentitiesOnly yes
```

这个配置代表在 `192.168.1.*`​ 上启用 `IdentitiesOnly=yes`

但有个例外情况，就算你做了上述配置，在 mobaxterm 上还是会出现该问题，需要在 session 配置中，打开 Expert SSH settings，然后取消勾选，即可

不过 mobaxterm 有个 ssh tunnel 功能还是无解
