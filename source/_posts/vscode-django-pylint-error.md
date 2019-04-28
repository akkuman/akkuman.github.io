---
title: vscode打开django项目pylint提示has not "object" member
date: 2019-04-28 05:41:57
tags: 
- 问题解决
categories:
- 问题解决
---

vscode 打开 django 项目提示 has not "object" member 是因为 Django 动态地将属性添加到所有模型类中，所以 ide 无法解析。


<!-- more -->

解决方案：

1. 安装 pylint-django

```
pip install -U pylint-django
```

2. 启用 pylint-django

打开项目下自动生成的 .vscode 文件夹下的 setting.json 文件，添加下面的配置项。

```
"python.linting.pylintArgs": [
        "--load-plugins=pylint_django"
    ]
```