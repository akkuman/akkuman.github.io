---
title: docker build出现交互式时区设置解决
date: 2021-03-03 10:09:59
toc: true
tags:
- life
categories:
- life
---


当我们基于ubuntu镜像构建Docker的时候，偶尔会出现 `please select the geographic area in which you live.` 让我们选择时区

<!--more-->

原因是ubuntu 18.04后没有默认的系统时区，安装tzdata会出现交互式时区设置

## 解决方案

Dockerfile 开头加上

```yaml
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai
```
