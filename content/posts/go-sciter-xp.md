---
layout: blog
title: xp 兼容的 go-sciter
date: 2022-09-19T18:02:47.978Z
showToc: true
draft: false
description: 本文说明了如何将 go-sciter 兼容 xp
cover:
  # only hide on current single page
  hidden: false
---

现在的 [https://github.com/sciter-sdk/go-sciter](https://github.com/sciter-sdk/go-sciter) 项目想要兼容 xp 已经十分困难

我写了一个例子，地址在 [https://github.com/akkuman/go-sciter-xp](https://github.com/akkuman/go-sciter-xp)， 旨在提供一个兼容 xp 的 go-sciter 样例。

感兴趣的可以将项目克隆下来后进行自己的开发

- - -

## 环境依赖

- go 1.10
- https://github.com/golang/dep 工具
- [sciter-sdk 4.4.4.7](https://github.com/c-smile/sciter-sdk/tree/c7d48627e8716bb803bebf2c74f54ab2dd0d7c51)

### 关于环境的说明

上面几个环境务必保持相同

#### sciter-sdk 为什么使用 4.4.4.7 版本

我使用 rundll32 在 xp 上调用 sciter.dll，最高只能支持到这个版本

我已经将这个版本的 dll 放到本仓库了

- [sciter-4.4.4.7-normal.dll](https://github.com/akkuman/go-sciter-xp/blob/master/sciter-4.4.4.7-normal.dll) 来自 https://github.com/c-smile/sciter-sdk/tree/c7d48627e8716bb803bebf2c74f54ab2dd0d7c51/bin.win/x32
- [sciter-4.4.4.7-skia.dll](https://github.com/akkuman/go-sciter-xp/blob/master/sciter-4.4.4.7-skia.dll) 来自 https://github.com/c-smile/sciter-sdk/tree/c7d48627e8716bb803bebf2c74f54ab2dd0d7c51/bin.win/x32skia

这两个版本的区别是，skia 使用 skia 进行渲染，并且体积大一些

#### 为什么使用 go1.10

根据 https://github.com/golang/go/issues/23380 ，golang version 1.10 是最后一个支持xp的版本，后续的版本不对兼容性做保证

关于gui库
- govcl: go ver>=1.9.2 : 优势： 可以使用lazarus或delphi等界面设计软件直接画界面
- go-sciter: go ver>=1.10：优势：使用了完整的web技术栈，但是肯定不能与浏览器的兼容性相比，不过写界面应该是够了，目前使用sciter的明星产品：rustdesk
- gotk3：go ver>=1.8 gtk绑定
- qt：支持1.10，但是安装较为复杂

考虑到美观和兼容的问题，建议使用 go-sciter

注意，go1.10不支持go module，需要使用gopath的模式

#### 为什么使用dep

dep 已经是一个不再维护的东西，已经被 go module 取代，但是 module 到 go1.13 才有支持，所以我们使用 dep

文件请查看 [Gopkg.toml](https://github.com/akkuman/go-sciter-xp/blob/master/Gopkg.toml)

关于 Gopkg.toml 的解释

```toml
[[constraint]]
  # 后续的版本合并了新版api（4.4.7.0+），xp可用的sciter-sdk版本最高到 4.4.4.7（https://github.com/c-smile/sciter-sdk/commit/c7d48627e8716bb803bebf2c74f54ab2dd0d7c51）
  # 见 https://github.com/sciter-sdk/go-sciter/issues/297 与 https://github.com/sciter-sdk/go-sciter/commit/99cd4de65a26163ff93872ef7bba888b479081dc
  # 所以需要降版本
  revision = "a04e052a28133d8a79c82b53fc861d1e473c0499"
  name = "github.com/sciter-sdk/go-sciter"

[[override]]
  branch = "master"
  name = "github.com/lxn/win"

[[override]]
  # 新版会报错 shift count type int, must be unsigned integer，见 shift count type int, must be unsigned integer
  # lxn/win 中引用了 window.UTF16PtrToString，所以不能引入太老的版本，见 https://github.com/golang/sys/blame/66a0560e4e097a54e439cdc529e28fcd0f9014e8/windows/syscall_windows.go
  branch = "internal-branch.go1.16-vendor"
  name = "golang.org/x/sys"

[prune]
  go-tests = true
  # unused-packages = true
```

- unused-packages = true 被注释掉了，主要是因为vendor默认会将不包含go文件的文件夹去除，而go-sciter使用了cgo，并将头文件全部放置到了同一个文件夹，[luuny](https://github.com/lunny) 还提了个 [PR](https://github.com/AdguardTeam/go-sciter/pull/2)，不过使用dep可以对此行为进行控制，就不需要了，dep的详细使用说明可见 https://blog.csdn.net/chenguolinblog/article/details/90665116
- go-sciter 我指定了特定的commit，主要是因为api的破坏性更新，具体原因见注释
- golang.org/x/sys 我 override 并指定了特定的分支，主要是因为存在依赖关系 go-sciter -> lxn/win -> x/sys/windows，不指定会默认使用 master 分支上的最新版本，会报错 shift count type int, must be unsigned integer，但是又不能使用太老的版本，因为 lxn/win 中引用了 window.UTF16PtrToString，我搜寻了一下 [blame](https://github.com/golang/sys/blame/66a0560e4e097a54e439cdc529e28fcd0f9014e8/windows/syscall_windows.go)，找到了离 UTF16PtrToString 最近的分支版本，你也可以继续测试更改版本的分支，我只是测试该版本无问题就使用了

## 样例构建说明

1. 安装 go1.10
2. 克隆该仓库到 $GOPATH/src 下面（就是gopath开发模式）
3. 按照 https://github.com/golang/dep 中的说明安装 dep
4. 使用命令 `dep ensure` 初始化 vendor
5. 使用命令 `go build -ldflags="-H windowsgui"` 进行构建（环境变量 GOARCH=386），注意：需要手动指定32位的编译器（即修改CC和CXX，我的例子中我使用 CC=D:\Applications\Soft\mingw32\bin\gcc;CXX=D:\Applications\Soft\mingw32\bin\g++）
6. 将 [sciter-4.4.4.7-normal.dll](sciter-4.4.4.7-normal.dll) 或 [sciter-4.4.4.7-skia.dll](sciter-4.4.4.7-skia.dll) 更名为 sciter.dll，运行exe即可

## 截图

![xp截图](https://raw.githubusercontent.com/akkuman/pic/master/img/2022/09/4215945a2983ad26d15532d9ae2e8366.png)
