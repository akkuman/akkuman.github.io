---
title: golang qt中的自定义Object
date: 2020-12-23 03:04:34
toc: true
tags:
- 问题解决
categories:
- 问题解决
---



这篇文章主要记录golang qt使用中的自定义Object怎么编写以及singal使用

<!--more-->

- wk.go

```
package wk

import (
	"fmt"
	"sync"

	"github.com/therecipe/qt/core"
	"github.com/therecipe/qt/gui"
	"github.com/therecipe/qt/network"
	"github.com/therecipe/qt/webkit"
)

// ScreenshotConfig screenshot config
type ScreenshotConfig struct {
	ID      string
	URL     string
	Width   int
	Height  int
	Quality int
	Format  string
	UA      string
}

// ScreenshotObject qt object
type ScreenshotObject struct {
	core.QObject

	_ func(config ScreenshotConfig) `signal:"startScreenshot,auto"`
	_ func(id string, data []byte)  `signal:"finishScreenshot,auto"`

	Map sync.Map
}

// StartScreenshot start screenshot slots
func (s *ScreenshotObject) startScreenshot(config ScreenshotConfig) {
	s.GetScreenshot(config)
}

// FinishScreenshot finish screenshot slots and store data to map
func (s *ScreenshotObject) finishScreenshot(id string, data []byte) {
	s.Map.Store(id, data)
}

// GetScreenshot get a snapshot for website
func (s *ScreenshotObject) GetScreenshot(config ScreenshotConfig) {
	...
	page.MainFrame().Load(qURL)

	page.ConnectLoadFinished(func(bool) {
        ...
		s.FinishScreenshot(config.ID, data)
		fmt.Println(data)
	})
}

```

- main.go

```
package main

import (
	"os"

	"github.com/akkuman/webkit-screenshot/wk"
	"github.com/therecipe/qt/widgets"
)

func main() {
	os.Setenv("QT_QPA_PLATFORM", "offscreen")

	app := widgets.NewQApplication(len(os.Args), os.Args)
	screenshotObj := wk.NewScreenshotObject(nil)

	go screenshot(screenshotObj, "https://www.baidu.com")

	app.Exec()
}

func screenshot(obj *wk.ScreenshotObject, url string) {
	config := wk.ScreenshotConfig{
		ID:      "xxxx",
		URL:     url,
		Width:   1920,
		Height:  1080,
		Quality: 50,
		Format:  "jpg",
		UA:      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A",
	}
	obj.StartScreenshot(config)
}

```

看到上面两段代码截取，golang qt里面使用 `Connect[singalName]` 连接 singal，在struct tag中加上auto代表可以把该结构体方法同名的方法自动Connect上去。

这里需要注意一点，auto 的方法名不要首字母大写，会与 qtmoc 自动生成的有冲突。

该程序的目的是需要在外部通过 goroutine 调用组件进行一系列方法。

这里需要十分注意的一点是，qt 组件必须在 qt 程序主消息循环中创建，不能在 goroutine 中创建，否则样例中的 `page.ConnectLoadFinished` 将不会被执行。

拿这个例子来说，就是 `screenshotObj := wk.NewScreenshotObject(nil)` 必须在主线程中，而不能用 goroutine 执行。