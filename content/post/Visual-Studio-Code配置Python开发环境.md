---
title: Visual Studio Code配置Python开发环境
slug: vscode-python-environment
date: 2016-06-29 21:29:45
categories: 
- Python
tags: 
- Python
- VSCode
---

# 1.安装Python插件

在VScode界面按`Crtl`+`Shift`+`P`或者`F1`

输入`ext install`

![ext install](/images/uploads/466e425945714456686a364e627865744763442d414838515f653955.png)

直接安装`Python`，也就是点击它，然后等待，安装好后会提示你重启
<!--more-->

# 2.配置运行Python程序

同样的打开命令面板（`Crtl`+`Shift`+`P`或`F1`），然后输入`Tasks: Configure Task Runner`（中文输入：任务，然后选择任务：配置任务运行程序），选择`Other`

此时VScode会自动生成.vscode文件夹并生成一个默认的task.json

![tasks.json](/images/uploads/466b50476a363774626941735f4974335930772d453231516557737a.png)

配置如下


    "version": "0.1.0",
    "command": "python",
    "isShellCommand": true,
    "args": ["${file}"],
    "showOutput": "always"

然后写完代码后
`Crtl`+`Shift`+`B`运行Py程序
![python-run](/images/uploads/466f3434734435754c39786a4f5f683333697a7561622d5172735134.png)

