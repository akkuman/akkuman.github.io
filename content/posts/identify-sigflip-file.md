---
categories:
- 网络安全
date: '2021-12-10T07:41:00.000Z'
showToc: true
tags:
- 蓝队
- 网络安全
title: 识别SigFlip生成的恶意文件

---



最近在移植 [med0x2e/SigFlip](https://github.com/med0x2e/SigFlip) 的过程中发现了一个有意思的点，可以用来作为检测的手段



在 SigFlip 项目的 [Detect/Prevent](https://github.com/med0x2e/SigFlip#detectprevent) 一节中作者有提到一些检测防御手段

> [https://docs.microsoft.com/en-us/security-updates/SecurityAdvisories/2014/2915720?redirectedfrom=MSDN](https://docs.microsoft.com/en-us/security-updates/SecurityAdvisories/2014/2915720?redirectedfrom=MSDN)

> Once the patch is installed and proper registry keys are set, No system restarts are required, you only need to restart the Cryptographic Services. The Applocker service will be also restarted as it depends on the cryptographic services.(@p0w3rsh3ll)

> Yara rule by Adrien; [https://twitter.com/Int2e_/status/1330975808941330432](https://twitter.com/Int2e_/status/1330975808941330432)



从 SigFlip 源码中，其实也能发现一个点



SigFlip 依赖一串特定的字节来定位shellcode的位置，详见 [Native/SigLoader/SigLoader/SigLoader.cpp#L102](https://github.com/med0x2e/SigFlip/blob/e24a1fcde8ab27f58c35935f65078b47b20eca43/Native/SigLoader/SigLoader/SigLoader.cpp#L102) 和 [Native/SigFlip/SigFlip/SigFlip.cpp#L232](https://github.com/med0x2e/SigFlip/blob/e24a1fcde8ab27f58c35935f65078b47b20eca43/Native/SigFlip/SigFlip/SigFlip.cpp#L232)

```c
for (_index = 0; _index < _CertTableSize; _index++) {
		if (*(_pePtr + _index) == 0xfe && *(_pePtr + _index + 1) == 0xed && *(_pePtr + _index + 2) == 0xfa && *(_pePtr + _index + 3) == 0xce) {
			printf("[*]: Tag Found 0x%x%x%x%x", *(_pePtr + _index), *(_pePtr + _index+1), *(_pePtr + _index+2), *(_pePtr + _index+3));
			_dataOffset = _index + 8;
			break;
		}
	}
```

```c
memcpy(_encryptedData, "\xFE\xED\xFA\xCE\xFE\xED\xFA\xCE", 8);
crypt((unsigned char*)_data, _dataSize, _key, _keySize, (unsigned char*)_encryptedData + 8);
```



也就是说我们在证书表中定位到 `\xFE\xED\xFA\xCE\xFE\xED\xFA\xCE` 这段特征就可以断定它疑似 SigFlip 生成的 payload 了，想要更精准一些可以结合 [https://twitter.com/Int2e_/status/1330975808941330432](https://twitter.com/Int2e_/status/1330975808941330432) 中提到的长度特征。



~~另外很有意思的一点是，这个项目是有问题的（截至20211103 commit ~~~~[e24a1fc](/58535d3f5ef64030991147ab0a85701f)~~~~），详见 ~~~~[Native/SigFlip/SigFlip/SigFlip.cpp#L164](https://github.com/med0x2e/SigFlip/blob/e24a1fcde8ab27f58c35935f65078b47b20eca43/Native/SigFlip/SigFlip/SigFlip.cpp#L164)~~~~ 和 ~~~~[Native/SigFlip/SigFlip/SigFlip.cpp#L260](https://github.com/med0x2e/SigFlip/blob/e24a1fcde8ab27f58c35935f65078b47b20eca43/Native/SigFlip/SigFlip/SigFlip.cpp#L260)~~~~，很多情况下该项目根本没法正常使用，因为pe文件的RVA和FOA之间的关系作者并没有进行处理，只有当pe文件中的 ~~`~~SectionAlignment~~`~~ 和 ~~`~~FileAlignment~~`~~ 一样时，RVA才等于FOA，导致的结果是，可能使用工具后签名会失效。错误的位置，加上上面的特征码，这个更加是一个强特征了。公鸡队之家修改后的 ~~~~[CrackerCat/sigFile](https://github.com/CrackerCat/sigFile)~~~~ 也没有修正这个bug。~~

上面是我莽撞了，`IMAGE_DIRECTORY_ENTRY_SECURITY` 这个结构的 `VirtualAddress` 就是相对于文件开头的偏移，可参见 [Does DataDirectory[IMAGE_DIRECTORY_ENTRY_SECURITY].VirtualAddress actually mean file offset?](https://social.msdn.microsoft.com/Forums/windows/en-US/29d3a40b-844e-49a5-b436-3aff929dba30/does-datadirectoryimagedirectoryentrysecurityvirtualaddress-actually-mean-file-offset?forum=windowssdk) 和 [SigThief 的相关实现](https://github.com/secretsquirrel/SigThief/blob/ffb501bcd86acd439e4458a33e9fc5ebed4b59a8/sigthief.py#L99-L116)，所以这个并不是bug



另外还有一个bug，注意在 [Native/SigFlip/SigFlip/SigFlip.cpp#L149-L159](https://github.com/med0x2e/SigFlip/blob/e24a1fcde8ab27f58c35935f65078b47b20eca43/Native/SigFlip/SigFlip/SigFlip.cpp#L149-L159)

```c
//Security entry seems to be located at the 7th offset (Data_Dir) for For x64 PE files, and the 5th offset for x86 PE files. just a quick workaround to make the script work for different PE archs.
if (IsWow64(GetCurrentProcess())) {
	if (_optHeader.Magic == 0x20B) {
		_DT_SecEntry_Offset = 2;
	}
}
else {
	if (_optHeader.Magic == 0x10B) {
		_DT_SecEntry_Offset = -2;
	}
}
...
//Get IMAGE_DIRECTORY_ENTRY_SECURITY field and retrieve the RVA and SIZE of the Certificate Table (WIN_CERTIFICATE).
_CertTableRVA = _optHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_SECURITY + _DT_SecEntry_Offset].VirtualAddress;
_CertTableSize = _optHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_SECURITY + _DT_SecEntry_Offset].Size;
```

但是实际上看到的基本都是 `IMAGE_DIRECTORY_ENTRY_SECURITY` 在第五个，而没有他这里的情况，并且就算是有这种情况，注释和代码写得也不相符。



最后一句，Native跑不起来，DotNet的实现是正确的



最后的 yara 规则大家可以自己研究下

