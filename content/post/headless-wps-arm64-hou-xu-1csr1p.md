---
title: headless-wps arm64 后续
slug: headless-wps-arm64-hou-xu-1csr1p
date: '2026-03-19 15:14:37+08:00'
lastmod: '2026-03-19 15:27:05+08:00'
tags:
  - Linux
categories:
  - 技术分享
keywords: Linux
description: >-
  这篇文章讨论了为 headless-wps 项目提供 ARM64 版本镜像的探索历程。核心结论是：在页大小为 4K 的 ARM64 Linux
  内核上，WPS 可以正常运行；但在页大小为 64K 的内核（如某些国产化系统）上，由于 WPS 内置的
  libcef（浏览器组件）无法加载，导致相关功能严重缺失。
toc: true
isCJKLanguage: true
---





有用过 [akkuman/headless-wps: run [wps\](https://linux.wps.cn/) in headless docker](https://github.com/akkuman/headless-wps) 的人可能知道这个一直没有 arm64 版本，此处记录下探索历程（相关内容均来自 [是否有可能提供arm版本的镜像 · Issue #7 · akkuman/headless-wps](https://github.com/akkuman/headless-wps/issues/7)）

## TLDR

4k 页大小内核的 arm64 linux，应该可以正常使用  
64k 页大小内核的 arm64 linux，和 libcef（浏览器） 相关的功能存在严重的功能缺失

另一个需要解决的问题是：arm64 版本只有企业版或者特供版才有 librpc，但这些版本无一例外都只能试用 30 天或需要用激活码激活

由于国产化 arm64 系统，有些内核对齐默认是 64k，所以还没做封装

## 细节

### 是否有可能提供arm版本的镜像

**State:**  open  
**Created by:**  @voyager0003  
**Created at:**  2026-03-09 05:20:49.000 UTC

目前的镜像是x86版本的，在个人的x86服务器上运行没问题，但是在一台信创服务器上跑就报错。  
我注意到wps官方有提供arm版本的deb安装包，不知道有没有可能，提供一版arm版本的镜像，谢谢！  
官方arm版本下载网址：https://365.wps.cn/download365

![Image](https://github.com/user-attachments/assets/c43f47dc-a076-4b5f-a1ae-1fbc21888305)

---

#### Comment by @akkuman at 2026-03-09 05:29:40.000 UTC

没有做arm版本的主要原因是信创系统，比如麒麟v10，有的内核对齐是64k，导致wps内置的比如配置页面这些qtwebkit页面打不开。所以并没有做。

之前测试的结果如上。

不过最近发现chromium已经有版本支持了64k页大小，但这个版本wps似乎不再更新了

---

#### Comment by @akkuman at 2026-03-09 05:30:25.000 UTC

另：wps365我没测试过，不清楚pywpsrpc这个库的支持情况

---

#### Comment by @akkuman at 2026-03-09 05:46:44.000 UTC

看到了这个 https://github.com/timxx/pywpsrpc/issues/121 ，等有空我将测试下 wps365 在64k页arm64上的兼容性，如果可行，我将打包 arm 版本

---

#### Comment by @voyager0003 at 2026-03-09 08:38:45.000 UTC

牛逼

---

#### Comment by @finch-xu at 2026-03-10 06:30:21.000 UTC

同求

---

#### Comment by @akkuman at 2026-03-17 10:10:53.000 UTC

经过我的测试，似乎在 64k页arm64 上依旧无法正常运行

![Image](https://github.com/user-attachments/assets/1aaa5441-199b-41a7-a7db-5c5cf856bd7c)

---

#### Comment by @voyager0003 at 2026-03-18 00:52:33.000 UTC

悲

---

#### Comment by @finch-xu at 2026-03-18 08:08:24.000 UTC

能否用 kata-runtime https://github.com/kata-containers/kata-containers 来做这件事，这是轻量虚拟机，能添加到docker运行时，直接用docker启动，用起来和普通容器差不多，kata虚拟机运行时有自己的内核，可以阻止64k的影响，不知道这样是否可行。  同时kata运行时在麒麟v10系统的安装踩坑查到了一些资料 https://www.cnblogs.com/v-fan/p/18843188 来自网络的博客，可以参考一下。  
我手头没有这种arm机器，比较尴尬，没法测试。  
再次感谢作者制作的镜像，每天处理几百个国内文档，持续跑了几个月了，非常稳定。

---

#### Comment by @akkuman at 2026-03-18 09:32:00.000 UTC

@finch-xu 你说的这个方案我之前考虑过，但是考虑到对用户使用成本太高，没弄

经过测试，实际上是 /opt/kingsoft/wps-office/office6/addons/cef/libcef.so 无法加载。

我尝试去 cef 官网下载了最新的 libcef（因为我记得最新的 chromium 已经支持了 64k pagesize），自己写 dlopen 能加载，但是 wps 运行起来会报错 `./wps: symbol lookup error: /opt/kingsoft/wps-office/office6/addons/kcef/libkbrowserclient.so: undefined symbol: cef_override_path`，无法解决。

---

#### Comment by @akkuman at 2026-03-18 09:43:05.000 UTC

@finch-xu 我也看了另一个相关问题 https://github.com/Cateners/tiny_computer/issues/510 ，我将该处提到的 wps 版本下载下来，然后将 libcef.so 提取出来放进去，发现也是不行的，经过资料查阅，发现是 debian arm64 新版本改成了 4k 对齐，导致问题莫名解决了

---

#### Comment by @finch-xu at 2026-03-18 09:52:33.000 UTC

感谢。等我拿到这种机器的时候也调试一下看看。

---

#### Comment by @akkuman at 2026-03-18 10:06:31.000 UTC

@finch-xu 好像不依赖 libcef.so 也能正常打开 word 文档，我不确定使用 pywpsrpc 是否能行，我有时间编译一个 arm pywpsrpc 试试。不过还有个问题，按照大家说的，应该 arm64 wps 只有企业版有 librpc，需要激活。

其实如果不需要支持 64k 页，我觉得直接换掉应该就行，并不存在无法解决的问题。主要还是国产 arm64 系统有一些默认页大小是 64k，自己测试可以重新编译内核，但是其他人的机器就不敢动了。

4k 页大小的系统应该是没问题

---

#### Comment by @akkuman at 2026-03-19 06:42:08.000 UTC

最新测试：为了防止过多的无用功，此次测试拿别人已经编译好的 https://github.com/kevinhonor/pywpsrpc/blob/master/packages/aarch64/pywpsrpc-2.3.9-cp310-cp310-linux_aarch64.whl

经过测试，wps 能正常打开 word，但是依旧是只要涉及到和浏览器(libcef)有关的，就直接卡死，典型代表比如 word -> pdf

注意：此结论只适用于 64k 页

![Image](https://github.com/user-attachments/assets/2bcf69e8-975b-4e0c-9252-978ad25a298f)

---

#### Comment by @akkuman at 2026-03-19 06:46:21.000 UTC

结论：4k 页大小内核的 arm64 linux，应该可以正常使用  
64k 页大小内核的 arm64 linux，存在较为严重的功能缺失，具体见上

另一个需要解决的问题是：arm64 版本只有企业版或者特供版才有 librpc，但这些版本无一例外都只能试用 30 天或需要用激活码激活

---

#### Comment by @akkuman at 2026-03-19 06:49:31.000 UTC

试用 30 天的解决方案，经过测试，似乎可以从 `rm -rf $HOME/.config/Kingsoft $HOME/.local/share/Kingsoft`​ 和 `license2.dat` 文件下手，经过测试，删除后重新打开就是重新弹出试用，具体由于环境问题打不开设置页面，不知是否奏效

激活码激活：尝试使用网上流传的激活码进行激活，出现几个现象：

1. 提示用于 wps for windows，不可用，但经过抓包，此时没有请求发出（怀疑是内置的黑名单）
2. 提示please check network connect，但经过抓包，此时没有请求发出，不知道问题是什么

---

#### Comment by @akkuman at 2026-03-19 06:56:56.000 UTC

@finch-xu 如果有继续研究的打算，可以加个好友交流下，可以在我的 github 主页找到我的邮箱

---
