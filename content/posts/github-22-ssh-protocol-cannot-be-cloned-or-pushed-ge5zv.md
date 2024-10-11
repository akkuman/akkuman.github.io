---
title: github 22 ssh 协议无法克隆或推送
slug: github-22-ssh-protocol-cannot-be-cloned-or-pushed-ge5zv
url: /post/github-22-ssh-protocol-cannot-be-cloned-or-pushed-ge5zv.html
date: '2024-10-10 16:39:15+08:00'
lastmod: '2024-10-11 13:21:06+08:00'
toc: true
isCJKLanguage: true
---

# github 22 ssh 协议无法克隆或推送

有两种方案

## 使用代理

编辑 \~/.ssh/config

先安装 ncat(nmap)

```plain
Host github.com
	User git
	HostName github.com
	ProxyCommand ncat --proxy-type socks5 --proxy-auth akkuman:akkuman --proxy 127.0.0.1:1080 %h %p
	TCPKeepAlive yes
```

## 改用 ssh with 443

比如 `git clone git@github.com:akkuman/rotateproxy.git`​ 改用 `git clone ssh://git@ssh.github.com:443/akkuman/rotateproxy.git`​

‍
