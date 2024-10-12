---
title: chrome SwitchyOmega 无法代理本机
date: 2020-10-28 09:25:00
tags:
- Tips
categories:
- Tips
---


比如使用burp，设置代理后，就算把 不代理的地址列表 中的全部去掉，如果流量是到本机，依旧无法代理

<!--more-->

解决方案：

不代理的地址列表中加上 <-loopback>

来源：

https://bugs.chromium.org/p/chromium/issues/detail?id=899126#c17