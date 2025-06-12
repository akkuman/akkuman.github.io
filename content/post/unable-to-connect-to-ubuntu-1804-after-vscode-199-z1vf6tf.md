---
title: vscode 1.99 后无法连接到 ubuntu 18.04
slug: unable-to-connect-to-ubuntu-1804-after-vscode-199-z1vf6tf
date: '2025-05-29 16:44:14+08:00'
lastmod: '2025-06-11 09:32:57+08:00'
toc: true
isCJKLanguage: true
---



# vscode 1.99 后无法连接到 ubuntu 18.04

‍

## 背景

vscode 远程开发出现报错 The remote host doesn't meet the prerequisites for running VS Code Server（远程主机不满足运行VS Code服务器的先决条件）

## 根本原因

早在2023年还是2024年初，vscode 就出过一次这种问题，官方的主要目的是放弃对低版本系统的支持。不过当时没有任何通知，比较突然，后续官方发了一个修复版本，让大家可以继续使用低版本系统到 2025 年第一季度，给了大家一定的时间去升级系统。

然后官方在 1.97 的 changelog 中决定在 1.99 后将不允许连接到低版本系统进行远程开发。

不过官方也给出了解决方案

参见 https://aka.ms/vscode-remote/faq/old-linux

## 解决方案

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
