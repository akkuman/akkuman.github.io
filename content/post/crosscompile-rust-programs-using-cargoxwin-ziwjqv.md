---
title: 使用 cargo-xwin 交叉编译 rust 程序
slug: crosscompile-rust-programs-using-cargoxwin-ziwjqv
date: '2025-06-12 14:16:42+08:00'
lastmod: '2025-06-12 14:33:32+08:00'
tags:
  - rust
  - 交叉编译
  - windows
  - cargo-xwin
  - libesedb
keywords: rust,交叉编译,windows,cargo-xwin,libesedb
description: >-
  本文介绍了使用cargo-xwin工具交叉编译Rust程序到Windows
  x86平台时遇到的问题及解决方案。通过创建Docker容器环境、安装必要依赖（clang/llvm）、配置Rust国内镜像源，最终使用
  cargo-xwin进行编译。虽然仍出现头文件缺失错误，但提供了完整的交叉编译环境搭建流程和调试以及最终解决方案。
toc: true
isCJKLanguage: true
---





## 背景

需要将 chainsaw 工具从 linux 交叉编译到 winsows x86，该工具使用了 libesedb-sys 库，使用 `i686-pc-windows-gnu`​ 交叉编译总报错

和 [mingw build failing · Issue #16 · sunsetkookaburra/rust-libesedb](https://github.com/sunsetkookaburra/rust-libesedb/issues/16) 出现的问题类似

## 方案

首先按 cargo-xwin 官方文档搭建交叉编译环境

```bash
git clone https://github.com/WithSecureLabs/chainsaw.git
cd chainsaw
docker run --rm -itd -e XWIN_ARCH=x86 -v $(pwd):/io -w /io messense/cargo-xwin:sha-05c8e72 bash
```

然后进入该容器安装一些依赖

```bash
apt update
apt install -y clang-tools llvm clang
# 如果需要使用 rustup 加速镜像，请设置如下环境变量
export RUSTUP_DIST_SERVER=https://mirrors.tuna.tsinghua.edu.cn/rustup
# 添加 target
rustup target add i686-pc-windows-msvc
```

如果你需要使用 `crates.io`​ 加速镜像，可以参照 [crates.io-index | 镜像站使用帮助 | 清华大学开源软件镜像站 | Tsinghua Open Source Mirror](https://mirrors.tuna.tsinghua.edu.cn/help/crates.io-index/) 和 [crates.io-index镜像_crates.io-index下载地址_crates.io-index安装教程-阿里巴巴开源镜像站](https://developer.aliyun.com/mirror/crates.io-index?spm=a2c6h.13651102.0.0.13641b11zEIlVa&file=crates.io-index)

执行命令进行编译

```bash
cargo xwin build --release --target i686-pc-windows-msvc
```

报错如下

```plaintext
...'Processthreadsapi.h' file not found
...'Synchapi.h' file not found
...'Threadpoolapiset.h' file not found

  --- stderr


  error occurred in cc-rs: command did not execute successfully (status code exit status: 1): LC_ALL="C" "clang-cl" "-nologo" "-MD" "-O2" "-Brepro" "-m32" "-arch:SSE2" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/include" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/common" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/libbfio" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/libcdata" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/libcerror" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/libcfile" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/libclocale" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/libcnotify" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/libcpath" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/libcsplit" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/libcthreads" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/libesedb" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/libfcache" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/libfdata" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/libfdatetime" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/libfguid" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/libfmapi" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/libfvalue" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/libfwnt" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/libmapidb" "-I" "/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/libesedb-20230824/libuna" "-DHAVE_LOCAL_LIBBFIO=1" "-DHAVE_LOCAL_LIBCDATA=1" "-DHAVE_LOCAL_LIBCERROR=1" "-DHAVE_LOCAL_LIBCFILE=1" "-DHAVE_LOCAL_LIBCLOCALE=1" "-DHAVE_LOCAL_LIBCNOTIFY=1" "-DHAVE_LOCAL_LIBCPATH=1" "-DHAVE_LOCAL_LIBCSPLIT=1" "-DHAVE_LOCAL_LIBCTHREADS=1" "-DHAVE_LOCAL_LIBFCACHE=1" "-DHAVE_LOCAL_LIBFDATA=1" "-DHAVE_LOCAL_LIBFDATETIME=1" "-DHAVE_LOCAL_LIBFGUID=1" "-DHAVE_LOCAL_LIBFMAPI=1" "-DHAVE_LOCAL_LIBFVALUE=1" "-DHAVE_LOCAL_LIBFWNT=1" "-DHAVE_LOCAL_LIBMAPIDB=1" "-DHAVE_LOCAL_LIBUNA=1" "--target=i686-pc-windows-msvc" "-Wno-unused-command-line-argument" "-fuse-ld=lld-link" "/imsvc/root/.cache/cargo-xwin/xwin/crt/include" "/imsvc/root/.cache/cargo-xwin/xwin/sdk/include/ucrt" "/imsvc/root/.cache/cargo-xwin/xwin/sdk/include/um" "/imsvc/root/.cache/cargo-xwin/xwin/sdk/include/shared" "-Fo/io/target/i686-pc-windows-msvc/release/build/libesedb-sys-0777ba6a247460c3/out/b3682e27dd4a7e97-libcthreads_condition.o" "-c" "--" "libesedb-20230824/libcthreads/libcthreads_condition.c"

```

看看头文件实际是否存在

```plaintext
$ find / -name '*rocessthreadsapi.h'
/root/.cache/cargo-xwin/xwin/sdk/include/um/processthreadsapi.h
```

可以看到存在，并且上面的报错中，也包含了这个文件夹

突然想到 windows 上查找头文件大小写不敏感，linux 上大小写敏感，于是进到 `/root/.cache/cargo-xwin/xwin/sdk/include/um/`​ 文件夹，使用 `ln -s processthreadsapi.h Processthreadsapi.h`​ 命令一个个建立了软链接，重新编译，成功了。

或者你也可以使用如下命令临时修改下载到本地的 libesedb-sys 库中的源代码

```bash
$ find / -name 'libcthreads_condition.h'
/usr/local/cargo/registry/src/mirrors.aliyun.com-0671735e7cc7f5e7/libesedb-sys-0.2.0/libesedb-20230824/libcthreads/libcthreads_condition.h
$ cd /usr/local/cargo/registry/src/mirrors.aliyun.com-0671735e7cc7f5e7/libesedb-sys-0.2.0/libesedb-20230824
$ grep -rn 'Synchapi.h' ./ | awk -F: '{print($1)}' | xargs -I{} sed -i 's|Synchapi.h|Synchapi.h|g' {}
$ grep -rn 'Processthreadsapi.h' ./ | awk -F: '{print($1)}' | xargs -I{} sed -i 's|Processthreadsapi.h|processthreadsapi.h|g' {}
$ grep -rn 'Threadpoolapiset.h' ./ | awk -F: '{print($1)}' | xargs -I{} sed -i 's|Threadpoolapiset.h|threadpoolapiset.h|g' {}
```

修改后重新编译

我已经给 libesedb-sys 提了个 PR，详见 [fix: header files not being found on linux by akkuman · Pull Request #18 · sunsetkookaburra/rust-libesedb](https://github.com/sunsetkookaburra/rust-libesedb/pull/18)
