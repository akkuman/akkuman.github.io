---
title: mysql8更新密码不成功
date: 2020-11-06 16:57:00
tags:
- Tips
categories:
- Tips
---

表现为按照官方文档 https://dev.mysql.com/doc/refman/8.0/en/resetting-permissions.html 中的说明 **B.3.3.2.3 Resetting the Root Password: Generic Instructions** 无法成功更改
<!--more-->

执行 ALTER USER 'root'@'localhost' IDENTIFIED BY 'MyNewPass'; 还是不能成功更改

进入mysql docker 发现使用 mysql -u root -p 就能登录，但是使用 mysql -h 127.0.0.1 -P 3306 -u root -p 不能登录，怀疑是本地登录和网络登录配置不同。

你可以先看看mysql的user表

1
mysql> select host,user,authentication_string from mysql.user;
host: 允许用户登录的ip，%表示可以远程，localhost表示本机；

user:当前数据库的用户名；

我这里是需要远程登录的密码改掉，所以执行 ALTER USER 'root'@'%' IDENTIFIED BY 'MyNewPass'; 即可