---
layout: blog
title: hugo+NetlifyCMS部署
date: 2022-06-25T08:02:47.978Z
showToc: true
draft: false
description: 本文记录了怎么为已经存在CI(Github Action)的hugo博客添加 Netlify CMS
cover:
  # only hide on current single page
  hidden: false
---
网上的博客很多关于Netlify CMS的部署都是使用了Netlify的服务，因为我自己的博客已经使用了GithubAction作为CI来自动部署，我的博客源文件放在hugo分支下，对hugo分支commit会触发GithubAction，然后使用进行网站构建并推送到master分支下，并且自定义域名是使用的其他域名提供商来解析的，本文主要是记录一下在这种情况下怎么为博客添加NetlifyCMS