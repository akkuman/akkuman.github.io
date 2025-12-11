---
title: 一行命令共享 SSH 终端会话
slug: oneline-command-to-share-an-ssh-terminal-session-z1wqqxi
date: 2025-12-11 09:20:00:00+08:00
lastmod: '2025-12-11 09:20:22+08:00'
tags:
  - Linux
categories:
  - 技术分享
keywords: Linux
description: >-
  本文介绍了一种快速共享SSH终端会话的方法，使用一条命令即可通过upterm工具（tmate的替代品）创建临时会话。执行命令后，系统会生成一个临时的SSH连接地址，用户可将其分享给他人以实现终端实时共享。
toc: true
isCJKLanguage: true
---





```bash
TMP_DIR=$(mktemp -d) && trap 'rm -rf "$TMP_DIR"' EXIT && curl -fsSL https://github.com/owenthereal/upterm/releases/download/v0.20.0/upterm_linux_amd64.tar.gz | tar -xz -C "$TMP_DIR" && "$TMP_DIR"/upterm host && rm -rf "$TMP_DIR"
```

upterm 是 tmate.io 的替代品

该命令会在执行完成后删除 upterm 文件

然后会打印出来

```plaintext
╭─ Session: oNWF9treC2UudFSY7Ztx ─╮
┌─────────┬────────────────────── ┐
│ Command:         │ /bin/bash                                   │
│ Force Command:   │ n/a                                         │
│ Host:            │ ssh://uptermd.upterm.dev:22                 │
│ Authorized Keys: │ n/a                                         │
│                  │                                             │
│ ➤ SSH Command:   │ ssh oNWF9treC2UudFSY7Ztx@uptermd.upterm.dev │
└─────────┴────────────────────── ┘

╰─ Run 'upterm session current' to display this again ─╯

🤝 Accept connections? [y/n] (or <ctrl-c> to force exit)

```

按 y 即可共享终端

然后输入 exit 执行可退出共享终端

其他人使用 `ssh oNWF9treC2UudFSY7Ztx@uptermd.upterm.dev`​ 即可连接到该共享终端

其中 upterm 的服务器也可以自行部署
