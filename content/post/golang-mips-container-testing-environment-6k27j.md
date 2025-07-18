---
title: 搭建 golang mips 容器测试环境
slug: golang-mips-container-testing-environment-6k27j
date: '2025-07-17 17:05:32+08:00'
lastmod: '2025-07-17 20:53:12+08:00'
tags:
  - Golang
  - qemu
  - mips
keywords: Golang,qemu,mips
description: >-
  本文介绍了在Golang中编译MIPS架构程序并在本地测试的方法。作者尝试使用multiarch/qemu-user-static容器环境时遇到兼容性问题，发现旧版本QEMU对MIPS
  32位支持不足。通过测试发现Arch
  Linux的最新版qemu-user-static可以正常运行，但tonistiigi/binfmt项目暂不支持MIPS 32位。最终解决方案是下载Arch
  Linux的qemu-user-static包，提取其中的qemu-mipsel-static（小端）或qemu-mips-static（大端）二进制文件挂载到容器中使用。
toc: true
isCJKLanguage: true
---





原文链接：[搭建 golang mips 容器测试环境 | Akkuman 的技术博客](https://www.hacktech.cn/post/2025/07/golang-mips-container-testing-environment-6k27j/)

## 背景

需要golang 编译 mips 程序，然后本地做测试

注意 mips 架构分为很多，以下是名词和对应的含义区别：

- mips：32 位大端
- mipsel/mipsle：32 位小端
- mips64：64 位大端
- mips64el/mips64le: 64 位小端

## 记录

编译 golang程序

```bash
GOOS=linux GOARCH=mips GOMIPS=softfloat go build
```

mips 环境

```bash
docker run --rm --privileged multiarch/qemu-user-static:register --reset
# https://github.com/multiarch/qemu-user-static/issues/15
find /proc/sys/fs/binfmt_misc -type f -name "*mipsn32*" -exec sh -c 'echo -1 > {}' \;
docker run -it --rm multiarch/debian-debootstrap:mips-buster-slim
```

经过测试

multiarch/qemu-user-static 的环境太老，对 mips 32 bit 的支持有问题

会报错

```plaintext
fatal error: sigaction failed

runtime stack:
runtime.throw({0xfd03e, 0x10})
        runtime/panic.go:1101 +0x48 fp=0x7ffff074 sp=0x7ffff060 pc=0xa3e00
runtime.sysSigaction.func1()
        runtime/os_linux.go:553 +0x4c fp=0x7ffff080 sp=0x7ffff074 pc=0x9ef14
runtime.sysSigaction(0x41, 0x7ffff0a8, 0x0)
        runtime/os_linux.go:552 +0x7c fp=0x7ffff098 sp=0x7ffff080 pc=0x5b114
runtime.sigaction(...)
        runtime/sigaction.go:15
runtime.setsig(0x41, 0x7dba4)
        runtime/os_linux.go:500 +0xbc fp=0x7ffff0c4 sp=0x7ffff098 pc=0x5afe0
runtime.initsig(0x0)
        runtime/signal_unix.go:148 +0x2c0 fp=0x7ffff100 sp=0x7ffff0c4 pc=0x7d23c
runtime.mstartm0()
        runtime/proc.go:1879 +0x70 fp=0x7ffff108 sp=0x7ffff100 pc=0x66508
runtime.mstart1()
        runtime/proc.go:1847 +0x94 fp=0x7ffff118 sp=0x7ffff108 pc=0x66400
runtime.mstart0()
        runtime/proc.go:1808 +0x7c fp=0x7ffff12c sp=0x7ffff118 pc=0x6634c
runtime.mstart()
        runtime/asm_mipsx.s:89 +0x14 fp=0x7ffff130 sp=0x7ffff12c pc=0xa8894

goroutine 1 gp=0x400128 m=nil [runnable]:
runtime.main()
        runtime/proc.go:147 fp=0x43e7ec sp=0x43e7ec pc=0x615f0
runtime.goexit({})
        runtime/asm_mipsx.s:664 +0x4 fp=0x43e7ec sp=0x43e7ec pc=0xaad14
```

和 https://github.com/golang/go/issues/33746#issuecomment-588066863 中的报错类似

尝试去 pkgs.org 找了个 arch linux 上最新版本的 qemu-user-static，把里面的 qemu-mips-static 拿出来，可以正常运行

说明新版本 qemu 有修复

根据 [Issues · multiarch/qemu-user-static](https://github.com/multiarch/qemu-user-static/issues/212) 来看，[tonistiigi/binfmt: Cross-platform emulator collection distributed with Docker images.](https://github.com/tonistiigi/binfmt) 有新版本的 qemu

但是下载看了下，支持的平台不包括 mips 32 位

提了个 [my computer is linux mips64el with 4.19.0 kernel. does it is supported? · Issue #105 · tonistiigi/binfmt](https://github.com/tonistiigi/binfmt/issues/255)

希望作者能早日支持

## 解决

不过弄出来一个另外的解决方案，就是结合新版本的 qemu-user-static 来使用，主要灵感来自于 [使用 qemu-user-static 在 Docker 中生成容器异构 - 编程进阶之路 - SegmentFault 思否](https://segmentfault.com/a/1190000045134048) 中提到的将 qemu-user-static 挂载进去

首先我们去 [Search Results for qemu-user-static](https://pkgs.org/search/?q=qemu-user-static) 找到 arch linux 的 qemu-user-static 包，比如我这里访问 [qemu-user-static-10.0.2-1-x86_64.pkg.tar.zst Arch Linux Download](https://archlinux.pkgs.org/rolling/archlinux-extra-x86_64/qemu-user-static-10.0.2-1-x86_64.pkg.tar.zst.html) ，得到包的下载地址，解压出来找到 qemu-mipsel-static（小端） 或 qemu-mips-static （大端）

然后放到机器上，添加可执行权限

然后按照如下

```bash
docker run --rm --privileged multiarch/qemu-user-static:register --reset
# https://github.com/multiarch/qemu-user-static/issues/15
find /proc/sys/fs/binfmt_misc -type f -name "*mipsn32*" -exec sh -c 'echo -1 > {}' \;
docker run -it --rm -v ./qemu-mips-static:/usr/bin/qemu-mips-static multiarch/debian-debootstrap:mips-buster-slim
```

前两步的主要目的是预先把环境配置起来

剩下的唯一的区别就是将 qemu-mips-static 挂载进去了

这样 golang 编译产物就能正常执行，没有报错

## 注意事项

如果你使用 garble，可能新版本会有问题，我提了个 [mipsle arch broken · Issue #963 · burrowers/garble](https://github.com/burrowers/garble/issues/963)

目前可降版本 go1.21.13+garble [v0.12.1](https://github.com/burrowers/garble/releases/tag/v0.12.1) 来解决

## 参考

- [Building Go Programs for MIPS - 独行的蚂蚁 - 博客](https://zyfdegh.github.io/post/202002-go-compile-for-mips/)
- [使用 qemu-user-static 在 Docker 中生成容器异构 - 编程进阶之路 - SegmentFault 思否](https://segmentfault.com/a/1190000045134048)
