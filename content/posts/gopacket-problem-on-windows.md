---
title: gopacket 在 windows 上面遇到的问题
date: 2019-07-09 22:00:00
tags:
- Tips
categories:
- Tips
---

前阵子有个需求是使用 golang 抓包改包，我用到了 gopacket 这个包，但是出了一些小问题。

<!--more-->

我按照网上的方法进行使用 OpenLive 抓包，发现并不行，报错 error open adapter 啥啥啥。

经过调试发现根本找不到这个网卡，需要用 \Device\NPF_ 开头的网卡设备名，我去看了 scapy 的实现，发现使用的是 winpcap/npcap 驱动的 pcap_findalldevs 这个方法，我去 gopacket 里面找了下，发现有个方法 pcap.FindAllDevs() 可以得到所有的网卡信息。

但是用这个方法得到的数据里面的 windows 自带的网卡的 Description 描述字段上就只有个 microsoft，压根不知道是什么东西，结合 net.interifaces() 方法中的 ip 与之前得到的数据对应起来，得到了一个简陋的方案

直接上代码

```golang
package main

import (
	"fmt"
	"log"
	"net"

	"github.com/google/gopacket/pcap"
)

type IfaceInfo struct {
	NPFName     string
	Description string
	NickName    string
	IPv4        string
}

func get_if_list() []IfaceInfo {
	var ifaceInfoList []IfaceInfo

	// 得到所有的(网络)设备
	devices, err := pcap.FindAllDevs()
	if err != nil {
		log.Fatal(err)
	}

	interface_list, err := net.Interfaces()
	if err != nil {
		log.Fatal(err)
	}

	for _, i := range interface_list {
		byName, err := net.InterfaceByName(i.Name)
		if err != nil {
			log.Fatal(err)
		}
		address, err := byName.Addrs()
		ifaceInfoList = append(ifaceInfoList, IfaceInfo{NickName: byName.Name, IPv4: address[1].String()})
	}

	// 打印设备信息
	// fmt.Println("Devices found:")
	// for _, device := range devices {
	// 	fmt.Println("\nName: ", device.Name)
	// 	fmt.Println("Description: ", device.Description)
	// 	fmt.Println("Devices addresses: ", device.Description)
	// 	for _, address := range device.Addresses {
	// 		fmt.Println("- IP address: ", address.IP)
	// 		fmt.Println("- Subnet mask: ", address.Netmask)
	// 	}
	// }
	var vaildIfaces []IfaceInfo
	for _, device := range devices {
		for _, address := range device.Addresses {
			for _, ifaceinfo := range ifaceInfoList {
				if strings.Contains(ifaceinfo.IPv4, address.IP.String()) {
					vaildIfaces = append(vaildIfaces, IfaceInfo{NPFName: device.Name, Description: device.Description, NickName: ifaceinfo.NickName, IPv4: ifaceinfo.IPv4})
					break
				}
			}
		}
	}

	return vaildIfaces
}

func main() {
	fmt.Println(get_if_list())
}
```