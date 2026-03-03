---
title: 为什么我的 powershell 启动这么慢
slug: why-is-my-powershell-starting-so-slowly-12hzjt
date: '2026-03-03 09:37:13+08:00'
lastmod: '2026-03-03 09:46:35+08:00'
tags:
  - windows
categories:
  - 技术分享
keywords: windows
description: >-
  本文分析了Windows
  Terminal中PowerShell启动缓慢的问题，发现主要原因是加载个人配置文件（profile.ps1）耗时过长。通过逐步排查，确定问题出在conda初始化脚本上。解决方案包括：注释掉conda相关代码以加快启动速度，或参考社区讨论中的优化方法。
toc: true
isCJKLanguage: true
---





## 背景

我的 windows terminal 每次启动 powershell 都很慢，并且会打印这样一行

```bash
Loading personal and system profiles took 1704ms.
```

## 排查

首先我们不加载任何内容，在 cmd 中执行 `pwsh -NoProfile`，powershell 立即启动，并且没有打印上面的日志

在 powershell 中执行 `$PROFILE`​，找到 profile 所在文件夹，然后找到同级目录下的 `profile.ps1`

我的内容如下

```powershell
Import-Module -Name "F7History"
#region conda initialize
# !! Contents within this block are managed by 'conda init' !!
If (Test-Path "D:\Applications\Scoop\apps\miniconda\current\Scripts\conda.exe") {
    (& "D:\Applications\Scoop\apps\miniconda\current\Scripts\conda.exe" "shell.powershell" "hook") | Out-String | ?{$_} | Invoke-Expression
}
#endregion
```

注释掉 F7History，似乎没有改善

注释掉 conda 相关，启动 powershell，`Loading personal and system profiles took 1704ms.` 这一行没有打印了，并且感觉启动变快了。修改 profile 来记录一下

```powershell
$global:ProfileStartTime = Get-Date

... 原有内容

$profileLoadTime = (Get-Date) - $global:ProfileStartTime
Write-Host "⚡ Profile 加载耗时: $($profileLoadTime.TotalMilliseconds.ToString('N0')) ms" -ForegroundColor Cyan
```

可以看到注释掉 conda，确实变快了

## 解决方案

1. 注释掉 conda
2. 或者你可以参考 [conda init powershell slows shell startup immensely. · Issue #11648 · conda/conda](https://github.com/conda/conda/issues/11648) 中的解决方案
