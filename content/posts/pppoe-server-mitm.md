---
title: PPPoE中间人拦截以及校园网突破漫谈
date: 2019-05-12 16:16:12
tags:
- 网络协议
categories:
- 网络协议
---


> 本文首发于[PPPoE中间人拦截以及校园网突破漫谈](https://www.anquanke.com/post/id/178484)，转载请注明出处。


# PPPoE中间人拦截以及校园网突破漫谈

校园生活快结束了，之前还有点未完成的想法，趁着这两天有兴趣搞搞。

此文面向大众是那种在校园内苦受拨号客户端的毒害，但是又想自己动手折腾下的。

<!--more-->

## 一些我知道的办法

目前主要的方法可以可以分为移动端和电脑客户端。

### 移动端

移动端基本是基于 http 的 portal 认证，这个解决方法比较多，但依据剧情情况而定。

比如拨号后克隆 mac 到路由器，还有基于这个方法的衍生方法，比如拨号前交换机，登陆后改路由器并复制 mac 到路由器。还有比如虚拟路由转发。

这些其实都是利用的检测的原理，按道理说，portal 并不像 PPPoE 那样，PPPoE 中间是不允许有路由节点的，因为在 PADI 广播包是本地广播，本地广播路由器不会进行转发，所以并不能找到一个目的 PPPoE Server。

这里扯远了，关于 PPPoE 下面再说。

我们接着看看 portal，这个是基于 HTTP 的，大体上的流程是

1. 访问一个 http 网站，比如 http://www.qq.com，因为网关会拦截 http 请求然后重定向到一个形如 http://58.53.199.144:8001/?userip=100.64.224.167&wlanacname=&nasip=58.50.189.124&usermac=1c-87-2c-77-77-9c
的网址。
2. 此时 app 会解析信息，比如 ip，mac。检测的地方就是在这里，比如检测你的手机 ip 是否和 userip 相同，加入你在路由器下，你的 ip 应该是形如 192.168.x.x 的地址，你的路由器的 wan ip 才是
和 userip 相同，还可能会进行比如 mac 判断，还可能检查 arp 表，至于这两样是怎样检测的我按下不表，总而言之，这里通不过检测，app 就判定你的网络环境不对。
3. 然后 app 会将账号或密码进行加密，然后 post 到认证服务器，认证通过后，你这个 ip 就可以上网了。

先说说为什么克隆 mac 有用，因为认证服务器那边是根据 mac 判定的，相同的 mac 在短时间内会获取到同样的 ip，并且短暂时间的断网也是允许的。其他衍生方法原理类似。

再来说说还有哪些办法，这些办法可能并没有之前的好操作。

比如 hook 判定函数

还有比如改 Response（这个办法是前阵子的思路，还没实践是否可行，既然判断参数取自响应包，那么我们应该能想到这个）

我前阵子用的比较多的其实是直接逆向 app 获取加密流程然后自写协议，但是现在看来可能是最费时费力的一种了，不过有一种好处，一个产品大概率是不会换加密算法的，顶多可能改改密钥，截取加密后的某一段。

这些大致上就是我所知道的几种移动端上面的方法了。

### 电脑端

电脑端方面老陈的文章已经写的很全面了，见 [How To : 从Netkeeper 4.X客户端获取真实账号](https://blog.sunflyer.cn/archives/460)

这里面提到了我们可以下手的三个方面

1. 客户端本身

比如 hook RasDialW api 和 CE 暴搜。

但是就如文章中所说，加了保护，可能是自行实现 peloader 也说不定，反正就是相当于没走系统的 api，而是自行搞了一份来进行拨号，这样就没办法通过 hook 系统 api 来获取了。另外暴搜内存也有局限。

拿我们湖北的举例子，湖北的客户端是动态加载一个 dll 来进行账号密码加密，但是这个过程很快，这个客户端主要的操作都貌似是在 dll 中完成，这里我说的快是指，他加载 dll 完成加密然后可能
又调用了它的其他 dll 拨号后，只要一个dll完成了它的“使命”，它会立刻卸载，导致我们通过 CE 手动暴搜内存几乎不可能（这里可能我写的有谬误，不过就我分析湖北的客户端来说感觉是这样）

2. 系统层面

这个就如文章中提到的事件日志相关的东西

3. 中间人

根据 PPPoE 协议的流程，我们完全可以自己搞一个 server 来进行拦截。

下面我们将详细了解这个，以及能够自己动手实现一个简单的 PPPoE Server。

## PPPoE 协议流程

PPPoE 是一个二层协议，工作在链路层。

PPPoE 主要分为两个阶段，一个是发现阶段，我的理解就是两台机器建立起点对点的联系，第二个是会话阶段，这个阶段主要是配置确认，然后开始验证账号密码。

至于后面的分配 ip 的确定我们按下不表，因为此文主要关注的是拦截。

PPPoE 具体可分为以下阶段

1. PPPoE发现阶段(Discovery)
   - 主机广播发起分组（PADI）
   - 有效发现提供包分组（PADO）
   - 有效发现请求分组（PADR）
   - 有效发现会话确认（PADS）
2. PPPoE会话阶段(Session)
   - LCP协议请求确认配置(LCP-Config-Req)
   - LCP协议确认配置(LCP-Config-Ack)
   - PAP或CHAP验证账号密码

验证通过后开始进行一些后续的分配 ip 以及其他操作。

## PPPoE 发现阶段

### PADI

PADI 是一个广播包，发往 ff:ff:ff:ff:ff:ff 的广播地址，然后这个广播包会在本地网络进行广播。

它的 CODE 字段值为 0×09，SESSION-ID（会话ID）字段值为 0×0000。

PADI 分组必须至少包含一个 Host-Uniq，Host-Uniq为主机唯一标识，类似于PPP数据报文中的标识域，主要是用来匹配发送和接收端的。因为对于广播式的网络中可能会同时存在很多个PPPoE的数据报文。

![](https://raw.githubusercontent.com/akkuman/pic/master/img/PADI_TIM_20190512202318.png)

因为此时发的是广播包，那么我们只需要本机搭建一个 Server 对 PADI 进行响应，就可以开始我们的中间人作业了。

具体流程就是监听网卡，然后过滤 CODE 字段值为 0×09 的包然后进行响应即可。

因为其中的 Host-Uniq 字段在后续的请求中都需要，我们写一个函数把这个字段值揪出来。

```python
#寻找客户端发送的Host-Uniq
def padi_find_hostuniq(self, payload):
    _key = b'\x01\x03'
    payload = bytes(payload)
    if _key in payload:
        _nIdx = payload.index(_key)
        _nLen = struct.unpack("!H", payload[_nIdx + 2:_nIdx + 4])[0]
        _nData = payload[_nIdx + 2:_nIdx + 4 + _nLen]
        return _key + _nData
    return
```

需要传入的是一个 Packet.payload，payload 是除去链路层的其他数据，在这里面具体就是 PPPoED 下面的数据

### PADO

当一个接入集中器（Server）接收到一个 PADI 包以后，就需要进行响应，发出 PADO 包了。

PADO 包的 CODE 字段值为 0×07，SESSION-ID 字段值仍为 0×0000。

PADO分组必须包含一个接入集中器名称类型的标签（此处的标签类型字段值为 akkuman），其实就是一个名字，你想填什么都可以。

并且需要包含前面 PADI 包中的 Host-Uniq 字段，这个字段在 PPPoE 的发现阶段都是必要的。

![](https://raw.githubusercontent.com/akkuman/pic/master/img/PADO_TIM_20190512203433.png)

在载荷中可能有多个 tag，他们的格式如下：

```
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |          TAG_TYPE             |        TAG_LENGTH             |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |          TAG_VALUE ...                                        ~
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

可以看出，标记的封装格式采用的是大家所熟知的TLV结构，也即是（类型+长度+数据）。标记的类型域为2个字节，各个标记的类型所代表的含义具体可以查看 [RFC 2516](https://datatracker.ietf.org/doc/rfc2516/) 或 [PPPoE帧格式](https://datatracker.ietf.org/doc/rfc2516/)

这里的 0x0103 即代表 Host-Uniq，是主机唯一标识，作用在上文已经提及。

那我们可以根据这个要求写一个发送 PADO 包的函数。

```python
#发送PADO回执包
def send_pado_packet(self, pkt):
    # 寻找客户端的Host_Uniq
    _host_Uniq = self.padi_find_hostuniq(pkt.payload)
    _payload = b'\x01\x02\x00\x07akkuman\x01\x01\x00\x00'
    if _host_Uniq:
        _payload += _host_Uniq
    # PADO 回执包的 sessoinid 为 0x0000
    pkt.sessionid =  getattr(pkt, 'sessionid', 0x0000)
    sendpkt = Ether(src=MAC_ADDRESS, dst=pkt.src, type=0x8863) / PPPoED(version=1, type=1, code=0x07, sessionid=pkt.sessionid, len=len(_payload)) / _payload
    scapy.sendp(sendpkt)
```

其中的 pkt 是接收到的 PADI 数据包。

上面的 _payload 中的 \x01\x02 代表是 AC-Name 字段，\x00\x07 是后面的 akkuman 的长度。\x01\x01 是代表 Service-Name 字段，一般为空，所以我们这里直接填 \x00\x00。下文不再赘述。

其中的源 mac 地址和目标 mac 地址我们需要改改。

然后加上 Host-Uniq 字段，封装成包发出去，注意这里的 type=0x8863 是代表发现阶段，0x8864 是会话阶段。

至于这个是怎么封装起来的，这个是 scapy 库的语法，Ether 代表链路层，剩下的依此大家参照图即可理解，最后的 _payload 代表接上一段原始数据，一般就是 bytes。

### PADR

因为 PADI 包是广播的，所以客户端有可能收到不同的接入集中器多个的 PADO 响应包，客户端应该基于 AC-Name 和可以提供的服务（这个参见 RFC2516）从中选择一个合适的接入集中器。

然后客户端就发送 PADR 包到自己选择的接入集中器（将目标 mac 改成 PADO 包中的源 mac 即可），其中 CODE 字段为 0×19，SESSION_ID 字段值仍为 0×0000。

![](https://raw.githubusercontent.com/akkuman/pic/master/img/PADR_TIM_20190512205952.png)

### PADS

当接入集中器收到一个 PADR 包以后，就要准备开始一个 PPP 会话了。

在这个阶段，接入集中器会为接下来的 PPPoE 会话生成一个独一无二的 SESSION_ID，然后组装起来进行发送。其中 CODE 字段值为 0×65 。

![](https://raw.githubusercontent.com/akkuman/pic/master/img/PADS_TIM_20190512210604.png)

根据此我们可以写出一个发送 PADS 包的函数。

```python
#发送PADS回执包
def send_pads_packet(self, pkt):
    #寻找客户端的Host_Uniq
    _host_Uniq = self.padi_find_hostuniq(pkt.payload)
    _payload = b'\x01\x01\x00\x00'
    if _host_Uniq:
        _payload += _host_Uniq

    pkt.sessionid =  SESSION_ID
    sendpkt = Ether(src=MAC_ADDRESS, dst=pkt.src, type=0x8863) / PPPoED(version=1, type=1, code=0x65, sessionid=pkt.sessionid, len=len(_payload)) / _payload
    scapy.sendp(sendpkt)
```

其中的 pkt 为接收到的 PADR 数据包。

此时发现阶段就已经完成了，接下来就是进行 PPPoE 的会话阶段了。

## PPPoE 会话阶段

PPPoE 会话阶段的抓包并没有那么明显的特征，可能你在不同的时间看到的包的顺序都不太一样。

在此阶段的 Type 为 0x8864，代表 PPPoES，即会话阶段。

### LCP链路配置建立

一个典型的 LCP Request 如下图所示。

![](https://raw.githubusercontent.com/akkuman/pic/master/img/LCP_REQ_TIM_20190512211932.png)

Protocol：决定了后面的载荷包含的是什么样的协议报文，类似以太帧的类型字段，是用以区分载荷送给哪个上层协议处理。收下为常见协议号：
- 0xC021: LCP报文
- 0xC023: Password Authentication Protocol （PAP）
- 0xC223: Challenge Handshake Authentication Protocol （CHAP）
- 0x8021: IPCP报文，它是NCP协议的一种 （用来协商分配 ip）
- 0x0021: IP报文

LCP(Link Control Protocol) 是链路控制协议，是 PPP 协议的一个成员协议，PPP 协议在 LCP 阶段默认不做认证协商，LCP 的认证只作为一个可选的参数。

接入集中器和客户端双方通过交互LCP配置报文来协商数据链路。

协商内容包括验证方式、最大接收单元 MRU、魔术字（Magic Number）等选项。
在此阶段 LCP 的状态机发生两次改变，进入会话阶段后，检测到链路可用，则物理层会向链路层发送一个 UP 事件，链路层收到该事件后，会将LCP的状态机从当前状态改变为 Request-Sent（请求发送）状态。
LCP 开始发送 Config-Request 报文（即上图中 LCP 下面的 CODE 字段，为 1 代表 Config-Request）来协商数据链路，无论哪一端接收到了 Config-Ack 报文（LCP 的 CODE 字段为 2）时， LCP的状态机又要发生改变，从当前状态改变为 Opened 状态，进入 Opened 状态后收到 Config-Ack 报文的一方则完成了当前阶段，应该向下一个阶段跃迁，下一个阶段可能是 Authentication（如 PAP 或 CHAP），也可能是 Network Layer Protocol（NLP）。
同理可知，另一端也是一样的，但须注意的一点是在链路配置阶段双方是链路配置操作过程是相互独立的。

如果配置了验证，将进入Authentication阶段，CHAP 或 PAP 验证。如果没有配置验证，则直接进入 Network Layer Protocol 阶段，即开始分配 ip 等操作。

这是在网上找的 LCP 报文格式，其实更建议大家配合 wireshark 抓包来看。

![](https://raw.githubusercontent.com/akkuman/pic/master/img/LCP_Packet_format.png)

上面我的提到了 LCP 中的 code，LCP协议使用Code字段区分11种报文格式，详细的表见下，平时我们用的比较多的就是 1 和 2

![](https://raw.githubusercontent.com/akkuman/pic/master/img/LCP_code_table.png)

- Identifier：标识域的值表示进行协商报文的匹配关系。 标识域目的是用来匹配请求和响应报文。当对端接收到该配置请求报文后，无论使用何种报文回应对方，但必须要求回应报文中的ID要与接收报文中的ID一致。换句话说，在一个协商数据链路阶段，这个字段的值都是一样的，在本次我的例子抓包中为 1。

- Length：它是代码域Code、标志域Identified、长度域Length和数据域Data四个域长度的总和。

下面是一张图，用来说明 req 与 ack 的交互。

![](https://raw.githubusercontent.com/akkuman/pic/master/img/Link_Establishment.jpg)

从这张图中可以相信不难理解之前的话了，A 和 B 初始都在 Request-Sent（请求发送）状态。
然后两者都开始发送 Config-Request 报文，只有 A 和 B 都收到了对方的 Config-Ack 报文。
才标志着 LCP 状态变迁的完成，可以向下一个阶段 NLP 或者 Autiontication（PAP 或 CHAP）跃迁。

在协商数据链路配置阶段，点对点（PPPoE是点对点协议）双方至少都发了一个 Config-Request 报文，该报文中包含了发送方对于所有的配置参数的期望值。

关于在协商数据链路配置阶段可能出现的报文，我给大家找了一页 PPT

![](https://raw.githubusercontent.com/akkuman/pic/master/img/LCP_Configuration_Packet_20190512220257.png)

- 如果对方对于自己发送的 Config-Request 回应了一个 Config-Ack，则说明对方能识别所有选项，并且全部能够被接受；
- 如果对方对于自己发送的 Config-Request 回应了一个 Config-Nak，则说明对方能识别所有选项，但只有部分能够被接受；
- 如果对方对于自己发送的 Config-Request 回应了一个 Config-Rej，则说明对方有部分选项不能被识别，或者不能被接受；
- 如果双方最终收到对方发送的 Config-Ack 报文，则说明对方对于自己提出的配置参数的协商已经取得了一致，这同时也标志着链路建立顺利结束。

如果接收到了 Config-Nak 或者 Config-Rej，这也就意味着自己必须修改相应配置参数的期望值，然后向对方重新发送一个Config-Request报文，且等待对方新的回应。

但是就我抓到的过程中，没看见过在这个阶段有 Config-Nak 的出现。

有了上面的基础，我们再来看我的抓包历史记录

![](https://raw.githubusercontent.com/akkuman/pic/master/img/Packet_LCP_History_20190512221121.png)

其实大多不用管，只需要知道收到一个 Config-Request 得回一个 Config-Ack，并且自己也得发一个 Config-Request，并等待接收到对方的 Config-Ack。

但是我抓了好几次包，测试了不少次，发现一般情况下，一方在第一次接收到对方的 Config-Request 报文时会回应一个 Config-Rej。后续才开始对接收到的 Config-Request 回应 Config-Ack。

据此我们可以写出代码。

```python
#处理 PPP LCP 请求
def send_lcp(self, pkt):
    # 初始化 clientMap
    if not self.clientMap.get(pkt.src):
        self.clientMap[pkt.src] = {"req": 0, "ack": 0}
        
    # 处理 LCP-Configuration-Req 请求
    if bytes(pkt.payload)[8] == 0x01:
        # 第一次 LCP-Configuration-Req 请求返回 Rej 响应包
        if self.clientMap[pkt.src]['req'] == 0:
            self.clientMap[pkt.src]['req'] += 1
            print("第 %d 次收到LCP-Config-Req" % self.clientMap[pkt.src]["req"])
            print("处理Req请求，发送LCP-Config-Rej包")
            self.send_lcp_reject_packet(pkt)
            print("发送LCP-Config-Req包")
            self.send_lcp_req_packet(pkt)
        # 后面的 LCP-Configuration-Req 请求均返回 Ack 响应包
        else:
            self.clientMap[pkt.src]['req'] += 1
            print("第 %d 次收到LCP-Config-Req" % self.clientMap[pkt.src]["req"])
            print("处理Req请求，发送LCP-Config-Ack包")
            self.send_lcp_ack_packet(pkt)
    # 处理 LCP-Configuration-Rej 请求
    elif bytes(pkt.payload)[8] == 0x04:
        print("处理Rej请求，发送LCP-Config-Req包")
        self.send_lcp_req_packet(pkt)

    # 处理 LCP-Configuration-Ack 请求
    elif bytes(pkt.payload)[8] == 0x02:
        self.clientMap[pkt.src]['ack'] += 1
        print("第 %d 收到LCP-Config-Ack" % self.clientMap[pkt.src]["ack"])
    else:
        pass
```

clientMap 请无视，最开始是打算支持多个 client，并做记录使用，但是发现拦截根本不用实现这个。

其中的方法我们先不展开，到时候会给大家把所有代码放上来，根据方法名大家应该能猜到是用来干嘛的。

### Authentication 阶段

链路建立起来后，应该向下一个阶段跃迁，下一个阶段一般是 Authentication。一般来说就只有 PAP 和 CHAP。

CHAP 在高校拨号客户端中使用还并不算多，大多采用 PAP，所以 CHAP 我们暂且按下不表，相信要是你能看完这篇文章并自己动手实践的话，CHAP 的分析对你来说也是手到擒来。

在这里我们主要介绍 PAP 认证以及最最关键的环节：抓取账号密码。

PAP 的 Protocol 字段为 0xc023

PAP 包格式见下图

![](https://raw.githubusercontent.com/akkuman/pic/master/img/PPP_PAP_20190512225749.png)

从中我们可以看到 CODE 字段为 1，代表一个 Authentication-Request。前面我们说过了，Identifier 字段在链路建立阶段，这个字段的值是一样的，然后跃迁到下一阶段后，这个字段的值随着每个请求递增。

PAP 包的认证方式是由被认证端主动发起，被认证端发送明文口令至认证端，由对方认证。

PAP 并不能防止重放和穷举等攻击，而 CHAP 是由认证端主动发起（challenge 挑战），具体的安全提升大家可以自行查阅相关资料。

其中的 CODE 字段我们可以参见下表

| CODE 值 | 报文名称 |
| ------ | ------ |
| 1 | Authentication-Request |
| 2 | Authentication-Ack |
| 3 | Authentication-Nak |

我们所做的是拦截，所以我们只需要关心 Authentication-Request 的 Data 字段就好，Data 字段中，Peer-ID（用户名）字段，Password字段，它们都是明文的。

这里多说一点关于 Authentication-Ack 和 Authentication-Nak，如果认证成功，认证端会返回一个 Ack 并携带成功信息给被认证端，相反，认证失败会返回 Nak 并携带相关信息。

所以我们要做的就是在收到 Authentication-Request 包时解析出账号密码即可完成我们的小 demo 了。

代码如下

```python
# 解析pap账号密码
def get_papinfo(self, pkt):
    # pap-req
    _payLoad = bytes(pkt.payload)
    if _payLoad[8] == 0x01:
        _nUserLen = int(_payLoad[12])
        _nPassLen = int(_payLoad[13 + _nUserLen])
        _userName = _payLoad[13:13 + _nUserLen]
        _passWord = _payLoad[14 + _nUserLen:14 + _nUserLen + _nPassLen]
        print("get User:%s,Pass:%s" % (str(_userName), str(_passWord)))
        #self.send_pap_authreject(pkt)
        if pkt.src in self.clientMap:
            del self.clientMap[pkt.src]

        print("欺骗完毕....")
```

0x01 即代表 CODE 字段的 Authentication-Request。我们只需要从这个包里面按照抓包中的格式进行解析即可获取账号密码。

总体完成代码我会放在文章最后

## 遇到的一些坑

就算是一个并不算很困难的东西，但是在做这个东西的过程中还是遇到了不少坑，我在这里记录一下，免得后人和我一样踩坑。

最开始我想着因为都是本机搭建 client 和 server，那么我直接把链路层的 source 和 destination 的 mac 都设置为本机的物理网卡 mac，也就是全部采用第一个 PADI 包中的 source mac，但是我发现
除了最开始的 PADI 和 PADO，后面的包，用 wireshark 根本抓不到，我猜想是不是两个 mac 相同的原因，导致包被丢弃了 client 没收到，或者 client 本身接到这个包，但是发现两个 mac 相同。
于是不继续发送 PADR 了，这个原因我并不明白，可以完整捕获流程的只能是 server 搭建在虚拟机或者网关也就是路由器。这个结果让我十分沮丧。然后我采用了几种我能想到的办法，但是均不奏效。

1. 最容易想到的应该是伪造 server mac 了。但并不能抓到，我怀疑是没办法找到这个 mac，可能丢弃了，但是我不理解为什么就算找不到应该也会发个包吧，不至于抓包记录都没有。
2. 我用工具搭建了一个TAP网卡，我用 wireshark 看了下，包的流经是先经过 TAP 网卡，然后 TAP 会作为一个二层交换机，修改源 mac 和目标 mac 后发往以太物理网卡，然后我采用 server 监听 TAP 网卡，发响应包采用物理网卡，但是依旧是后续进行不下去，虽说这两个mac不一样，但是 client 那边依旧没响应，不知道是 client 丢弃了这个包还是说 client 那边没收到。

### 解决

当然这个问题到最后解决了，这里感谢一下老陈的指点。

其实比较简单，问题就是 npcap，毕竟 scapy 和 wireshark 都推荐这个，我也就采用了这个，但是就像前面所说的，就算伪造 mac，应该也会流经物理网卡，但是 npcap 本地发的包收不到client响应包。

所以采用 winpcap 就能正常了，包括两个 mac 相同也可以抓到。

至于这个具体是什么导致的，还是说是一个 bug，并不是太清楚。

## 你还可以做哪些有趣的事情

拦截以后，你可以自己配合自己的路由器进行拨号。

甚至大胆一点，你也可以尝试给客户端一个成功的 Authentication-Ack，看客户端会是什么效果，要是你继续模拟完整个流程，包括 IPCP，那么客户端会按照你的想法给你发送心跳包吗？

## 代码地址

[PPPoE-Intercept](https://github.com/akkuman/pppoe-intercept)

## 参考资料

- [How To : 从Netkeeper 4.X客户端获取真实账号](https://blog.sunflyer.cn/archives/460)
- [RFC 2516 - A Method for Transmitting PPP Over Ethernet (PPPoE)](https://datatracker.ietf.org/doc/rfc2516/)
- [RFC 1570 - PPP LCP Extensions](https://datatracker.ietf.org/doc/rfc1570/)
- [RFC 1661 - The Point-to-Point Protocol (PPP)](https://datatracker.ietf.org/doc/rfc1661/)
- [点到点协议PPP-百度文库](https://wenku.baidu.com/view/e644ba4f33687e21af45a916)
- [PPP（three P）基本原理](http://support.huawei.com/huaweiconnect/enterprise/huawei/m/ViewThread.html?tid=364813)
- [PPPoE-hijack](https://github.com/Karblue/PPPoE-hijack)
- [PPPoE工作原理以及PPPoE帧格式](http://www.360doc.com/content/12/0312/20/3725126_193822217.shtml)

## 致谢

感谢踩坑无助的时候[老陈](https://blog.sunflyer.cn/)的提点