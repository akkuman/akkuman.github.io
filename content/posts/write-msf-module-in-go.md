---
title: 如何用Golang写msf插件模块
date: 2020-02-14 14:16:00
tags:
- msf
- 红队
- 工具
categories:
- 开发
---

最近有空在看msf，发现msf里面有模块的源码是golang的，去翻了翻wiki，wiki上面的编写日期是2018.12.13，搜了下国内，好像没有这方面的文章，那就自己跟着做做记个笔记

<!--more-->

首先第一步自然是安装go，官方wiki上测试是在1.11.2通过，建议使用 version >= 1.11.2 的go，怎么安装go我不再赘述

## 注意事项

### 模块限制

不过golang目前还只支持以下几个msf模块的编写

- remote_exploit
- remote_exploit_cmd_stager
- capture_server
- docs
- single_scanner
- single_host_login_scanner
- multi_scanner

### 代码限制

目前并不支持第三方库，但是可以在模块目录的 `share/src` 文件夹下放置你的库，整体上来说还是比较鸡肋

模块之间公有的库的路径在 `lib/msf/core/modules/external/go/src/metasploit` 目录下，可以自行查看

## 格式

### 顶行

首先go源码文件的顶行需要有可执行的标识，需要在文件顶行写上 `//usr/bin/env go run "$0" "$@"; exit "$?"`

这个原因主要是因为msf是基于ruby的，执行golang代码的话需要知晓执行路径或环境的信息，所以必须插入这一行

比如

```golang
//usr/bin/env go run "$0" "$@"; exit "$?"

package main

import (
	"metasploit/module"
	"net/http"
)
```

### 元数据信息

下面是需要填入一些元数据的信息来初始化你的模块，这一部分和ruby比较类似，主要是为了让msf能够读取、搜索和使用这些信息

```golang
import "metasploit/module"
func main() {
  metadata := &module.Metadata{
    Name: "<module name",
    Description: "<describe>",
    Authors: []string{"<author 1>", "<author 2>"},
    Date: "<date module written",
    Type:"<module type>",
    Privileged:  <true|false>,
    References:  []module.Reference{},
    Options: map[string]module.Option{	
      "<option 1":     {Type: "<type>", Description: "<description>", Required: <true|false>, Default: "<default>"},		
      "<option 2":     {Type: "<type>", Description: "<description>", Required: <true|false>, Default: "<default>"},
  }}

  module.Init(metadata, <the entry method to your module>)
}
```

可以看到main()方法调用了module.Init，后面的注释我们可以看到是 模块的入口方法

我们刚才说过模块之间公有的库，我们跟到这里面看看这个 module.Init 的定义

```golang
/*
 * RunCallback represents the method to call from the module
 */
type RunCallback func(params map[string]interface{})

/*
 * Initializes the module waiting for input from stdin
 */
func Init(metadata *Metadata, callback RunCallback) {
	var req Request

	err := json.NewDecoder(os.Stdin).Decode(&req)
	if err != nil {
		log.Fatalf("could not decode JSON: %v", err)
	}

	switch strings.ToLower(req.Method) {
	case "describe":
		metadata.Capabilities = []string{"run"}
		res := &MetadataResponse{"2.0", req.ID, metadata}
		if err := rpcSend(res); err != nil {
			log.Fatalf("error on running %s: %v", req.Method, err)
		}
	case "run":
		params, e := parseParams(req.Parameters)
		if e != nil {
			log.Fatal(e)
		}
		callback(params)
		res := &RunResponse{"2.0", req.ID, RunResult{"Module complete", ""}}
		if err := rpcSend(res); err != nil {
			log.Fatalf("error on running %s: %v", req.Method, err)
		}
	default:
		log.Fatalf("method %s not implemented yet", req.Method)
	}
}
```

可以看到，入口方法就是一个参数格式为 `map[string]interface{}` 的回调函数，下面的 `Init` 也好理解，首先根据你的传入参数，
查看是否是 `describe` 还是 `run` 指令，如果是 `run` 指令就执行回调，逻辑十分简单。

## 例子

msf框架的wiki中给了一个完整的示例[https://github.com/rapid7/metasploit-framework/blob/master/modules/auxiliary/scanner/msmail/exchange_enum.go](https://github.com/rapid7/metasploit-framework/blob/master/modules/auxiliary/scanner/msmail/exchange_enum.go)

我们直接那这个来分析一下

```golang
//usr/bin/env go run "$0" "$@"; exit "$?"

package main

import (
	"crypto/tls"
	"fmt"
	"metasploit/module"
	"msmail"
	"net/http"
	"strconv"
	"strings"
	"sync"
)

func main() {
	metadata := &module.Metadata{
		Name:        "Exchange email enumeration",
		Description: "Error-based user enumeration for Office 365 integrated email addresses",
		Authors:     []string{"poptart", "jlarose", "Vincent Yiu", "grimhacker", "Nate Power", "Nick Powers", "clee-r7"},
		Date:        "2018-11-06",
		Type:        "single_scanner",
		Privileged:  false,
		References:  []module.Reference{},
		Options: map[string]module.Option{
			"RHOSTS":     {Type: "string", Description: "Target endpoint", Required: true, Default: "outlook.office365.com"},
			"EMAIL":      {Type: "string", Description: "Single email address to do identity test against", Required: false, Default: ""},
			"EMAIL_FILE": {Type: "string", Description: "Path to file containing list of email addresses", Required: false, Default: ""},
		}}

	module.Init(metadata, run_exchange_enum)
}
```

首先开头就是我们刚才所谈到的格式，首先是顶行的固定格式，然后main方法是定义了元数据信息，里面定义这个模块的基本信息，
然后定义了模块的三个参数项 RHOSTS、EMAIL、EMAIL_FILE，紧接着调用了 `module.Init`

入口方法是 `run_exchange_enum`

我们看看这个方法的源码

```golang
func run_exchange_enum(params map[string]interface{}) {
	email := params["EMAIL"].(string)
	emailFile := params["EMAIL_FILE"].(string)
	threads, e := strconv.Atoi(params["THREADS"].(string))
	ip := params["rhost"].(string)

	if e != nil {
		module.LogError("Unable to parse 'Threads' value using default (5)")
		threads = 5
	}

	if threads > 100 {
		module.LogInfo("Threads value too large, setting max(100)")
		threads = 100
	}

	if email == "" && emailFile == "" {
		module.LogError("Expected 'EMAIL' or 'EMAIL_FILE' field to be populated")
		return
	}

	var validUsers []string
	if email != "" {
		validUsers = o365enum(ip, []string{email}, threads)
	}

	if emailFile != "" {
		validUsers = o365enum(ip, msmail.ImportUserList(emailFile), threads)
	}

	msmail.ReportValidUsers(ip, validUsers)
}
```

首先方法的开头取了模块的基本配置信息，紧接着是一系列判断，然后我们看到关键的代码

```golang
var validUsers []string
if email != "" {
	validUsers = o365enum(ip, []string{email}, threads)
}

if emailFile != "" {
	validUsers = o365enum(ip, msmail.ImportUserList(emailFile), threads)
}

msmail.ReportValidUsers(ip, validUsers)
```

`o365enum` 方法就在这个方法的下面，但是这里并不是我们讨论的重点，是什么我们不管，只需要知道，他执行了一些枚举遍历的操作，返回了可用的用户，操作怎么做的不在我们的讨论重点内

然后调用了 `msmail.ReportValidUsers(ip, validUsers)`

前面我们说过，并不支持第三方库，`msmail`是他自己在 `share/src` 下创建的一个库，具体代码可以在[https://github.com/rapid7/metasploit-framework/blob/master/modules/auxiliary/scanner/msmail/shared/src/msmail/msmail.go](https://github.com/rapid7/metasploit-framework/blob/master/modules/auxiliary/scanner/msmail/shared/src/msmail/msmail.go)看到

我们直接定位到我们刚才说到的 `msmail.ReportValidUsers`

```golang
package msmail

import (
	...
	"metasploit/module"
	...
)
...
func ReportValidUsers(ip string, validUsers []string) {
	port := "443"
	service := "owa"
	protocol := "tcp"
	for _, user := range validUsers {
		opts := map[string]string{
			"port":         port,
			"service_name": service,
			"address":      ip,
			"protocol":     protocol,
		}
		module.LogInfo("Loging user: " + user)
		module.ReportCredentialLogin(user, "", opts)
	}
}
```

这里面把传过来的用户名遍历了然后调用了

```golang
module.LogInfo("Loging user: " + user)
module.ReportCredentialLogin(user, "", opts)
```

前一个方法我们能猜到是日志输出
后一个呢？我们都跟过去看看

- [https://github.com/rapid7/metasploit-framework/blob/master/lib/msf/core/modules/external/go/src/metasploit/module/core.go](https://github.com/rapid7/metasploit-framework/blob/master/lib/msf/core/modules/external/go/src/metasploit/module/core.go)

```golang
func rpcSend(res interface{}) error {
	rpcMutex.Lock()
	defer rpcMutex.Unlock()

	resStr, err := json.Marshal(res)
	if err != nil {
		return err
	}
	f := bufio.NewWriter(os.Stdout)
	if _, err := f.Write(resStr); err != nil {
		return err
	}
	if err := f.Flush(); err != nil {
		return err
	}

	return nil
}

...

func LogInfo(message string) {
	msfLog(message, "info")
}

...

func msfLog(message string, level string) {
	req := &logRequest{"2.0", "message", logparams{level, message}}
	if err := rpcSend(req); err != nil {
		log.Fatal(err)
	}
}
```

可以看到 `module.LogInfo` 是基础的日志输出

- [https://github.com/rapid7/metasploit-framework/blob/master/lib/msf/core/modules/external/go/src/metasploit/module/report.go](https://github.com/rapid7/metasploit-framework/blob/master/lib/msf/core/modules/external/go/src/metasploit/module/report.go#L44)

```golang
func ReportCredentialLogin(username string, password string, opts map[string]string) {
	base := map[string]string{"username": username, "password": password}
	if err := report("credential_login", base, opts); err != nil {
		log.Fatal(err)
	}
}

func report(kind string, base map[string]string, opts map[string]string) error {
	for k, v := range base {
		opts[k] = v
	}
	req := &reportRequest{"2.0", "report", reportparams{kind, opts}}
	return rpcSend(req)
}
```

这个方法就是很简单的把数据略微友好型展示了一下

所以整个的流程就是选择好模块，设置好参数，`module.Init` 进去，然后直接 `run`，就执行 `module.Init` 第二个参数传入的回调方法

然后后面就只是你用golang进行其他操作最后再进行调用msf公有模块进行信息展示了

## References

- [https://github.com/rapid7/metasploit-framework/wiki/Writing-External-GoLang-Modules](https://github.com/rapid7/metasploit-framework/wiki/Writing-External-GoLang-Modules)
- [https://github.com/rapid7/metasploit-framework/blob/master/modules/auxiliary/scanner/msmail/exchange_enum.go](https://github.com/rapid7/metasploit-framework/blob/master/modules/auxiliary/scanner/msmail/exchange_enum.go)
- [https://github.com/rapid7/metasploit-framework/tree/master/lib/msf/core/modules/external/go/src/metasploit/module](https://github.com/rapid7/metasploit-framework/tree/master/lib/msf/core/modules/external/go/src/metasploit/module)