---
title: ansible-playbook 独立二进制编译实录
slug: ansibleplaybook-independent-binary-compilation-actual-record-2f3tyf
date: '2024-11-14 13:45:40+08:00'
lastmod: '2024-11-14 14:40:17+08:00'
toc: true
isCJKLanguage: true
tags:
  - Ansibe
  - Python
  - Nuitka
  - Earthly
keywords: Ansibe,Python,Nuitka,Earthly
---





## 背景/起因

内部产品涉及到很多 docker 镜像，分布式安装涉及很多主机，所以采用了 ansible 来编写部署脚本，但是有时候会因为部署机器的系统或安装的 ansible 版本不同，总是会有各种各样的问题。

最开始解决这个问题的方案是构建了一个安装了 ansible 的 alpine 镜像，然后让用户导入镜像再执行特定的命令来进行安装。

但是我们为了保证 docker 版本不一致导致的安装问题，我们在 ansible 脚本执行过程中，会清空卸载目标主机上的 docker，然后用我们的方案重装，这就导致了执行安装命令的机器不能作为目标主机进行部署，需要一台额外的主机（因为我们是依靠 docker 容器内部的 ansible-playbook 来执行的，清空卸载 docker 服务这个动作会造成 ansible-playbook 停止执行）。

所以自然而然就想到：能不能像 Golang 一样编译一个 ansible-playbook 的独立二进制可执行文件，这样就解决这个问题了。

当然，也有像 Pulumi 这样的方案，能够使用 Golang 代码来定义执行过程，目前本人还没调研过是否能方便编译出二进制运行。不过部署脚本已经使用 ansible 了，为了成本最小，还是继续能沿用 ansible 最佳。

## 方案调研

ansible 是一个 Python 写的工具。

Python 工具编译成可执行文件大致有这几种方案：

- pyinstaller
- Nuitka
- cx_Freeze
- py2exe
- PyOxidizer

截止到我当时处理这个问题时，PyOxidizer 还并不成熟，所以看了下 Nuitka，是 pyinstaller 之后出来的更现代的方案，所以决定选用这个。

编译环境方面的问题，打算使用 Docker 进行解决，恰好用过 Earthly，可以在 Docker 环境中编译好后导出文件，所以用这个

## 牛刀小试

我首先尝试使用 Python 的官方镜像做打包

搜索到了一个人有做过相关的 [Ansika/Dockerfile at main · HexmosTech/Ansika](https://github.com/HexmosTech/Ansika/blob/main/Dockerfile)

结合这个 Dockerfile，加上自己的调研测试，得出如下 `Earthfile`​

```dockerfile
VERSION 0.8
FROM python:3.9-slim-bullseye
WORKDIR /workdir

deps:
    RUN sed -i "s|http://deb.debian.org/debian|http://mirror.sjtu.edu.cn/debian|g" /etc/apt/sources.list \
        && apt-get update -y
    # 安装 ansile 7
    RUN python3.9 -m pip install ansible==7.7.0 -i https://mirror.sjtu.edu.cn/pypi/web/simple
    # 安装 nuitka 及其依赖
    RUN apt-get install --no-install-recommends -y \
            python3.9-dev \
            build-essential \
            patchelf \
            ccache \
            clang \
            libfuse-dev \
            upx \
        && python3.9 -m pip install nuitka==2.1.3 -i https://mirror.sjtu.edu.cn/pypi/web/simple

build:
    FROM +deps
    RUN python3.9 -m nuitka \
        --onefile \
        --clang \
        --include-package=pty \
        --include-package=xml \
        --include-package-data=ansible:'*.py' \
        --include-package-data=ansible:'*.yml' \
        /usr/local/bin/ansible-playbook
    SAVE ARTIFACT ansible-playbook.bin AS LOCAL ansible-playbook.bin
```

执行 `earthly +build`​ 即可编译导出。

但是这个方案依赖 GLIBC，并且因为基础镜像是 debian bullseye，所以运行环境需求 GLIBC\_2.29，经测试需要 ubuntu 22 以上才可以使用。

这个环境要求太苛刻了，很多企业内部的环境都达不到。

## 静态编译？

Golang 编译的时候，我们可以使用 alpine + musl 的手段，构建出一个无依赖的静态可执行文件。那这个可以吗？

经过我的一番调研，答案是基本走不通，原因是 python 有些库里面是使用 ctypes 调用了动态链接库，如果改用 musl 编译，则根本运行不了。

后续会提供我 Nuitka + musl 静态编译的构建尝试经历。

## 降低 GLIBC 要求？

Nuitka 官方对于静态编译的 issue 有做过一些回应，官方给出的方案是使用他们付费计划中提供的一个低版本 GLIBC 依赖的镜像来编译。

这给了我灵感，我也可以使用低版本镜像，然后进行编译。

## 步入正轨

这时才算走上比较可行的方案。

经过尝试，我选用了 `debian:jessie-slim`​ 作为基础镜像。

### 准备 Python 环境

但是我们需要安装一个 python 环境来编译，jessie 官方源里面的镜像实在太低了。

这时我想到了之前研究过 Rye 这个 uv 生态中的工具，里面可以随时安装 python 版本，在源码中能看到该工具使用的是 [Releases · indygreg/python-build-standalone](https://github.com/indygreg/python-build-standalone/releases) 这个预打包好的 python 环境。

尝试安装编译，但是使用 Nuitka 编译时总会报 gcc 相关的错误。

经过一番调研，应该是 python-build-standalone 用的基础编译系统 GLIBC 版本较高，`debian:jessie`​ 上能安装的 gcc 最高版本和这个无法进行符号链接。

所以决定自行从源码构建 python。

看了下 python 的官方文档关于自行编译的文档，比较复杂，还是找找有没有现成的。

首先我尝试了这个仓库 [python-cmake-buildsystem/python-cmake-buildsystem：用于编译 Python 的 cmake 构建系统 --- python-cmake-buildsystem/python-cmake-buildsystem: A cmake buildsystem for compiling Python](https://github.com/python-cmake-buildsystem/python-cmake-buildsystem)

但是该仓库依赖的 cmake 版本比较高，而 `debian:jessie`​ 不满足，然后升级 cmake 又涉及到升级 glibc，死循环了。

没有其他比较简单的方案了吗？

想到还有个比较出名的工具是 pyenv，我去看了看工具源码，这个工具居然是从 python 源码编译的，试一试。

python 安装没问题。

Nuitka 编译 helloworld 样例，出现问题了。

pyenv 默认采用 gcc 编译python，而 nuitka 会检测到 gcc 版本过低，不支持 c11，转用 g++，导致两边符号不对，nuitka 无法编译（我猜的）

那我们改用 clang 试试，clang 就没有这个问题了，什么版本都能用，都支持 c11。

经过测试，Nuitka 编译测试通过

所以敲定 pyenv 的方案。

### 最终方案

因为目前产品用的比较多的是 python 3.9，所以为了保持一致，还是使用 pyenv 安装了 3.9

至于依赖包为什么用这些，我也是一点点根据报错扣出来的。

根据上面的结论，我们可以给出一个 `Earthfile`​

```dockerfile
VERSION 0.8
FROM debian:jessie-slim
WORKDIR /workdir

deps:
    ENV PYTHON_BUILD_MIRROR_URL_SKIP_CHECKSUM=1
    ENV PYTHON_BUILD_MIRROR_URL="https://registry.npmmirror.com/-/binary/python"
    ENV PATH="/root/.pyenv/bin:$PATH"
    RUN \
        # 写入镜像源
        echo 'deb [trusted=yes] http://mirrors.aliyun.com/debian-archive/debian jessie main' > /etc/apt/sources.list \
        && echo 'deb [trusted=yes] http://mirrors.aliyun.com/debian-archive/debian-security jessie/updates main' >> /etc/apt/sources.list \
        && echo 'deb-src [trusted=yes] http://mirrors.aliyun.com/debian-archive/debian jessie main' >> /etc/apt/sources.list \
        && echo 'deb-src [trusted=yes] http://mirrors.aliyun.com/debian-archive/debian-security jessie/updates main' >> /etc/apt/sources.list \
        && echo 'deb [trusted=yes] http://mirrors.aliyun.com/debian-archive/debian jessie-backports main' > /etc/apt/sources.list.d/backports.list \
        && echo 'deb-src [trusted=yes] http://mirrors.aliyun.com/debian-archive/debian jessie-backports main' >> /etc/apt/sources.list.d/backports.list \
        && echo 'deb [trusted=yes] http://mirrors.aliyun.com/debian-archive/debian jessie-backports-sloppy main' > /etc/apt/sources.list.d/backports-sloppy.list \
        && echo 'deb-src [trusted=yes] http://mirrors.aliyun.com/debian-archive/debian jessie-backports-sloppy main' >> /etc/apt/sources.list.d/backports-sloppy.list \
        && apt-get update \
        # 构建python需要的装备
        # 参考 https://github.com/pyenv/pyenv/issues/2426#issuecomment-1200430855
        && apt-get build-dep -y python3 \
        # https://github.com/pyenv/pyenv/wiki/Common-build-problems#2-your-openssl-version-is-incompatible-with-the-python-version-youre-trying-to-install
        && apt-get -t jessie-backports install -y openssl \
        && apt-get install --no-install-recommends -y \
                ca-certificates \
                patchelf \
                ccache \
                curl \
                git \
                # 构建python需要的装备
                # 使用 clang 是因为 gcc 版本过低
                # pyenv 默认采用 gcc 编译python，而 nuitka 会检测到 gcc 版本过低，不支持 c11，转用 g++，导致两边符号不对，nuitka 无法编译（我猜的）
                # 而 clang 就没有这个问题了，什么版本都能用，都支持 c11
                # 参见 https://nuitka.net/doc/user-manual.html#c-compiler
                clang \
                build-essential \
                gdb \
                lcov \
                pkg-config \
                libbz2-dev \
                libffi-dev \
                libgdbm-dev \
                liblzma-dev \
                libncurses5-dev \
                libreadline6-dev \
                libsqlite3-dev \
                libssl-dev \
                lzma \
                lzma-dev \
                tk-dev \
                uuid-dev \
                zlib1g-dev
    # 从源码构建安装 python 3.9.19
    RUN curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
    RUN eval "$(pyenv init -)"
    RUN PYTHON_CONFIGURE_OPTS="--enable-shared" CXX="clang++" CC="clang"  pyenv install 3.9.19 \
        && pyenv global 3.9.19

build:
    FROM +deps
    RUN /root/.pyenv/versions/3.9.19/bin/python -m pip install --force-reinstall ansible==7.7.0 nuitka==2.1.3 -i https://mirror.sjtu.edu.cn/pypi/web/simple
    # 此处编译的时候不能再设置 CXX="clang++" CC="clang"，否则会出现下面的错误
    # TypeError: 'NoneType' object is not iterable:
    #     File "/root/.pyenv/versions/3.9.19/lib/python3.9/site-packages/nuitka/build/Onefile.scons", line 314:
    #         reportCCompiler(env, "Onefile", output_func=scons_logger.info)
    #     File "/root/.pyenv/versions/3.9.19/lib/python3.9/site-packages/nuitka/build/SconsCompilerSettings.py", line 971:
    #         ".".join(str(d) for d in env.gcc_version),
    #     FATAL: Error, onefile bootstrap binary build failed.
    # 无法创建 onefile
    RUN /root/.pyenv/versions/3.9.19/bin/python -m nuitka \
        --clang \
        --onefile \
        --include-package=pty \
        --include-package=xml \
        --include-package-data=ansible:'*.py' \
        --include-package-data=ansible:'*.yml' \
        /root/.pyenv/versions/3.9.19/bin/ansible-playbook
    SAVE ARTIFACT ansible-playbook.bin AS LOCAL ansible-playbook.bin
```

执行 `earthly +build`​ 即可编译，经过测试，该版本的 ansible-playbook.bin 甚至能在 Ubuntu 14 上使用

至于其他踩的坑，从我上面这些代码的注释中也能看出来。
