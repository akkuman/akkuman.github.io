---
title: 教程视频如何压制体积更小
date: 2018-11-07 20:46:00
tags:
- Tips
categories:
- Tips
---


录制完了教程视频，如何压制会在不影响观看的情况下，使得到的视频体积较小呢？

<!--more-->

以下是使用x264进行压制，如果是使用小丸工具箱请自定义命令

```
--crf 28 --level 4.1 --ref 3 --bframes 13 --keyint 600 --qcomp 0.8 --b-adapt 1 --scenecut 30 --me umh --merange 32 --subme 10 --trellis 2 --aq-mode 3 --aq-strength 1.0 --psy-rd 0.6:0.0 --direct auto --partitions all
```

音频建议压制为32Kbps或以下，教程不需要太好的音质。
