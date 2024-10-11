---
title: 配置 Dev Container
slug: configure-dev-container-h516g
url: /post/configure-dev-container-h516g.html
date: '2024-10-10 16:39:08+08:00'
lastmod: '2024-10-11 17:37:45+08:00'
toc: true
isCJKLanguage: true
---

# 配置 Dev Container

## 我的环境

vscode remote ssh 开发，远程主机上已安装 docker

并且当前用户已通过命令 `sudo usermod -aG docker $USER`​ 加入了 docker 组

## 使用

vscode 已安装 [https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) 插件

使用命令 ctrl shift p 搜索 dev container get start

选了我开发的 python3

然后vscode打开了一个新的窗口，显示设置容器时失败

报错为 Command failed: getent passwd

## 排错

但是手动调用 sudo getent passwd <user> 是成功的，不加 sudo 就不行

经过各方查证，可能原因是这里，[https://github.com/microsoft/vscode-remote-release/issues/2957](https://github.com/microsoft/vscode-remote-release/issues/2957) 但是我 ubuntu 使用的是 Samba AD 域认证，查找了一圈无合适的解决方案

按照 [https://github.com/microsoft/vscode-remote-release/issues/2957#issuecomment-874713511](https://github.com/microsoft/vscode-remote-release/issues/2957#issuecomment-874713511) 这里所说，去看看 getent 相关的源码看能不能有所发现

看了下，这个 getent passwd <user> 中的user实际来源于这

​![a2f698de866aedd810ef79e70c10c787.webp](https://raw.githubusercontent.com/akkuman/akkuman.github.io/hugo/images/a2f698de866aedd810ef79e70c10c787.webp)​

继续往上看了下，发现这个 remoteUser 无法置空（在 remote ssh）情况下

看来这个行不通

最后也没解决，让公司帮我换了个云桌面就没问题了
