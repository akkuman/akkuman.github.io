---
title: safety classifier 解决方案
slug: safety-classifier-solution-ncrdm
date: '2026-09-24 16:46:28+08:00'
lastmod: '2026-09-24 16:49:31+08:00'
tags:
  - 工具
categories:
  - 技术分享
keywords: 工具
description: >-
  这篇文章说明了通过网关（如 NewAPI）的兼容接口使用 Claude Code 时，可能遇到 `The safety classifier is
  temporarily unavailable` 报错的原因和临时解决方案。
toc: true
isCJKLanguage: true
---





如果你最近通过网关（比如NewAPI）的兼容接口使用 claude-code

可能会遇到这个问题

```yaml
The safety classifier is temporarily unavailable
```

核心原因是：Claude Code 的 Bash 安全分类器通常不是走你 /model 里选的主对话模型，而是一条单独的安全判定链路

普通对话走 messages 路径，网关支持，所以正常；  
Bash 分类器走另一种请求形态或端点，网关没完整代理，所以持续报 temporarily unavailable；  
结果是 auto 模式下 Bash / WebSearch 等动作被卡住。

claude 官方链接可查看

[Auto mode classifier request charges - Claude Code Docs](https://code.claude.com/docs/en/auto-mode-classifier-billing)

临时**解决方案**：

增加环境变量

```yaml
export CLAUDE_CODE_AUTO_MODE_SERVER=0
```

## Reference

[(1) X 上的 Rainman：“给用 API Key / 自建网关跑 Claude Code 的同学提个醒： 如果你在 auto 模式下遇到： Bash safety classifier temporarily unavailable 并且反复重试也恢复不了，那它可能不是“服务过载”，而是调用链路本身不通。 核心原因是：Claude Code 的 Bash 安全分类器通常不是走你 /model” / X](https://x.com/0xdeusyu/status/2068910660482990215)
