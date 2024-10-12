---
title: git彻底删除或变更子模块
date: 2019-05-23 14:30:00
tags:
- git
categories:
- git
---

今天遇到一个很怪的问题，我想把我的一个子模块切换到另一个上游，我按照网上的方法删除子模块然后新建后，这个子模块依旧跟踪着我先前的上游。自己摸索了一下，可能方法比较傻，不过是可行的，希望能给大家一些帮助。

<!--more-->

1. 使原先子模块不被版本控制（先把子模块从版本控制系统移除）

```
git rm --cached /path/to/files
```

2. 删除子模块目录

```
rm -rf /path/to/files
```

3. 修改 .gitmodules，移除这个 submodule

```
-[submodule "themes/next"]
-	path = themes/next
-	url = https://github.com/theme-next/hexo-theme-next.git
```

3. 修改 `.git/config` 内容，把需要删除的 submodule 配置项删除
4. 修改 `.git/modules` 文件夹内容，把你想要删除的子模块目录删除（这项十分重要，或者你知道怎么修改也可以修改，不然导致的后果就是你改过来的同名子模块依然跟踪着之前的分支，git pull 也没法拉取你在 .gitmosules 中新定义的上游地址）
5. 后面再按照普通的方法添加子模块即可

一些子模块的操作可以参见[Git Submodule 用法筆記](https://blog.chh.tw/posts/git-submodule/)