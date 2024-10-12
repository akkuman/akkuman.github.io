---
categories:
- 工具
date: '2021-12-06T08:09:00.000Z'
showToc: true
tags:
- 工具
- 笔记
title: 将newsletter转为rss

---



相关的开源项目 [https://github.com/leafac/kill-the-newsletter](https://github.com/leafac/kill-the-newsletter)

作者提供了一个网站 [https://kill-the-newsletter.com/](https://kill-the-newsletter.com/) 来提供服务，截至20211119，至少已经提供了两年的服务了，所以稳定性还可

下面就是使用方法了

1. 选择一个你要订阅的newsletter，比如 [https://random-lab.ghost.io/](https://random-lab.ghost.io/)

1. 打开 [https://kill-the-newsletter.com/](https://kill-the-newsletter.com/) ，输入你要给该订阅取的名字，比如我输入 `1000小食报` ，然后点击 `create inbox`

1. 然后会提供给你一个邮箱和一个rss订阅地址

1. 将邮箱地址填入第一步中的订阅邮箱

1. 将rss订阅地址加到你的rss阅读器

一般情况下你会收到的第一个订阅消息是叫你确认订阅，点击确认地址即可

![](https://raw.githubusercontent.com/akkuman/pic/master/notionimg/7d/d6/7dd60ab74cab5a242a2452de7283627f.png)



下面说下原理：

首先需要有个邮服，然后每次创建inbox的时候随机生成一个邮箱，并且将此邮箱的收件箱内容转为rss订阅暴露出来



