---
title: 一行命令删除空的docker images
date: 2021-03-03 10:14:17
toc: true
tags:
- life
categories:
- life
---


有些时候我们 docker build 镜像会出现很多 `<none>` 的残余 cache image 在我们的系统中。

<!--more-->

可以使用 awk 来完成一行命令删除空的docker images

```bash
sudo docker images | awk '{if($1=="<none>") print $3}' | xargs sudo docker rmi
```