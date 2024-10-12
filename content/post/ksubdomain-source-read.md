---
categories:
- 源码阅读
date: '2022-02-28T02:56:00.000Z'
showToc: true
tags:
- 源码阅读
- 学习
title: ksubdomain源码阅读

---



前两天看了amass关于dns枚举的实现，当然关于加速dns枚举的还有ksubdomain这个项目，今天花了几分钟看了下实现

阅读基于 [https://github.com/boy-hack/ksubdomain/commit/9a2f2967eb8fb5c155b22393b9241f4cd6a02dc4](https://github.com/boy-hack/ksubdomain/commit/9a2f2967eb8fb5c155b22393b9241f4cd6a02dc4)

## 分析

首先从入口点开始看 [https://github.com/boy-hack/ksubdomain/blob/main/cmd/ksubdomain/enum.go#L55-L109](https://github.com/boy-hack/ksubdomain/blob/main/cmd/ksubdomain/enum.go#L55-L109)

```go
Action: func(c *cli.Context) error {
		if c.NumFlags() == 0 {
			cli.ShowCommandHelpAndExit(c, "enum", 0)
		}
		var domains []string
		// handle domain
		if c.String("domain") != "" {
			domains = append(domains, c.String("domain"))
		}
		if c.String("domainList") != "" {
			dl, err := core.LinesInFile(c.String("domainList"))
			if err != nil {
				gologger.Fatalf("读取domain文件失败:%s\n", err.Error())
			}
			domains = append(dl, domains...)
		}
		levelDict := c.String("level-dict")
		var levelDomains []string
		if levelDict != "" {
			dl, err := core.LinesInFile(levelDict)
			if err != nil {
				gologger.Fatalf("读取domain文件失败:%s,请检查--level-dict参数\n", err.Error())
			}
			levelDomains = dl
		} else if c.Int("level") > 2 {
			levelDomains = core.GetDefaultSubNextData()
		}

		opt := &options.Options{
			Rate:         options.Band2Rate(c.String("band")),
			Domain:       domains,
			FileName:     c.String("filename"),
			Resolvers:    options.GetResolvers(c.String("resolvers")),
			Output:       c.String("output"),
			Silent:       c.Bool("silent"),
			Stdin:        c.Bool("stdin"),
			SkipWildCard: c.Bool("skip-wild"),
			TimeOut:      c.Int("timeout"),
			Retry:        c.Int("retry"),
			Method:       "enum",
			OnlyDomain:   c.Bool("only-domain"),
			NotPrint:     c.Bool("not-print"),
			Level:        c.Int("level"),
			LevelDomains: levelDomains,
		}
		opt.Check()

		r, err := runner.New(opt)
		if err != nil {
			gologger.Fatalf("%s\n", err.Error())
			return nil
		}
		r.RunEnumeration()
		r.Close()
		return nil
	},
```

具体的实现细节就不关注了，可以看到入口点只是读取了一些配置，继续进入 `RunEnumeration` 看看



```go
func (r *runner) RunEnumeration() {
	ctx, cancel := context.WithCancel(r.ctx)
	defer cancel()
	go r.recvChanel(ctx) // 启动接收线程
	for i := 0; i < 3; i++ {
		go r.sendCycle(ctx) // 发送线程
	}
	go r.handleResult(ctx) // 处理结果，打印输出

	var isLoadOver bool = false // 是否加载文件完毕
	t := time.NewTicker(1 * time.Second)
	defer t.Stop()
	for {
		select {
		case <-t.C:
			r.PrintStatus()
			if isLoadOver {
				if r.hm.Length() == 0 {
					gologger.Printf("\n")
					gologger.Infof("扫描完毕")
					return
				}
			}
		case <-r.fisrtloadChanel:
			go r.retry(ctx) // 遍历hm，依次重试
			isLoadOver = true
		}
	}
}
```

首先是启动了一个接收dns resp数据包的协程，然后启动了三个发送dns req数据包的协程，还有一个线程 `handleResult` 用来输出结果

剩下的我们先不关注，可以思考一下，启动一个发送协程，一个接收协程，一个用来打印结果，单纯这三个协程我们肯定是没法控制整个程序的停止的，因为接收协程肯定是需要一个死循环去读取。

所以我们看看下来的控制，`isLoadOver` 比较关键，可以看到它由 `fisrtloadChanel` 来控制，我们找找它是在哪里被赋值的

```go
type runner struct {
	ether           *device.EtherTable //本地网卡信息
	hm              *statusdb.StatusDb
	options         *options2.Options
	limit           ratelimit.Limiter
	handle          *pcap.Handle
	successIndex    uint64
	sendIndex       uint64
	recvIndex       uint64
	faildIndex      uint64
	sender          chan string
	recver          chan core.RecvResult
	freeport        int
	dnsid           uint16 // dnsid 用于接收的确定ID
	maxRetry        int    // 最大重试次数
	timeout         int64  // 超时xx秒后重试
	ctx             context.Context
	fisrtloadChanel chan string // 数据加载完毕的chanel
	startTime       time.Time
	domains         []string
}

func New(options *options2.Options) (*runner, error) {
	var err error
	version := pcap.Version()
	r := new(runner)
	gologger.Infof(version + "\n")

	r.options = options
	r.ether = GetDeviceConfig()
	r.hm = statusdb.CreateMemoryDB()

	gologger.Infof("DNS:%s\n", options.Resolvers)
	r.handle, err = device.PcapInit(r.ether.Device)
	if err != nil {
		return nil, err
	}

	// 根据发包总数和timeout时间来分配每秒速度
	allPacket := r.loadTargets()
	if options.Level > 2 {
		allPacket = allPacket * int(math.Pow(float64(len(options.LevelDomains)), float64(options.Level-2)))
	}
	calcLimit := float64(allPacket/options.TimeOut) * 0.85
	if calcLimit < 1000 {
		calcLimit = 1000
	}
	limit := int(math.Min(calcLimit, float64(options.Rate)))
	r.limit = ratelimit.New(limit) // per second

	gologger.Infof("Rate:%dpps\n", limit)

	r.sender = make(chan string, 99)          // 多个协程发送
	r.recver = make(chan core.RecvResult, 99) // 多个协程接收

	freePort, err := freeport.GetFreePort()
	if err != nil {
		return nil, err
	}
	r.freeport = freePort
	gologger.Infof("FreePort:%d\n", freePort)
	r.dnsid = 0x2021 // set dnsid 65500
	r.maxRetry = r.options.Retry
	r.timeout = int64(r.options.TimeOut)
	r.ctx = context.Background()
	r.fisrtloadChanel = make(chan string)
	r.startTime = time.Now()

	go func() {
		for _, msg := range r.domains {
			r.sender <- msg
			if options.Method == "enum" && options.Level > 2 {
				r.iterDomains(options.Level, msg)
			}
		}
		r.domains = nil
		r.fisrtloadChanel <- "ok"
	}()
	return r, nil
}
```

我们可以看到它是用来在数据全部发往 `sender` 后的一个标识位，可以看到 `New` 函数是用来初始化限速器，timeout等等。

然后我们继续回到之前的代码看看

```go
case <-r.fisrtloadChanel:
			go r.retry(ctx) // 遍历hm，依次重试
			isLoadOver = true
```

可以看到当数据全部发往 `sender` 后，将会调用`retry`

```go
func (r *runner) retry(ctx context.Context) {
	for {
		// 循环检测超时的队列
		now := time.Now()
		r.hm.Scan(func(key string, v statusdb.Item) error {
			if r.maxRetry > 0 && v.Retry > r.maxRetry {
				r.hm.Del(key)
				atomic.AddUint64(&r.faildIndex, 1)
				return nil
			}
			if int64(now.Sub(v.Time)) >= r.timeout {
				// 重新发送
				r.sender <- key
			}
			return nil
		})
		length := 1000
		time.Sleep(time.Millisecond * time.Duration(length))
	}
}
```

可以看到具体逻辑是：判断是否达到最大重试次数，如果没有就重新入队去进行dns请求，如果达到最大次数则从缓存中删除它。

然后继续往下看，可以看到 `isLoadOver = true` ，然后可以看

```go
if isLoadOver {
				if r.hm.Length() == 0 {
					gologger.Printf("\n")
					gologger.Infof("扫描完毕")
					return
				}
			}
```

可以看到当 `isLoadOver == true && r.hm.Length() == 0` 时，会停止扫描退出。也就是所有的子域名枚举完成或达到最大重试次数，则退出。

看完了控制逻辑，我们可以看看具体的发送包和接收包的函数了

首先看看发送

```go
func (r *runner) sendCycle(ctx context.Context) {
	for domain := range r.sender {
		r.limit.Take()
		v, ok := r.hm.Get(domain)
		if !ok {
			v = statusdb.Item{
				Domain:      domain,
				Dns:         r.choseDns(),
				Time:        time.Now(),
				Retry:       0,
				DomainLevel: 0,
			}
			r.hm.Add(domain, v)
		} else {
			v.Retry += 1
			v.Time = time.Now()
			v.Dns = r.choseDns()
			r.hm.Set(domain, v)
		}
		send(domain, v.Dns, r.ether, r.dnsid, uint16(r.freeport), r.handle)
		atomic.AddUint64(&r.sendIndex, 1)
	}
}
```

可以看到首先是发送速率的控制，然后从缓存中获取生成的子域名，如果没有代表第一次跑，初始化一个Item丢给send去发包，如果已经存在则重试次数加一，然后重新选择dns服务器，然后丢给send发包。

具体的发包函数我们就不看了，`ksubdomain` 是采用的 `gopacket` 直接构造dns包然后使用网卡发包，目的为了提速

然后看看接收函数

```go
func (r *runner) recvChanel(ctx context.Context) error {
	...

	parser := gopacket.NewDecodingLayerParser(
		layers.LayerTypeEthernet, &eth, &ipv4, &ipv6, &udp, &dns)

	var data []byte
	var decoded []gopacket.LayerType
	for {
		data, _, err = handle.ReadPacketData()
		if err != nil {
			continue
		}
		err = parser.DecodeLayers(data, &decoded)
		if err != nil {
			continue
		}
		if !dns.QR {
			continue
		}
		if dns.ID != r.dnsid {
			continue
		}
		atomic.AddUint64(&r.recvIndex, 1)
		if len(dns.Questions) == 0 {
			continue
		}
		subdomain := string(dns.Questions[0].Name)
		r.hm.Del(subdomain)
		if dns.ANCount > 0 {
			atomic.AddUint64(&r.successIndex, 1)
			result := core.RecvResult{
				Subdomain: subdomain,
				Answers:   dns.Answers,
			}
			r.recver <- result
		}
	}
}
```

我摘取了一部分，可以看到具体逻辑就是不断从网卡中获取然后解析dns返回包，然后从缓存中删除该子域名并放入 `recver` chan，这个chan主要是用来读取并输出的。

整体逻辑大体上就是这样。

## 总结

整体加速思路其实和amass有点像

amass是使用了一些额外的技巧来达到同步调用，使用单个udp连接来完成，一个协程用来写，一个用来读，而ksubdomain直接调用网卡驱动绕过了操作系统，可以突破操作系统的发包限制，会更快一些，amass对于udp到tcp的dns请求做了一些适配

