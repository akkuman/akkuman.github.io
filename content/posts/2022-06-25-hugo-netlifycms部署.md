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

---

## Netlify CMS 做什么

安装之前我们需要了解一下Netlify CMS是什么。Netlify CMS 和 Forestry 等工具一样，它可以帮助你管理你的git仓库，我们一般的主要用途就是拿它来管理git仓库中的 blog 源文件，它提供了一个友好的界面来帮助你编写你的 blog 源文件，然后后续的 git commit push 它会帮你效劳，你可以拿它来作为CI，自动帮你构建好网站，也可以只使用他的编辑推送功能，把它当作一个管理后台，让其他的CI来帮你做后面的事情。

举个例子，我有一个博客托管在 github pages，拥有自己的CI来进行博客部署，我只需要推送 markdown 博文源文件到指定分支下，即可触发构建，但是我不想每次都在本地写博客，我希望有个简单的方式来让我随时随地在线编辑发布博客，那我就可以使用 Netlify CMS，当然，你也可以使用 github.dev，不过缺点是你需要另外的工具来处理你的图片，因为 github.dev 不支持图片粘贴（相应的插件也无法安装），但是 Netlify CMS 能够通过配置来完成粘贴图片的功能，麻雀虽小五脏俱全。

## 如何部署

可能你看了不少说明文档，但是还是处于不可用的状态。