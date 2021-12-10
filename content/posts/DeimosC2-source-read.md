---
title: DeimosC2 源码阅读
date: 2021-04-16 12:32:14
toc: true
tags:
- 源码阅读
categories:
- 源码阅读
---


花了点时间阅读了一下 [https://github.com/DeimosC2/DeimosC2](https://github.com/DeimosC2/DeimosC2) 项目的源代码，本文是一个简要的阅读笔记

<!--more-->

## 项目结构

```
.
|   build_frontend.bat
|   build_frontend.sh
|   requirements.txt
|   serial
|          
+---agents
|   +---doh
|   |       doh_agent.go               DNSOverHTTP agent代码
|   +---https
|   |       https_agent.go             HTTPS agent
|   +---quic
|   |       quic_agent.go              QUIC agent
|   +---resources                      agent基础功能
|   |   +---agentfunctions
|   |   |       functions.go
|   |   +---domainhiding
|   |   |       esni_DoH.go
|   |   +---filebrowser
|   |   |       filebrowser_linux.go
|   |   |       filebrowser_mac.go
|   |   |       filebrowser_windows.go
|   |   +---fingerprint
|   |   |       fingerprint_linux.go
|   |   |       fingerprint_mac.go
|   |   |       fingerprint_windows.go
|   |   +---selfdestruction
|   |   |       kill_linux.go
|   |   |       kill_macos.go
|   |   |       kill_windows.go
|   |   +---shellexec
|   |   |       exec_both.go
|   |   |       exec_windows.go
|   |   \---shellinject
|   |           shellcode_linux.go
|   |           shellcode_macos.go
|   |           shellcode_windows.go
|   \---tcp
|           tcp_agent.go 
+---archives
+---c2                                        C2 server主程序
|   |   main.go                                       程序入口
|   |   requirements.txt
|   +---agents
|   |   |   agent_handler.go                  agent相关基础方法
|   |   \---techniques                        一些其他技术相关实现
|   |       \---httpstechniques
|   |               domainhiding.go
|   |               normal.go
|   +---gobfuscate                            gobfuscate开源项目抽取[golang混淆]，可使用garble
|   |       const_to_var.go
|   |       gobfuscate.go
|   |       gopath_copy.go
|   |       hash.go
|   |       LICENSE
|   |       pkg_names.go
|   |       README.md
|   |       strings.go
|   |       symbols.go
|   |       util.go
|   +---lib
|   |   |   listener_handler.go               监听器相关基础方法
|   |   +---archive
|   |   |       archive.go                    数据备份相关
|   |   +---certs
|   |   |       gen_cert.go                   证书生成
|   |   +---gobuild
|   |   |       compile.go                    对生成的go代码进行编译，生成agent客户端
|   |   +---sqldb
|   |   |       sql.go                        服务端数据库相关
|   |   \---validation
|   |           validation.go                 服务端前后端数据验证
|   +---listeners                             服务端监听器相关实现
|   |       common.go
|   |       dns.go
|   |       https.go
|   |       quic.go
|   |       tcp.go
|   +---loot                                  战利品相关操作
|   |       loot.go                           
|   +---modules                               模块加载相关
|   |       module_handler.go
|   |       reflectivedll.go
|   +---webserver                             服务端前后端交互相关
|   |   |   dashboard.go
|   |   |   webserver.go
|   |   +---googauth
|   |   |       googauth.go
|   |   +---mfa
|   |   |       mfa.go
|   |   \---websockets
|   |           alerts.go
|   \---webshells
|           webshell_handler.go
+---docs
|       CHANGELOG.md
+---droppers
|   +---Linux
|   |   +---Bash
|   |   |       ondisk_dropper_tcp.sh
|   |   +---Perl
|   |   |       ondisk_dropper_tcp.pl
|   |   \---python
|   |           ondisk_dropper_tcp.py
|   +---Templates
|   |       tcp.template
|   \---Windows
|       |   dropper_options.json
|       +---binary
|       |   \---golang
|       |           dropper.go
|       +---Perl
|       |       ondisk_dropper_tcp.pl
|       +---PowerShell
|       |       ondisk_dropper_tcp.ps1
|       \---python
|               ondisk_dropper_tcp.py  
+---lib
|   +---agentscommon
|   |       agents.go
|   +---crypto
|   |       aes.go
|   |       rsa.go
|   +---logging
|   |       log.go
|   +---modulescommon
|   |       common.go
|   +---privileges
|   |       isadmin_linux.go
|   |       isadmin_macos.go
|   |       isadmin_windows.go
|   \---utils
|           utils.go
+---modules                                      一些的额外模块
|   +---collection
|   |   \---screengrab
|   |       +---agents
|   |       |   +---bin
|   |       |   \---src
|   |       |           screengrab.c
|   |       |           screengrab.go
|   |       \---server
|   |           +---bin
|   |           \---src
|   |                   screengrab.go
|   +---credentialaccess
|   |   +---lsadump
|   |   |   +---agents
|   |   |   |   +---bin
|   |   |   |   \---src
|   |   |   |           lsadump.go
|   |   |   \---server
|   |   |       +---bin
|   |   |       \---src
|   |   |               lsadump.go
|   |   +---minidump
|   |   |   +---agents
|   |   |   |   +---bin
|   |   |   |   \---src
|   |   |   |           minidump.c
|   |   |   |           minidump.go
|   |   |   \---server
|   |   |       +---bin
|   |   |       \---src
|   |   |               lsassparse.py
|   |   |               minidump.go
|   |   +---ntdsdump
|   |   |   +---agents
|   |   |   |   +---bin
|   |   |   |   \---src
|   |   |   |           ntdsdump.go
|   |   |   \---server
|   |   |       +---bin
|   |   |       \---src
|   |   |               ntdsdump.go
|   |   +---samdump
|   |   |   +---agents
|   |   |   |   +---bin
|   |   |   |   \---src
|   |   |   |           samdump.go
|   |   |   \---server
|   |   |       +---bin
|   |   |       \---src
|   |   |               lsaparse.py
|   |   |               samdump.go
|   |   |               samparse.py
|   |   \---shadowdump
|   |       +---agents
|   |       |   +---bin
|   |       |   \---src
|   |       |           shadowdump.go
|   |       \---server
|   |           +---bin
|   |           \---src
|   |                   shadowdump.go
|   +---discovery
|   |       empty.txt
|   +---dlls
|   |       c2.c
|   +---exfil
|   |       empty.txt
|   +---lateral_movement
|   |       empty.txt
|   +---persistence
|   |       empty.txt
|   \---privilege_escalation
|           empty.txt
```

## 程序主体

1. 初始化日志
2. 自定义 GOROOT 和 GOPATH 环境变量
3. 恢复（监听器和webshell）或初始化数据库，自定义或生产证书
4. 预混淆（依赖文件拷贝到GOPATH）
5. 启动插件注册RPC服务
6. 执行定期备份
7. 启动前后端之间的https和websocket接口服务

## 细节

服务端针对每一个session维护了一个执行命令队列，agent端针对所有任务的输出结果维护了一个队列

server和agent之间维护着心跳，由agent主动向server发送心跳，每次心跳时，agent从server对应的任务队列中获取命令拿去执行，同时将自己的命令结果输出返回到server

需要说一下的是modules文件夹，里面分为服务端和客户端，客户端是投递到agent中执行的，服务端的概念是c2服务器中注册的插件，整个流程大致上为：

1. 用户下发模块任务
2. 找到对应的模块 
3. 启动该模块插件RPC服务并在c2 RPC服务中注册插件
4. 将模块客户端投递到agent进行执行 
5. c2服务器获取到任务结果
6. 将任务结果发送至模块插件RPC服务进行处理并返回处理结果

其中agent端的架构也需要说一下，agent支持两种模块形式：

1. drop: 直接投递二进制可执行程序比如exe到agent进行执行
2. inject: 投递反射dll至agent的内存中执行

其中drop形式的就是上文中提到的模块插件，c2利用rpc进行与第三方模块之间的通信，第三方模块通过c2的rpc注册自己的插件，c2通过插件的rpc将结果发送至插件进行处理，在agent也有类似的处理，首先agent会启动一个rpc服务，然后接收到c2投递过来的drop exe后，将rpc端口作为命令行参数传递给该exe进行执行，然后drop exe执行过程中会将结果通过传递进来的rpc服务端口进行结果回送

