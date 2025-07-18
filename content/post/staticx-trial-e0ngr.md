---
title: staticx 试用
slug: staticx-trial-e0ngr
date: '2025-07-16 13:56:03+08:00'
lastmod: '2025-07-18 10:51:34+08:00'
tags:
  - staticx
  - Python
  - pyinstaller
  - Nuitka
keywords: staticx,Python,pyinstaller,Nuitka
description: >-
  本文测试了staticx工具在32位系统上打包Python程序为静态可执行文件的可行性。通过Docker创建32位Debian环境，分别使用nuitka和pyinstaller进行打包测试。结果显示：nuitka的standalone模式产物无法运行，而pyinstaller+onefile模式生成的二进制文件可在64位系统运行，但在CentOS
  6 32位系统报错缺少libnssfix.so。后续尝试在CentOS 6 32位直接安装Python
  3.11并用pyinstaller打包时，staticx处理过程出现异常。测试表明当前方案存在跨平台兼容性问题，特别是对老旧32位系统的支持不足。
toc: true
isCJKLanguage: true
---





## 介绍

staticx 是一个工具，可以将动态可执行文件与其库依赖项捆绑在一起，以便它们可以在任何地方运行，就像静态可执行文件一样

## 测试目的

常规场景使用没有什么问题，本次测试目的是在 32 位系统上打包出一个静态可执行文件，使之能够在 centos 6 32 位和其他 64 位系统上运行

## 流程

```bash
docker run --platform linux/386 -itd docker.io/library/debian:bookworm-slim bash
```

然后进入容器

```bash
cd ~
apt update
apt install -y python3-full musl-tools scons
python3 -m venv venv
# https://staticx.readthedocs.io/en/latest/installation.html#install-from-source
BOOTLOADER_CC=/usr/bin/musl-gcc venv/bin/pip install https://github.com/JonathonReinhart/staticx/archive/master.zip -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
~/venv/bin/pip3 install nuitka pyinstaller requests -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
```

写一个测试程序

```python
import requests

resp = requests.get('https://www.baidu.com')

print(resp.text)
```

我们对 nuitka 和 pyinstaller 都试一下，根据 staticx 官方文档来看，对 pyinstaller 有特殊支持

nuitka测试下来不行，使用 `--standalone`​ 编译的结果，然后使用 staticx，产物无法运行

```bash
$ ./main.staticx.bin
/tmp/staticx-MHcIOm/requests/__init__.py:86: RequestsDependencyWarning: Unable to find acceptable character detection dependency (chardet or charset_normalizer).
Traceback (most recent call last):
  File "/tmp/staticx-MHcIOm/main.py", line 3, in <module>
  File "/tmp/staticx-MHcIOm/requests/api.py", line 73, in get
  File "/tmp/staticx-MHcIOm/requests/api.py", line 59, in request
  File "/tmp/staticx-MHcIOm/requests/sessions.py", line 589, in request
  File "/tmp/staticx-MHcIOm/requests/sessions.py", line 703, in send
  File "/tmp/staticx-MHcIOm/requests/adapters.py", line 667, in send
  File "/tmp/staticx-MHcIOm/urllib3/connectionpool.py", line 766, in urlopen
  File "/tmp/staticx-MHcIOm/urllib3/connectionpool.py", line 292, in _get_conn
  File "/tmp/staticx-MHcIOm/urllib3/connectionpool.py", line 1057, in _new_conn
ImportError: Can't connect to HTTPS URL because the SSL module is not available.
```

使用 nuitka + `--standalone --onefile`​，产物也无法运行

```bash
$ ./main.staticx.bin
Error, couldn't find attached data header.
```

使用 pyinstaller + onefile 试试

产物可以运行

然后拷贝到其他 64 位机器上可以运行

拷贝到 centos6 32 位，报错

```bash
/tmp/staticx-hbjNPa/main: error while loading shared libraries: libnssfix.so: cannot stat shared object: Invalid argument
```

然后我们在 centos 6 32 位系统上安装 python 3.11（实测 3.12 编译安装 staticx 报错）

然后打包

```bash
~/venv311/bin/pyinstaller -F main.py
~/venv311/bin/staticx ./dist/main main.s.bin
```

报错

```bash
Traceback (most recent call last):
  File "/root/venv311/lib/python3.11/site-packages/staticx/api.py", line 134, in generate
    run_hooks(self)
  File "/root/venv311/lib/python3.11/site-packages/staticx/hooks/__init__.py", line 12, in run_hooks
    hook(sx)
  File "/root/venv311/lib/python3.11/site-packages/staticx/hooks/pyinstaller.py", line 49, in process_pyinstaller_archive
    h.process()
  File "/root/venv311/lib/python3.11/site-packages/staticx/hooks/pyinstaller.py", line 76, in process
    self._add_required_deps(binary)
  File "/root/venv311/lib/python3.11/site-packages/staticx/hooks/pyinstaller.py", line 152, in _add_required_deps
    self.sx.add_library(deppath, exist_ok=True)
  File "/root/venv311/lib/python3.11/site-packages/staticx/api.py", line 171, in add_library
    libpath = self._handle_lib_symlinks(libpath)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/root/venv311/lib/python3.11/site-packages/staticx/api.py", line 236, in _handle_lib_symlinks
    self.sxar.add_symlink(arcname, target)
  File "/root/venv311/lib/python3.11/site-packages/staticx/archive.py", line 95, in add_symlink
    self.tar.addfile(t)
  File "/root/.pyenv/versions/3.11.13/lib/python3.11/tarfile.py", line 2250, in addfile
    self.fileobj.write(buf)
  File "/root/.pyenv/versions/3.11.13/lib/python3.11/lzma.py", line 240, in write
    compressed = self._compressor.compress(data)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_lzma.LZMAError: Internal error

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/root/venv311/lib/python3.11/site-packages/staticx/api.py", line 328, in generate
    gen.generate(output=output)
  File "/root/venv311/lib/python3.11/site-packages/staticx/api.py", line 133, in generate
    with self.sxar as ar:
  File "/root/venv311/lib/python3.11/site-packages/staticx/archive.py", line 72, in __exit__
    self.close()
  File "/root/venv311/lib/python3.11/site-packages/staticx/archive.py", line 78, in close
    self.tar.close()
  File "/root/.pyenv/versions/3.11.13/lib/python3.11/tarfile.py", line 2013, in close
    self.fileobj.write(NUL * (BLOCKSIZE * 2))
  File "/root/.pyenv/versions/3.11.13/lib/python3.11/lzma.py", line 240, in write
    compressed = self._compressor.compress(data)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_lzma.LZMAError: Internal error

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/root/venv311/bin/staticx", line 8, in <module>
    sys.exit(main())
             ^^^^^^
  File "/root/venv311/lib/python3.11/site-packages/staticx/__main__.py", line 49, in main
    generate(args.prog, args.output,
  File "/root/venv311/lib/python3.11/site-packages/staticx/api.py", line 324, in generate
    with gen:
  File "/root/venv311/lib/python3.11/site-packages/staticx/api.py", line 55, in __exit__
    self._cleanup()
  File "/root/venv311/lib/python3.11/site-packages/staticx/api.py", line 71, in _cleanup
    self.sxar.close()
  File "/root/venv311/lib/python3.11/site-packages/staticx/archive.py", line 82, in close
    self.xzf.close()
  File "/root/.pyenv/versions/3.11.13/lib/python3.11/lzma.py", line 147, in close
    self._fp.write(self._compressor.flush())
                   ^^^^^^^^^^^^^^^^^^^^^^^^
_lzma.LZMAError: Internal error

```

我们换个命令

```bash
~/venv311/bin/staticx --no-compress ./dist/main main.s.bin
```

执行 `main.s.bin`​

有点小问题，但是能执行

```bash
__nss_configure_lookup("gshadow", "files") failed: Invalid argument
__nss_configure_lookup("initgroups", "files") failed: Invalid argument
__nss_configure_lookup("gshadow", "files") failed: Invalid argument
__nss_configure_lookup("initgroups", "files") failed: Invalid argument
<!DOCTYPE html>
<!--STATUS OK--><html> <head>...
```

留了个 [__nss_configure_lookup Invalid argument · Issue #294 · JonathonReinhart/staticx](https://github.com/JonathonReinhart/staticx/issues/294)
