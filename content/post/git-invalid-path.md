---
title: git出现Invalid path
date: 2019-09-12 16:39:00
tags:
- Tips
categories:
- Tips
---

今天换了电脑，我直接把整个仓库从电脑A复制到了电脑B，包括仓库下面的 `.git` 文件夹。

修改代码后我执行了一下 `git add .`

出现了一个报错

```
fatal: Invalid path 'D:/Studio/Repo': No such file or directory
```

看了下，这不是我上一台电脑的仓库目录吗。

我在网上找了一下，并没有找到一个比较好的解决方案。

想了想，git仓库配置都是在 `.git` 文件夹下面，下面肯定有配置文件。

直接拿文本搜索工具搜索了一下，我这里使用的 `grep`

```
λ grep -rn "D:/Code" ./.git
./.git/config:6:        worktree = D:/Studio/Repo/theproject
```

可以看到config里面有这个配置，直接把这个 worktree 改成你现在项目所在的位置即可解决问题
