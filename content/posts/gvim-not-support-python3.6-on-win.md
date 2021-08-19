---
title: "windows下使用gvim不支持python3.6问题解决"
date: 2017-11-28 22:29:00
tags:
- Tips
categories:
- Tips
---

在用户目录下C:\Users\Administrator\新建vim配置文件夹vimfiles，然后该文件下建立一个文件vimrc  

vimrc内容：
```
set pythonthreedll=python36.dll
```

但是前提是你的Python文件夹在环境变量PATH内

比如

我装的gvim是的32位的，那么python也需要是32位
环境变量配置PATH中存在Python36的安装目录