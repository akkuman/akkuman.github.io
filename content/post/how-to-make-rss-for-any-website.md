---
title: "如何自己烧制全文RSS（打造自己RSS源）"
date: 2017-09-07 19:15:00
tags:
- Tips
categories:
- Tips
---

## 烧制RSS源
<!--more-->
1. 到[Feed43](http://feed43.com/)注册一个账号，虽说不注册也能用，但是为了方便修改自己烧制的RSS，最好还是注册一个账号来管理
2. 到主页点击Create new feed
3. 输入网址点击reload

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/51bba122916b22fcd97d23cb3db33cf0..png)

4. 可以看到请求的html中1处是文章的定位处，我们针对这个写出2处的代码就可以了

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/8722a7429679566e19aad31421e4edc3..png)

下面是2处的具体代码
```
//2处的代码
<tr>{*}
<td>{%}</td>{*}
<td{*}align="left"><a{*}href="{%}"{*}target="_blank"><font{*}color="#F2753F">{*}
{%}</font></a></td>{*}
<td>{%}</td>{*}
</tr>{*}
```
**在feed43中，我们会用到两种代码块：`{%}`和`{*}`，其中`{%}`替换你想获取的内容，`{*}`用来省略无关代码**

5. 填写规则完成后点击`Extract`，可以看到下面抓取出了具体的列表

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/c1c68ee33126caa4ce3b07f5053f7567..png)

6. 把具体要展示的信息变量填写好

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/4a283f1f711f69e7be08db4d310cc1b8..png)

7. 点击`Preview`即可获取feed地址`http://feed43.com/3772386342045020.xml`

## 获取全文输出feed
这里推荐两个网址，直接把上面我们得到的feed的地址填入即可获取全文烧制的RSS
- [Full Rss](https://www.freefullrss.com/)
- [FeedSoSo](http://www.feedsoso.com/)