---
title: 博客园某开源主题暗藏私货？
date: 2020-05-12 22:14:00
tags:
- 前端
- 生活
categories:
- 生活
---


2020/05/13 14:50更新

在评论的驱使下我仔细去看了下，有几处确实用到了后端接口

```js
  loadBlogTalk: (page) => {
    return forwardXmlJsonp("https://ing.cnblogs.com/u/" + blogConst.blogAcc + "/" + page, parseTalkList);
  },
```

```js
  loadBlogSearch: (keyword) => {
    return forwardXmlJsonp("https://zzk.cnblogs.com/s/blogpost?w=" + encodeURI("blog:" + blogConst.blogAcc + " " + keyword), parseSearchKeyWord);
  },
```

```js
  loadFollowers: (page) => {
    let url = "https://home.cnblogs.com/u/" + blogConst.blogAcc + "/relation/followers/";
    if (page && page > 1) {
      url += "?page=" + page;
    }
    return forwardXmlJsonp(url, parseFollowers);
  },
```

这三个接口是走的php后端的api，理由是能自洽的，因为涉及到不同子域了，存在跨站请求，所以需要第三方后端来进行处理

不过百度统计我还是不太能理解

----------------------------------------

2020/05/12 22:14

**首先说好本文只是我个人的猜测，如果有不对的地方请及时指正**

## 背景

前些天朋友介绍，看到一个博客园主题，主题的思路很棒，具体怎么棒不表，只是后来看了看源码，发现了一些秘密的东西。

源码地址[https://github.com/cjunn/cnblog_theme_atum](https://github.com/cjunn/cnblog_theme_atum)

## 发现

### 神秘的后端请求

首先是这个主题会向主题作者的php服务器发送请求

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/e6d962c441b46203d9ff44042a72091c..png)

这里我们可以看到是返回一个callback，这一般是解决跨域所采用的jsonp技术

那么jsonp的具体原理是啥？

#### jsonp原理

因为浏览器跨域机制的存在，如果在对方接口服务器上面并没有做cors相关的操作，那么是请求不到ajax接口数据的，jsonp技术应运而生

浏览器是可以引入外域的js的，并且外域上不需要做任何跨域相关的设置，引入外域js后就可以调用该js里面的函数，所以在接口上传递一个callback，比如

```
<script src="http://a.com/a.php?callback=ttt"></script>
```

然后那边返回一个js，js的内容为

```
ttt({'a': 1, 'b': 2})
```

那么调用ttt函数即可获得这个json数据

### 后端请求问题点

是不是到现在为止你还是觉得，好像没什么问题啊，他返回一下好像也没问题啊？

但是试想一个，这个callback他是可以在后端任意替换的，比如给你加个js获取你的一些信息，甚至还可以控制你的浏览器一些行为，比如帮他点击一个啥啥啥，可以了解一下Beef

### 神秘的加密字符串

我看了这个主题占用cpu和内存比较低，所以花了几分钟时间翻了下源码，发现了一些奇怪的东西

我在找上面所说的php请求的时候发现了这个

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/a9e0c0780f708158affbf79440bd7837..png)

然后跟进去

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/9f5b327e371f102cf1c031dfe815c28e..png)

继续跟

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/df9a7160eb303f31236c171286aabf79..png)

有一串加密的东西

看名称像是百度统计，但是你为什么加个密，跟进这个加密函数看看

```
/**
 *
 *  Base64 encode / decode
 *  http://www.webtoolkit.info
 *
 **/


  // private property
let _keyStr = ""
_keyStr += "AByz0r4wxs";

// public method for encoding
let encode = function (input) {
  var output = "";
  var chr1, chr2, chr3, enc1, enc2, enc3, enc4;
  var i = 0;

  input = _utf8_encode(input);

  while (i < input.length) {
    chr1 = input.charCodeAt(i++);
    chr2 = input.charCodeAt(i++);
    chr3 = input.charCodeAt(i++);

    enc1 = chr1 >> 2;
    enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
    enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
    enc4 = chr3 & 63;

    if (isNaN(chr2)) {
      enc3 = enc4 = 64;
    } else if (isNaN(chr3)) {
      enc4 = 64;
    }

    output = output +
      _keyStr.charAt(enc1) + _keyStr.charAt(enc2) +
      _keyStr.charAt(enc3) + _keyStr.charAt(enc4);
  } // Whend

  return output;
} // End Function encode
_keyStr += "KLMCDEtuTUVWX12NOPQk";


// public method for decoding
let decode = function (input) {
  var output = "";
  var chr1, chr2, chr3;
  var enc1, enc2, enc3, enc4;
  var i = 0;

  input = input.replace(/[^A-Za-z0-9\+\/\=]/g, "");
  while (i < input.length) {
    enc1 = _keyStr.indexOf(input.charAt(i++));
    enc2 = _keyStr.indexOf(input.charAt(i++));
    enc3 = _keyStr.indexOf(input.charAt(i++));
    enc4 = _keyStr.indexOf(input.charAt(i++));

    chr1 = (enc1 << 2) | (enc2 >> 4);
    chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
    chr3 = ((enc3 & 3) << 6) | enc4;

    output = output + String.fromCharCode(chr1);

    if (enc3 != 64) {
      output = output + String.fromCharCode(chr2);
    }

    if (enc4 != 64) {
      output = output + String.fromCharCode(chr3);
    }

  } // Whend

  output = _utf8_decode(output);

  return output;
} // End Function decode
_keyStr += "lmnopqYZabcdef";


// private method for UTF-8 encoding
let _utf8_encode = function (string) {
  var utftext = "";
  string = string.replace(/\r\n/g, "\n");

  for (var n = 0; n < string.length; n++) {
    var c = string.charCodeAt(n);

    if (c < 128) {
      utftext += String.fromCharCode(c);
    } else if ((c > 127) && (c < 2048)) {
      utftext += String.fromCharCode((c >> 6) | 192);
      utftext += String.fromCharCode((c & 63) | 128);
    } else {
      utftext += String.fromCharCode((c >> 12) | 224);
      utftext += String.fromCharCode(((c >> 6) & 63) | 128);
      utftext += String.fromCharCode((c & 63) | 128);
    }

  } // Next n

  return utftext;
} // End Function _utf8_encode
_keyStr += "35RSJFGHIvgh";
// private method for UTF-8 decoding
let _utf8_decode = function (utftext) {
  var string = "";
  var i = 0;
  var c, c1, c2, c3;
  c = c1 = c2 = 0;

  while (i < utftext.length) {
    c = utftext.charCodeAt(i);

    if (c < 128) {
      string += String.fromCharCode(c);
      i++;
    } else if ((c > 191) && (c < 224)) {
      c2 = utftext.charCodeAt(i + 1);
      string += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
      i += 2;
    } else {
      c2 = utftext.charCodeAt(i + 1);
      c3 = utftext.charCodeAt(i + 2);
      string += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
      i += 3;
    }

  } // Whend

  return string;
} // End Function _utf8_decode
_keyStr += "ij6789+/=";

export default {
  i: (message) => {
    return encode(message);
  },
  o: (ciphertext) => {
    return decode(ciphertext);
  },
}
```

这个函数自己跑一下，跑出来是 `https://hm.baidu.com/hm.js?ae80cc662109a34c868ba6cbe3431c8d` 这个百度统计地址

然后在初始化的时候，也就是你每次进网站的时候

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/aa69a015753464ad0ee3d37295d2e813..png)

每次进网站调用这个函数 initBaiduCount()

并且加了个路由守卫调用 pushBaiduCount()

可能有的人不理解路由守卫是什么，路由守卫就是一个hook钩子，在你每次进入或离开路由，或者说该网站的页面时调用，比如这里是进入一个新路由的时候就调用一下，跟进去看看

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/39be8918530f841982360988881746ce..png)

这里是插入了百度统计代码

### 我的疑惑点

我不太懂百度统计是什么东西，一直认为就是一个管站点流量和访问量的，也不知道有啥其他东西

我说下我觉得可疑的点

我姑且认为是为了给自己的博客进行统计，但是这其中为什么大费周章去加密解密，这个我不太理解

还有的是这个加密的js去掉了后缀js，这样github就没法检索分析代码了，不把代码down下来应该是只能硬找

我看了下，其实并没有用到自建php服务器上的东西，最开始以为是反代博客园转化为接口，但是我看了下请求，全都是只有callback，返回的一个字符串，我实在想不到是有什么必要进行这个操作，目前看起来是没有价值的

所以问题来了：

1. 添加了百度统计，但是大费周章加解密，看起来并不是让用户可自定义的项或者不是大大方方给人看的东西？
2. 这个php服务器主要用处是什么？目前的callback看起来是毫无意义的，还是真像我所想的，方便以后做一些事情？