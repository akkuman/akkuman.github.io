---
title: A script to help you clean up old versions of VS Code extensions
slug: a-script-to-help-you-clean-up-old-versions-of-vs-code-extensions-247eov
date: '2026-02-28 16:20:27+08:00'
lastmod: '2026-02-28 16:22:47+08:00'
tags:
  - vscode
  - Linux
categories:
  - 技术分享
keywords: vscode,Linux
toc: true
isCJKLanguage: true
---





‍

introduce

As is well known, this is a long-standing bug: VS Code always leaves behind old versions of extensions when upgrading extensions.

众所周知，这是一个长期存在的 bug：VS Code 在升级扩展程序时总是会留下旧版本的扩展程序。

Previously, this space usage was not a problem, but with the emergence of AI programming extensions, after long-term operation, the size of the related extensions may reach the GB level, quickly filling up the disk.

以前，这种空间占用不是问题，但随着 AI 编程扩展的出现，经过长期运行，相关扩展的大小可能会达到 GB 级别，迅速填满磁盘。

The main function of this extension is to help you remove older versions of the extension on your Linux host and devcontainer, thus freeing up disk space.

此扩展程序的主要功能是帮助您删除 Linux 和 devcontainer 上的旧版本扩展程序，从而释放磁盘空间。

### Usage

```bash
curl -s https://gist.githubusercontent.com/akkuman/c1d9577fab2a8701142887de5dc04270/raw/a9a5172936e75a04fdafaac3e5c87905558b662c/cleanup-vscode-ext.sh | bash
```
