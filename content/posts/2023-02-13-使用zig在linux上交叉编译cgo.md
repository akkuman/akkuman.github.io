---
layout: blog
title: 使用zig在linux上交叉编译cgo
date: 2023-02-13T02:46:29.508Z
showToc: true
draft: false
description: 使用zig在linux上交叉编译cgo 的 github action
cover:
  # only hide on current single page
  hidden: false
---
使用zig在linux上交叉编译cgo 的 github action，此处不做解释了，自己可以看注释进行实验

```yaml
name: build

on:
  push:
    tags:
      - '*'

jobs:
  build-rotateproxy:
    runs-on: ubuntu-18.04
    steps:
      - name: Checkout
        uses: actions/checkout@v2
      - name: Setup Zig
        uses: goto-bus-stop/setup-zig@v1
        with:
          version: 0.9.1
      - name: Setup Golang
        uses: actions/setup-go@v2
        with:
          go-version: 1.17
      - name: Build RotateProxy
        run: |
          # download macos sysroot
          git clone --depth=1 https://github.com/hexops/sdk-macos-12.0.git "$HOME/macos-SDK"
          # create zig script
          mkdir -p "$HOME/.bin"
          export PATH=$PATH:"$HOME/.bin"
          touch "$HOME/.bin/zcc" && touch "$HOME/.bin/zxx"
          chmod +x "$HOME/.bin/zcc" && chmod +x "$HOME/.bin/zxx"
          mkdir -p build
          cd cmd/rotateproxy
          configs=(
            'linux amd64 x86_64-linux-musl'
            'linux 386 i386-linux-musl'
            'windows amd64 x86_64-windows-gnu'
            'windows 386 i386-windows-gnu'
            'darwin amd64 x86_64-macos-gnu'
          )
          IFS=$'\n'
          for i in ${configs[@]}
          do
            IFS=$' '
            config=($i)
            goos=${config[0]}
            goarch=${config[1]}
            libc=${config[2]}
            ext=''
            if [ "${goos}" = "windows" ];then
              ext='.exe'
            fi
            # ref: https://dev.to/kristoff/zig-makes-go-cross-compilation-just-work-29ho
            echo "goos: ${goos}  goarch: ${goarch}  libc: ${libc}"
            echo '#!/bin/sh' > "$HOME/.bin/zcc"
            echo '#!/bin/sh' > "$HOME/.bin/zxx"
            # ref: https://github.com/ziglang/zig/issues/10660
            # ref: https://github.com/ziglang/zig/issues/1349
            # ref: https://github.com/ziglang/zig/issues/10299#issuecomment-989153750
            if [ "${goos}" = "darwin" ];then
              # zig 0.10.0关于sysroot的行为有变更，参见 https://github.com/ziglang/zig/issues/10790#issuecomment-1030712395
              echo 'ZIG_LOCAL_CACHE_DIR="$HOME/tmp" zig cc -target '${libc}' --sysroot="$HOME/macos-SDK/root" -I"$HOME/macos-SDK/root/usr/include" -L"$HOME/macos-SDK/root/usr/lib" -F"$HOME/macos-SDK/root/System/Library/Frameworks" $@' >> "$HOME/.bin/zcc"
              echo 'ZIG_LOCAL_CACHE_DIR="$HOME/tmp" zig c++ -target '${libc}' --sysroot="$HOME/macos-SDK/root" -I"$HOME/macos-SDK/root/usr/include" -L"$HOME/macos-SDK/root/usr/lib" -F"$HOME/macos-SDK/root/System/Library/Frameworks" $@' >> "$HOME/.bin/zxx"
              # zig cc 调用clang，clang更新后默认加了一些参数，见 https://github.com/golang/go/issues/38876 https://stackoverflow.com/questions/42074035
              # 经过测试最基本需要 -Wno-nullability-completeness -Wno-expansion-to-defined -Wno-availability
              export CGO_CPPFLAGS="-Wno-error -Wno-nullability-completeness -Wno-expansion-to-defined -Wno-builtin-requires-header -Wno-availability"
            else
              echo 'ZIG_LOCAL_CACHE_DIR="$HOME/tmp" zig cc -target '${libc}' $@' >> "$HOME/.bin/zcc"
              echo 'ZIG_LOCAL_CACHE_DIR="$HOME/tmp" zig c++ -target '${libc}' $@' >> "$HOME/.bin/zxx"
            fi
            cat "$HOME/.bin/zxx"
            cat "$HOME/.bin/zcc"
            CGO_ENABLED=1 GOOS="${goos}" GOARCH="${goarch}" CC="zcc" CXX="zxx" go build -o "../../build/rotateproxy-${goos}-${goarch}${ext}" -trimpath -ldflags="-linkmode=external -extldflags=-static -s -w"
          done
      - name: Run GoReleaser
        uses: goreleaser/goreleaser-action@v2
        with:
          version: latest
          args: release --rm-dist
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```