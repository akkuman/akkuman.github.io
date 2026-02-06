---
title: 迁移git仓库已有文件到 lfs
slug: migrate-existing-files-in-git-repository-to-lfs-z1wjust
date: '2026-02-05 09:58:59+08:00'
lastmod: '2026-02-06 09:43:38+08:00'
tags:
  - Linux
  - Git
categories:
  - 技术分享
keywords: Linux,Git
description: >-
  本文介绍了如何将Git仓库中的大文件迁移到Git LFS（Large File
  Storage）中。核心方法是利用`.gitattributes`文件定义需要追踪的大文件，然后通过`git lfs migrate import
  --everything
  --fixup`命令进行迁移。但直接使用`--fixup`可能无效，因为该命令依赖历史提交中的`.gitattributes`文件。解决方案是先用`git-filter-repo`工具将`.gitattributes`文件注入到所有历史提交中，再执行LFS迁移。文章还提供了备选方案：通过解析`.gitattributes`文件生成`--include`参数列表进行迁移，但此方法可能无法处理标签。最终推荐的方法是先注入`.gitattributes`到历史记录，再使用`--fixup`完成迁移。
toc: true
isCJKLanguage: true
---





## 问题背景

我已经有了一个 .gitattributes 文件，我希望将仓库中的大文件全部重写到 lfs 上

.gitattributes 文件样例如下：

```plaintext
assets/geolite2-asn-ipv4.mmdb filter=lfs diff=lfs merge=lfs -text
assets/geolite2-asn-ipv6.mmdb filter=lfs diff=lfs merge=lfs -text
assets/qqwry.dat filter=lfs diff=lfs merge=lfs -text
assets/zxipv6wry.db filter=lfs diff=lfs merge=lfs -text
```

## 最终解决方案（TLDR）

```bash
# 首先安装 git-filter-repo
uv tool install git-filter-repo
# 然后将 .gitattributes 添加到每个提交
HASH=$(git hash-object -w "$(pwd)/.gitattributes")
git filter-repo --force --commit-callback "commit.file_changes.append(FileChange(b'M', b'.gitattributes', b'${HASH}', b'100644'))"
# 然后使用 --fixup 根据 .gitattributes 文件转换为 lfs 格式
git lfs migrate import --everything --fixup
```

注意：该方案仅适用于 gitattributes 文件中不包含 exclude 规则的情况

## 解决过程

​`git lfs migrate import`​ 有一个 `--fixup` 参数

根据官方的解释：

```plaintext
--fixup Infer --include and --exclude filters on a per-commit basis based on the .gitattributes files
           in  a  repository.  In practice, this option imports any filepaths which should be tracked by Git LFS
           according to the repository´s .gitattributes file(s), but aren´t already  pointers.  This  option  is
           incompatible with explicitly given --include, --exclude filters.
```

似乎看起来是我们想要的作用，但是我使用后发现并没有重写，原因在这：[是否可以使用 `lfs migrate import --fixup` 将整个仓库追溯性地转换为 LFS？ · 问题 #3543 · git-lfs/git-lfs --- Is it possible to use lfs migrate import --fixup to retroactively convert an entire repository to LFS? · Issue #3543 · git-lfs/git-lfs](https://github.com/git-lfs/git-lfs/issues/3543)  

> --fixup 工作原理是使仓库在每个历史节点上都与其 `.gitattributes` 文件保持一致。由于你是在历史节点上的最新节点添加 .gitattributes 文件，因此 git lfs migrate --fixup 大部分时间都不起作用。
>
> 我认为你可以做两件事来代替：
>
> 1. 你可以不使用 `--fixup`​ ，而是明确指定 `--include`​ 和 `--exclude`​ 参数，让 Git LFS 为你创建 \` `.gitattributes`​ 文件。你提到你不想使用这个选项，但实际上应该没问题：Git LFS 会修改你的 \`.gitattributes\` 文件，但不会进行冗余修改（例如，如果我们想要添加的条目已经存在，那么 Git LFS 将不会执行任何操作）。
> 2. 或者，您可以使用 git rebase 将引入 .gitattributes 的提交提前到历史记录中， 然后运行 ​​ git lfs migrate --import --everything 。由于您引入的 .gitattributes 更改会更早出现，因此 --fixup 将转换您想要的文件。

既然上面的不起作用，那就只能使用 awk + xargs 来实现了

```bash
cat .gitattributes | grep 'filter=lfs diff=lfs merge=lfs' | awk '{print($1)}' | xargs -I{} git lfs migrate import --include="{}" --everything
```

但是他有个问题，不会迁移 tag

所以参考如下链接，给出一个最终方案

- https://github.com/git-lfs/git-lfs/issues/3543#issuecomment-947883998
- https://github.com/git-lfs/git-lfs/issues/3543#issuecomment-1019633715
- https://github.com/git-lfs/git-lfs/issues/3543#issuecomment-2380668083

```bash
# 首先安装 git-filter-repo
uv tool install git-filter-repo
# 然后将 .gitattributes 添加到每个提交
HASH=$(git hash-object -w "$(pwd)/.gitattributes")
git filter-repo --force --commit-callback "commit.file_changes.append(FileChange(b'M', b'.gitattributes', b'${HASH}', b'100644'))"
# 然后使用 --fixup 根据 .gitattributes 文件转换为 lfs 格式
git lfs migrate import --everything --fixup
```
