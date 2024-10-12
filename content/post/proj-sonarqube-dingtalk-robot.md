---
title: SonarQube钉钉通知插件
date: 2021-09-29 04:22:47
showToc: true
tags:
- project
categories:
- project
---


网上看到的钉钉通知插件已经不适用于最新的 SonarQube 了，所以自己花了点时间撸了一下

<!--more-->

仓库地址: [https://github.com/akkuman/sonarqube-ding-robot](https://github.com/akkuman/sonarqube-ding-robot)

## 参数说明

```
Usage of ./sonarqube-ding-robot:
  -addr string
        输入监听地址 (default "0.0.0.0:9001")
  -token string
        输入sonarqube token
```

## 使用

### 钉钉机器人的配置

首先打开群机器人添加页面

添加一个 `自定义（通过webhook接入自定义服务）` 的机器人

然后复制出该回调地址

![](https://raw.githubusercontent.com/akkuman/pic/master/img/2021/09/237e276639b2961a91a351c23b869b31.png)

你会得到一个类似于 `https://oapi.dingtalk.com/robot/send?access_token=xxxx` 的url，其中的 `xxxx` 就是钉钉机器人的token

![](https://raw.githubusercontent.com/akkuman/pic/master/img/2021/09/505a93e9ce327f3d5c75753e15d5211b.png)

添加一个安全设置，关键词添加 `代码`，或者你可以选择ip段，这里不详细说明了

### 获取 sonarqube 的token

按照下图进行生成

![](https://raw.githubusercontent.com/akkuman/pic/master/img/2021/09/839c9807b59df97f12b6b9c19f0af946.png)

生成后你会得到 sonarqube 的 token

### 运行 sonarqube-ding-robot

下载程序

```shell
wget https://github.com/akkuman/sonarqube-ding-robot/releases/latest/download/sonarqube-ding-robot
```

或者

```shell
go install github.com/akkuman/sonarqube-ding-robot
```

然后后台运行该程序（服务）

```shell
chmod +x sonarqube-ding-robot
nohup ./sonarqube-ding-robot -addr 0.0.0.0:9696 -token sonarqube的token
```

### 在sonarqube进行网络调用配置

如果你想配置全局的网络调用（所有项目都发送通知），进入 sonarqube 的网络调用配置界面 `http://xxxx.com/admin/webhooks`

![](https://raw.githubusercontent.com/akkuman/pic/master/img/2021/09/fd545b3a634f124be5eba9d5166ca817.png)

按照上图进行设置

### 通知完成

然后进行扫描后，将会在钉钉群内推送一则通知

![](https://raw.githubusercontent.com/akkuman/pic/master/img/2021/09/5f963299f076a14f5bb5d65dd4631410.png)

## Reference

- [https://github.com/viodo/sonar-dingtalk-plugin](https://github.com/viodo/sonar-dingtalk-plugin)