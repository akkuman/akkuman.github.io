---
title: "size_t和unsigned int区别"
date: 2017-12-03 22:46:00
tags:
- 笔记
categories:
- 笔记
---

size_t和unsigned int有所不同,size_t的取值range是目标平台下最大可能的数组尺寸,一些平台下size_t的范围小于int的正数范围,又或者大于unsigned int.最典型的,在x64下,int还是4,但size_t是8.这意味着你在x64下最大可能开辟的数组尺寸是2^64.如果你使用int或者unsigned int,那么在x64下如果你的代码中全部使用uint作为数组的尺寸标记,那么你就会失去控制 `2^32` 尺寸以上的数组的机会.虽然现在在x64上开辟一个大于 `2^32` 大小的连续数组依然是个不大可能的事情,但是..........  

“640K内存对于任何人来说都足够了”----比尔盖茨


链接：https://www.zhihu.com/question/24773728/answer/28920149
