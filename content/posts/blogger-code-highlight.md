---
title: blogger添加代码高亮
date: 2018-05-26 22:11:00
tags:
- Tips
categories:
- Tips
---

blogger(blogspot)自带的是没有代码高亮的，我们可以用下面的方法添加代码高亮。  

<!--more-->

<!--more-->

首先我们打开blogger(blogspot)后台，然后点击`主题背景-->修改html`，然后在弹出的窗口右上角搜索(search)`</head>`，然后在`</head>`之前添加如下代码：
```html
<!-- highlight.js Additions START -->
<link href='//cdn.bootcss.com/highlight.js/9.12.0/styles/atom-one-light.min.css' rel='stylesheet'/>
<script src='//cdn.bootcss.com/highlight.js/9.12.0/highlight.min.js'/>
<script>hljs.initHighlightingOnLoad();</script>
<!-- highlight.js Additions END -->
```
其中版本号`9.12.0`和js以及css都是可以自行更改的，我只是选了我这个时间上最新的版本，并且选了比较适合本人blogger的配色，这些都是可以自行更改的。