---
title: centos6使用高版本python
slug: centos6-uses-a-higher-version-of-python-6ysrp
date: '2025-07-11 13:21:15+08:00'
lastmod: '2025-07-18 10:43:16+08:00'
tags:
  - Python
  - CentOS
  - Nuitka
keywords: Python,CentOS,Nuitka
toc: true
isCJKLanguage: true
---





## 背景

需要能在 centos 6.3 上跑的 python 3.10 3.12

并且需要支持 pandas/numpy 科学库，能使用 nuitka 打包

官方版本肯定是跑不起来的

根据之前的 ansible-playbook 独立二进制编译实录 中提到的参考来看

## 笔记

### 64 位系统

首先找个 centos 6.3 镜像

```bash
docker run --name centos6 -itd matrim/centos6.3:latest bash
docker exec -it centos6 bash
```

然后换一下镜像 [centos-vault镜像_centos-vault下载地址_centos-vault安装教程-阿里巴巴开源镜像站](https://developer.aliyun.com/mirror/centos-vault)

由于 centos 6.3 的源中的 nss 版本过低，会导致 curl 出现 curl: (35) SSL connect error 这种问题，并且很多和 https 相关的比如 git 都会出问题，查了下 centos 6.3 和 6.10 的 glibc 版本都是 2.12，所以直接用 6.10 的源即可

```bash
minorver=6.10
sed -e "s|^mirrorlist=|#mirrorlist=|g" \
         -e "s|^#baseurl=http://mirror.centos.org/centos/\$releasever|baseurl=http://mirrors.aliyun.com/centos-vault/$minorver|g" \
         -i.bak \
         /etc/yum.repos.d/CentOS-*.repo
```

然后安装 pyenv，设置 pyenv 拉取镜像，安装 python 编译依赖

```bash
yum install git
# pyenv 相关环境变量
export PYTHON_BUILD_MIRROR_URL_SKIP_CHECKSUM=1
export PYTHON_BUILD_MIRROR_URL="https://registry.npmmirror.com/-/binary/python"
export PATH="/root/.pyenv/bin:$PATH"
# 换成 github 镜像拉取
export GITHUB_MIRROR="https://ghfast.top/https://github.com/"
curl -L https://files.m.daocloud.io/raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | sed 's|-c advice.detachedHead=0 -c core.autocrlf=false||g' | sed 's|GITHUB="https://github.com/"|GITHUB="'$GITHUB_MIRROR'"|g' | bash
```

其中因为 `git clone`​ 使用了 `-c advice.detachedHead=0 -c core.autocrlf=false`​，而低版本 git 不支持，所以我们需要去除，然后使用了 github 镜像来拉取 pyenv 相关的 git 仓库

```bash
# 安装 python 编译依赖
yum groupinstall -y "Development Tools"
yum install -y \
    bzip2-devel \
    ncurses-devel \
    libffi-devel \
    openssl-devel \
    readline-devel \
    sqlite-devel \
    zlib-devel \
    gdbm-devel \
    xz-devel \
    tk-devel
```

我们先试试编译安装 python 3.9

```bash
pyenv install 3.9
```

报错如下

```bash
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/root/.pyenv/versions/3.9.23/lib/python3.9/ssl.py", line 99, in <module>
    import _ssl             # if we can't import it, let the error propagate
ModuleNotFoundError: No module named '_ssl'
ERROR: The Python ssl extension was not compiled. Missing the OpenSSL lib?
```

查询了一下， CentOS 6 默认的 OpenSSL 1.0.1e 太旧，Python 3.9+ 需要 OpenSSL 1.1.1+

```bash
bash-4.1# openssl version
OpenSSL 1.0.1e-fips 11 Feb 2013
```

尝试手动编译 openssl

```bash
# 下载最新 OpenSSL 1.1.1
curl -o openssl-1.1.1w.tar.gz https://files.m.daocloud.io/github.com/openssl/openssl/releases/download/OpenSSL_1_1_1w/openssl-1.1.1w.tar.gz
tar -xf openssl-1.1.1w.tar.gz
cd openssl-1.1.1w

# 编译安装到 /usr/local/openssl
./config --prefix=/usr/local/openssl --openssldir=/usr/local/openssl shared zlib
make -j$(nproc)
make install

# 更新动态库链接
echo "/usr/local/openssl/lib" > /etc/ld.so.conf.d/openssl.conf
ldconfig

# 验证新版本
/usr/local/openssl/bin/openssl version
# 应输出 OpenSSL 1.1.1w
```

然后再编译

```bash
# https://github.com/pyenv/pyenv/wiki/common-build-problems#1-openssl-is-installed-to-an-uncommon-location
PYTHON_CONFIGURE_OPTS="--with-openssl=/usr/local/openssl" pyenv install 3.9
```

此时已经编译出产物了，但是还是有出现类似的报错

```bash
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/root/.pyenv/versions/3.9.23/lib/python3.9/sqlite3/__init__.py", line 57, in <module>
    from sqlite3.dbapi2 import *
  File "/root/.pyenv/versions/3.9.23/lib/python3.9/sqlite3/dbapi2.py", line 27, in <module>
    from _sqlite3 import *
ModuleNotFoundError: No module named '_sqlite3'
WARNING: The Python sqlite3 extension was not compiled. Missing the SQLite3 lib?
```

手动编译 sqlite3

```bash
wget https://www.sqlite.org/2023/sqlite-autoconf-3420000.tar.gz
tar -xf sqlite-autoconf-3420000.tar.gz
cd sqlite-autoconf-3420000
./configure --prefix=/usr
make -j$(nproc)
make install
```

然后重新编译安装

```bash
PYTHON_CONFIGURE_OPTS="--enable-loadable-sqlite-extensions --with-openssl=/usr/local/openssl"  pyenv install 3.10
```

可以了，python 3.12 也没问题

但是安装 pandas 时报错如下

```bash
../meson.build:28:4: ERROR: Problem encountered: NumPy requires GCC >= 8.4
```

手动编译 gcc 时间可太久了，用 clang 试试呢

```bash
# 安装 epel 源
rpm -Uvh http://mirrors.aliyun.com/epel-archive/6/x86_64/epel-release-6-8.noarch.rpm
sed -e 's!^mirrorlist=!#mirrorlist=!g' \
    -e 's!^#baseurl=!baseurl=!g' \
    -e 's!https\?://download\.fedoraproject\.org/pub/epel!http://mirrors.aliyun.com/epel-archive!g' \
    -e 's!https\?://download\.example/pub/epel!http://mirrors.aliyun.com/epel-archive!g' \
    -i /etc/yum.repos.d/epel{,-testing}.repo
# 安装 clang
yum install clang
# 使用 clang 编译
CC=clang CXX=clang++ ~/.pyenv/versions/3.10.18/bin/pip install pandas -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
```

还是报错

```bash
ERROR: C++ Compiler does not support -std=c++17
```

经过查阅，`numpy`​ 的编译失败，原因是 **C++ 编译器不支持 C++17 标准**（`ERROR: C++ Compiler does not support -std=c++17`​）。此外，你的 `clang`​ 版本是 **3.4.2**，而 `numpy`​ 2.2.6 需要支持 C++17 的编译器（如 `gcc>=8`​ 或 `clang>=7`​）

无论是手动编译 gcc，还是手动编译 clang，耗时都太长了，看看有没有人有编译好的东西

找到了两个

- [ispras/centos6.9-build-docker: CentOS 6.9 build Docker environment to distribute portable Linux binaries](https://github.com/ispras/centos6.9-build-docker)
- [opencfs/centos6-gcc9 - Docker Image | Docker Hub](https://hub.docker.com/r/opencfs/centos6-gcc9)

我们拿 centos6.9-build 来测试

依旧是安装 pyenv，然后是安装 python 编译依赖（不要安装 openssl-devel，以免覆盖掉 [openssl 1.1.1i](https://github.com/ispras/centos6.9-build-docker/blob/fd75cc36d271bdac12e46fd49d94452ea6be2730/Dockerfile#L15-L19) ），然后编译 sqlite3。然后继续使用 pyenv 编译

```bash
yum install -y \
    bzip2-devel \
    ncurses-devel \
    libffi-devel \
    readline-devel \
    zlib-devel \
    gdbm-devel \
    xz-devel \
    tk-devel
wget https://www.sqlite.org/2023/sqlite-autoconf-3420000.tar.gz
tar -xf sqlite-autoconf-3420000.tar.gz
cd sqlite-autoconf-3420000
./configure --prefix=/usr/local/sqlite3
make -j$(nproc)
make install
echo "/usr/local/sqlite3/lib" > /etc/ld.so.conf.d/sqlite3.conf
ldconfig
pyenv install 3.12
```

测试安装 pandas 没问题

### 32 位系统

按照 [ispras/centos6.9-build-docker: CentOS 6.9 build Docker environment to distribute portable Linux binaries](https://github.com/ispras/centos6.9-build-docker) 中的 Dockerfile，安装 gcc 9.3

然后按照上面的方式编译安装 python

如果打包出来的东西你想放到其他机器上运行，你可能需要使用 `LDFLAGS="-static-libgcc -static-libstdc++"`​ 来编译这些东西

```bash
# 镜像源
minorver=6.10
sed -e "s|^mirrorlist=|#mirrorlist=|g" \
         -e "s|^#baseurl=http://mirror.centos.org/centos/\$releasever|baseurl=http://mirrors.aliyun.com/centos-vault/$minorver|g" \
         -i.bak \
         /etc/yum.repos.d/CentOS-*.repo
rpm -Uvh http://mirrors.aliyun.com/epel-archive/6/x86_64/epel-release-6-8.noarch.rpm
sed -e 's!^mirrorlist=!#mirrorlist=!g' \
    -e 's!^#baseurl=!baseurl=!g' \
    -e 's!https\?://download\.fedoraproject\.org/pub/epel!http://mirrors.aliyun.com/epel-archive!g' \
    -e 's!https\?://download\.example/pub/epel!http://mirrors.aliyun.com/epel-archive!g' \
    -i /etc/yum.repos.d/epel{,-testing}.repo
# 安装基础依赖
yum -y install gcc gcc-c++ glibc-devel.i686 glibc-devel \
                   libstdc++-devel.i686 libstdc++-devel make zlib-devel \
                   python-devel git wget unzip xz bzip2 lzop re2c \
                   texi2html texinfo libffi-devel m4 glibc-static ccache
# 编译安装 openssl 1.1.1（高版本 python 依赖）
curl -O -L https://files.m.daocloud.io/github.com/openssl/openssl/releases/download/OpenSSL_1_1_1i/openssl-1.1.1i.tar.gz && \
    tar xf openssl-1.1.1i.tar.gz && rm -rf openssl-1.1.1i.tar.gz && \
    cd openssl-1.1.1i && ./config --prefix=/usr && \
    sed -i '/^CFLAG/s/$/ -fPIC/' Makefile && \
    make -j$(nproc) && make install && cd .. && rm -rf openssl-1.1.1i
# 编译安装 sqlite3 高版本（高版本 python 依赖）
wget https://www.sqlite.org/2023/sqlite-autoconf-3420000.tar.gz && \
	tar -xf sqlite-autoconf-3420000.tar.gz && rm -rf sqlite-autoconf-3420000.tar.gz && \
	cd sqlite-autoconf-3420000 && \
	./configure --prefix=/usr && \
	make -j$(nproc) && make install && cd .. && rm -rf sqlite-autoconf-3420000
# 安装 cmake （目前没看到高版本 cmake 的要求，如果后续出现，可能需要自行编译）
yum install -y cmake
# 编译安装 binutils
curl -O -L https://mirrors.aliyun.com/gnu/binutils/binutils-2.34.tar.xz && \
    tar xf binutils-2.34.tar.xz && rm -rf binutils-2.34.tar.xz && \
    cd binutils-2.34 && \
    ./configure --prefix=/usr && make -j$(nproc) && make install && \
    cd .. && rm -rf binutils-2.34
# 编译安装 gcc 9.3（numpy 编译安装要求 c++17，或者 gcc >= 8.4）
curl -O -L https://mirrors.aliyun.com/gnu/gcc/gcc-9.3.0/gcc-9.3.0.tar.xz && \
    tar xf gcc-9.3.0.tar.xz && rm -rf gcc-9.3.0.tar.xz && \
    cd gcc-9.3.0 && \
    contrib/download_prerequisites && \
    mkdir ../gcc-build && cd ../gcc-build && \
    ../gcc-9.3.0/configure --prefix=/usr --enable-languages=c,c++ --enable-multilib && \
    make -j$(nproc) && make install && \
    cd .. && rm -rf gcc-9.3.0 gcc-build
# 安装 pyenv
yum install -y git curl
echo 'export PYTHON_BUILD_MIRROR_URL_SKIP_CHECKSUM=1' >> ~/.bashrc
echo 'export PYTHON_BUILD_MIRROR_URL="https://registry.npmmirror.com/-/binary/python"' >> ~/.bashrc
export GITHUB_MIRROR="https://ghfast.top/https://github.com/"
curl -L https://files.m.daocloud.io/raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | sed 's|-c advice.detachedHead=0 -c core.autocrlf=false||g' | sed 's|GITHUB="https://github.com/"|GITHUB="'$GITHUB_MIRROR'"|g' | bash
cat >> ~/.bashrc <<EOF
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - bash)"

# Restart your shell for the changes to take effect.

# Load pyenv-virtualenv automatically by adding
# the following to ~/.bashrc:

eval "$(pyenv virtualenv-init -)"
EOF
source ~/.bashrc
```

此时就可以安装高版本 python 了

需要注意的是，经过测试，numpy 编译时，如果不使用 `-static-libgcc -static-libstdc++`​，打包出来的将会报错如下类似于依赖 GCC_7.0.0

```bash
# 预配置，尽量 -static-libgcc -static-libstdc++
echo 'export LDFLAGS="$LDFLAGS -static-libgcc -static-libstdc++"' >> ~/.bashrc
# 安装 python 3.12
pyenv install 3.12
# 如果你想安装静态编译版的 python
# PYTHON_CONFIGURE_OPTS="--disable-shared" pyenv install 3.12
# 会生成 libpython.a 静态库，可以使用 nuitka --standalone --static-libpython=yes
```

然后就可以安装 numpy，requests 等库尽情玩耍了

如果你使用了 numpy 库，并且想使用 nuitka 打包，需要使用如下命令（注意上面的 LDFLAGS 依旧）

```bash
 ~/venv/bin/nuitka --standalone --include-data-files=/lib/libz.so.1.2.3=libz.so.1 --include-data-files=/usr/lib/libstdc++.so.6.0.28=libstdc++.so.6 --include-data-files=/usr/lib/libgcc_s.so.1=libgcc_s.so.1 main.py
```

其中的 `--include-data-files`​ 需要注意，一般是拷贝到其他机器在运行时报错缺少 `libz.so.x`​ 这种，就需要从编译机上弄一份进去

另外，如果是在此处 32 位系统上编译出来的 exe（依赖 glibc），拷贝到 64 位系统上需要注意：64 位系统上需要先安装 x86 的 glibc（现代很多系统安装软件过程中就已经安装了，如果没有，需要使用 `yum install glibc.i686`​ 这样的命令安装，apt 系的系统类似）

‍
