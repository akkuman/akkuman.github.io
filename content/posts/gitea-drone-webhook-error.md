---
title: gitea drone webhook触发失败 
date: 2020-12-08 04:48:09
toc: true
tags:
- 问题解决
categories:
- 问题解决
---



我们知道在Drone中激活gitea仓库后会在该仓库下生成一个webhook，但是当我们推送时却无事发生，测试推送时出现错误

```
Delivery: Post "http://ci.test.com/hook?secret=zMIxs0On0e7FOpgt6RImNrlgD6Bu4OQr": read tcp 172.27.0.3:56812->10.20.156.4:80: i/o timeout
```

<!--more-->

该错误有两种原因

1. 超时过短
2. Drone无法访问到该仓库的 `.drone.yml` 文件

针对第一种问题，一般是给 gitea 增加 `DELIVER_TIMEOUT` 即可

针对第二个问题，可能分为两种几种情况

1. 仓库中没有这个文件，这个直接在仓库中创建一个即可
2. 仓库中有这个文件但是访问不到，可能是你的 nginx 设置了策略，以 `.` 开头的文件无法访问

解决方案：
删除掉 nginx 配置中类似于下面的策略

```
location ~ /\.(?!well-known) {
        deny all;
}
```

该策略的作用是当用户访问以 `.` 开头的文件则返回403