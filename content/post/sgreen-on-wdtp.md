---
title: "为静态博客生成器WDTP移植了一款美美哒主题"
date: 2017-06-13 13:08:00
tags:
- 前端
categories:
- 开发
---

## 前言
关于这个主题的移植后公布，我已经联系了主题作者并取得同意，这个主题是[一夜涕](http://yiyeti.cc/)所写的[Sgreen](http://yiyeti.cc/zheteng/132.html)，预览图见下

<!--more-->

## 关于WDTP
就是一个很方便很便携很快速的cpp编写的带gui跨平台的开源的静态博客生成器，软件作者更新记录在[V站](https://www.v2ex.com/t/338138)可以找到,[软件官网](http://underwaysoft.com/works/wdtp/index.html)也可以找到

## 主题预览图

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/6ed3787f957975a62f004c6cbc7ffff9..png)


## DEMO
[Demo](http://akkuman.pancakeapps.com/)

## 功能
- 内置两种颜色的css，根据白天夜晚控制进行替换
- WDTP预览采用的ie内核，Qplayer的player.js文件会一直爆语法错误，增加了一段js用来判断是否是ie内核的浏览器，如果不是ie内核才会加载player.js
- 数遍移植链接抖动特效
- 鼠标移至头像与社交图标会有旋转效果
- Qplayer音乐播放器
- zoom图片效果
- 复制时会出现版权弹窗提示，复制的文本也带有版权信息
- 弹窗采用sweetalert
- 手机端的适配

## 安装说明
安装WDTP并新建项目后点击中间齿轮导入外部主题，然后在右侧属性面板选择主题Sgreen
然后根节点新建三个文件，名称分别为archives,about,links并在右侧属性面板把三个文档设置为隐身模式（也就是不参与整站博客目录生成，但是html文件都存在）
点击上方眼睛图标可以进入编辑界面，编辑界面右键-扩展标记-发布记录，可以增加时间归档标记
更多玩法可以自己发掘或者软件帮助看说明

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/facdd70464c2c0cbe9c8b383fc0f2977..png)

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/4f371c18ebb24f2247c4278a1b1dfa97..png)

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/da708e3e14d3cf62b2b56a5d5c5b7a9d..png)

## 主题下载地址
[点击我下载](http://git.oschina.net/Akkuman/wdtpSgreen/raw/master/wdtpSgreen.wtpl)