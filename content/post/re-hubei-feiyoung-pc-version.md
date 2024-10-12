---
title: 湖北校园网PC端拨号算法逆向
date: 2019-05-21 13:50:00
toc: true
tags:
- 网络协议
- 逆向
categories:
- 逆向
---

# 湖北校园网PC端拨号算法逆向

## 前言

上一文 [PPPoE中间人拦截以及校园网突破漫谈](https://www.anquanke.com/post/id/178484)我们谈到使用 PPPoE 拦截来获取真实的账号密码。  
在这个的基础上，我对我们湖北的客户端进行了逆向，得到了拨号加密算法。

<!--more-->

## 准备工作

首先查壳，发现这个版本没壳了，我记得之前好像是加过 vmp 的呀，不管了。  
然后我们看看目录下的 dll 导出表看看有没有什么好东西

![](https://raw.githubusercontent.com/akkuman/pic/master/img/20190521135332_AidcComm_Export.png)

AidcComm.dll 里面有这些东西，看来这个极大可能会是我们的目标。

我们再看看主程序的导入表，发现主程序的导入表里面并没有这个 dll，那我们动态调试的时候应该怎么断到这个 dll 中去呢。  
没有导入表说明没有 .lib，那有可能是通过 LoadLibrary 加载的 dll，至于自实现 peloader，我觉得应该这个软件应该不会是这样。  
看看就知道了。  
直接用 x32dbg 和 IDA 开始看。

## 逆向过程

x32dbg 打开主程序，然后 `bp LoadLibraryW`，再重新载入程序，我们可以一步步运行发现 AidcComm.dll 被载入了。  
然后运行到用户代码处

![](https://raw.githubusercontent.com/akkuman/pic/master/img/20190521140452_x32dbg_load_aidccomm.png)

我们可以看到此时 eax 寄存器的值为 55870000，这个就是 LoadLibrary 返回的 HANDLE。一般思路来说，接下来就是用 GetProcAddress 获取导出表函数的地址了。  
继续往下走几步，即可发现我们的猜测并没有错误。

![](https://raw.githubusercontent.com/akkuman/pic/master/img/20190521141007.png)

从这张图我们可以看到主程序获取了 AidcComm.GetPWD 和 AidcComm.GetRegularAccount 的地址。  
那我们通过 call 之后的 eax 跳转过去在这两个函数的地址下断，直接跑起来。  
然后我们会发现在 AidcComm.GetRegularAccount 断下来了，传入的参数可以在堆栈窗口中看到。

![](https://raw.githubusercontent.com/akkuman/pic/master/img/20190521142139.png)

我们去 IDA 分析 GetRegularAccount 这个函数，同时在调试器这边动态跟（这个我已经分析过了，所以有的变量和函数名我已经改过了）

![](https://raw.githubusercontent.com/akkuman/pic/master/img/20190521142257.png)

首先最直观的就是账号的变换，账号只需要加上前缀 `!^Wnds0` 即可（但其实加密出来后，主程序这个给它又加了一个后缀 `@hbxy`）。（从调试器可以看到）  
密码我们直接跟到 GetPWD 里面去看。

![](https://raw.githubusercontent.com/akkuman/pic/master/img/20190521143020.png)

通过调试器我们可以观察出，这个分支结构只会执行 `a2 == 1` 这个分支。  
看来是通过下面这个函数加密的了。（我给他改了名 encryptPwdWithKey）
我们进到 `encryptPwdWithKey(void *password, char *key, rsize_t SizeInBytes)` 这个函数去查看。

![](https://raw.githubusercontent.com/akkuman/pic/master/img/20190521143504.png)

通过分析我们可以得出大致上的流程
1. password 用 key RC4 一下得到 A
2. 把 A md5 一下得到 B，如果第 11 位为奇数，取 B 的前 16 位，偶数就后 16 位，得到 C
3. C 再用 key RC4 一下得到 D
4. D 再 md5 一下，取 [8:24]得到 E

也就是最后得到的 E 是加密之后的。

可能有的小伙伴不明白为什么会是 RC4，这里有几个提示的地方，第一是这个字符串的提示，第二是 RC4 加密流程是很容易分辨的，这个靠经验了。

但是我们发现我们截取出来的密码和这个是有点小不一样的。通过调试，可以看到在 GetRegularAccount 函数加密出来后，又调用了一个函数，这个函数我给它重命名为 fixHBKey 了。

![](https://raw.githubusercontent.com/akkuman/pic/master/img/20190521144314.png)

我们跟进去看看

![](https://raw.githubusercontent.com/akkuman/pic/master/img/20190521144424.png)

代码并不长，我们可以直接调试器分析，如果你想用 IDA 也是可以的，IDA 可以搜索上图中的 `<<< FixHBKey: %s <<<` 这个字符串来定位这个函数。
或者我们可以看到这个函数的入口地址为 `001115D0`，这个 exe 的加载基址我们可以往上滑到顶看到为 `000F1000`，两个之间的差值为 `205D0`，
然后再把这个差值加上 IDA 加载的基址，即可找到这个函数。

这个函数的大致作用就是修改上面我们得到的 E
- E[今天几号日期 % 16] 替换为 'b' 得到最后的密码

这块我们是搞清楚了，那 key 是怎么来的呢。  
这个我们就需要大量借助调试器了，我们重启一下主程序，然后在上面的分析基础上找到这个 key 第一次出现的地方，我们可以发现
在 AidcRes 偏移 10110 处即为 key 的生成函数。

![](https://raw.githubusercontent.com/akkuman/pic/master/img/20190521150058.png)

这个函数巨长，同样的，我们借助之前的方法在 IDA 中找到这个函数，我这里直接按偏移，可以看到在 sub_420110 即为我们的加密函数，
这里我已经重命名为 generateKey。

这个函数太长了，我无法截全图，我直接丢代码然后分析，这里分析建议大家调试结合代码来看，不然一头雾水。其中大量的必要变量和函数我已经重命名，方便大家阅读。

```c
int __thiscall generateKey(char *this, int a2, char a3, int a4, int a5, int a6, int a7, int a8)
{
  int v8; // eax
  int v9; // edx
  int v11; // [esp+8h] [ebp-37Ch]
  char *v12; // [esp+20h] [ebp-364h]
  int len_username_b_MonthDay; // [esp+24h] [ebp-360h]
  char *v14; // [esp+28h] [ebp-35Ch]
  int len_bUsernameMonthDay; // [esp+2Ch] [ebp-358h]
  char *v16; // [esp+30h] [ebp-354h]
  char *mem_17; // [esp+34h] [ebp-350h]
  int v18; // [esp+38h] [ebp-34Ch]
  int lenMonthDay; // [esp+3Ch] [ebp-348h]
  int lenUsername; // [esp+40h] [ebp-344h]
  int v21; // [esp+44h] [ebp-340h]
  int v22; // [esp+48h] [ebp-33Ch]
  int *v23; // [esp+4Ch] [ebp-338h]
  int v24; // [esp+50h] [ebp-334h]
  const char *v25; // [esp+54h] [ebp-330h]
  int len_HbKeyGa; // [esp+58h] [ebp-32Ch]
  int lenHbKeyGa; // [esp+5Ch] [ebp-328h]
  char *pMem_64_a; // [esp+60h] [ebp-324h]
  int len_HbKeyGb; // [esp+64h] [ebp-320h]
  int lenHbKeyGb; // [esp+68h] [ebp-31Ch]
  char *pMem_64_b; // [esp+6Ch] [ebp-318h]
  int v32; // [esp+70h] [ebp-314h]
  int v33; // [esp+74h] [ebp-310h]
  int v34; // [esp+78h] [ebp-30Ch]
  int v35; // [esp+7Ch] [ebp-308h]
  int len_monthDay_Username_b; // [esp+80h] [ebp-304h]
  char *v37; // [esp+84h] [ebp-300h]
  int len_username_MonthDay_b; // [esp+88h] [ebp-2FCh]
  LPVOID lp_mix_md5_1; // [esp+8Ch] [ebp-2F8h]
  size_t v40; // [esp+90h] [ebp-2F4h]
  int v41; // [esp+94h] [ebp-2F0h]
  LPVOID v42; // [esp+98h] [ebp-2ECh]
  LPVOID v43; // [esp+9Ch] [ebp-2E8h]
  LPVOID v44; // [esp+A0h] [ebp-2E4h]
  int index3; // [esp+A4h] [ebp-2E0h]
  int index2; // [esp+A8h] [ebp-2DCh]
  char *pHbKeyGa; // [esp+ACh] [ebp-2D8h]
  int index6; // [esp+B0h] [ebp-2D4h]
  int index5; // [esp+B4h] [ebp-2D0h]
  _DWORD *md5_monthDay_Username_b; // [esp+B8h] [ebp-2CCh]
  _DWORD *md5_username_b_MonthDay; // [esp+BCh] [ebp-2C8h]
  _DWORD *md5_username_MonthDay_b; // [esp+C0h] [ebp-2C4h]
  void *mix_md5_1; // [esp+C4h] [ebp-2C0h]
  int md5_1_pLus3remainder4; // [esp+C8h] [ebp-2BCh]
  int md5_bUsernameMonthDay; // [esp+CCh] [ebp-2B8h]
  char *pHbKeyGb; // [esp+D0h] [ebp-2B4h]
  void *v57; // [esp+D4h] [ebp-2B0h]
  void *v58; // [esp+D8h] [ebp-2ACh]
  int md5_4_plus5remainer4; // [esp+DCh] [ebp-2A8h]
  void *mix_md5_2; // [esp+E0h] [ebp-2A4h]
  const char *userName; // [esp+E4h] [ebp-2A0h]
  char *monthDay; // [esp+E8h] [ebp-29Ch]
  char *bUsernameMonthDay; // [esp+ECh] [ebp-298h]
  char *username_b_MonthDay; // [esp+F0h] [ebp-294h]
  char *username_MonthDay_b; // [esp+F4h] [ebp-290h]
  char *monthDay_Username_b; // [esp+F8h] [ebp-28Ch]
  char *p_HbKeyGb; // [esp+FCh] [ebp-288h]
  char *p_HbKeyGa; // [esp+100h] [ebp-284h]
  const char *username; // [esp+104h] [ebp-280h]
  _DWORD *md5_2; // [esp+108h] [ebp-27Ch]
  _DWORD *md5_3; // [esp+10Ch] [ebp-278h]
  int index1; // [esp+114h] [ebp-270h]
  int index4; // [esp+118h] [ebp-26Ch]
  int temp1; // [esp+11Ch] [ebp-268h]
  int temp2; // [esp+120h] [ebp-264h]
  _DWORD *md5_4; // [esp+124h] [ebp-260h]
  int md5_1; // [esp+128h] [ebp-25Ch]
  size_t SizeInBytes; // [esp+134h] [ebp-250h]
  char *DstBuf; // [esp+138h] [ebp-24Ch]
  char *pThis; // [esp+13Ch] [ebp-248h]
  int v81; // [esp+140h] [ebp-244h]
  int v82; // [esp+144h] [ebp-240h]
  int v83; // [esp+148h] [ebp-23Ch]
  int v84; // [esp+14Ch] [ebp-238h]
  int v85; // [esp+150h] [ebp-234h]
  int v86; // [esp+154h] [ebp-230h]
  int v87; // [esp+158h] [ebp-22Ch]
  int v88; // [esp+15Ch] [ebp-228h]
  char hbKey; // [esp+160h] [ebp-224h]
  char v90; // [esp+161h] [ebp-223h]
  char hbKeyGa; // [esp+1E4h] [ebp-1A0h]
  char mem_64_a; // [esp+1E5h] [ebp-19Fh]
  char hbKeyGb; // [esp+228h] [ebp-15Ch]
  char mem_64_b; // [esp+229h] [ebp-15Bh]
  char v95; // [esp+22Fh] [ebp-155h]
  char v96[4]; // [esp+26Ch] [ebp-118h]
  char v97[5]; // [esp+270h] [ebp-114h]
  int v98; // [esp+275h] [ebp-10Fh]
  int v99; // [esp+279h] [ebp-10Bh]
  int v100; // [esp+27Dh] [ebp-107h]
  int v101; // [esp+281h] [ebp-103h]
  int v102; // [esp+285h] [ebp-FFh]
  __int16 v103; // [esp+289h] [ebp-FBh]
  char v104; // [esp+28Bh] [ebp-F9h]
  char v105[4]; // [esp+28Ch] [ebp-F8h]
  char v106[5]; // [esp+290h] [ebp-F4h]
  int v107; // [esp+295h] [ebp-EFh]
  int v108; // [esp+299h] [ebp-EBh]
  int v109; // [esp+29Dh] [ebp-E7h]
  int v110; // [esp+2A1h] [ebp-E3h]
  int v111; // [esp+2A5h] [ebp-DFh]
  __int16 v112; // [esp+2A9h] [ebp-DBh]
  char v113; // [esp+2ABh] [ebp-D9h]
  char v114[4]; // [esp+2ACh] [ebp-D8h]
  char v115[5]; // [esp+2B0h] [ebp-D4h]
  int v116; // [esp+2B5h] [ebp-CFh]
  int v117; // [esp+2B9h] [ebp-CBh]
  int v118; // [esp+2BDh] [ebp-C7h]
  int v119; // [esp+2C1h] [ebp-C3h]
  int v120; // [esp+2C5h] [ebp-BFh]
  __int16 v121; // [esp+2C9h] [ebp-BBh]
  char v122; // [esp+2CBh] [ebp-B9h]
  char v123[4]; // [esp+2CCh] [ebp-B8h]
  char v124[5]; // [esp+2D0h] [ebp-B4h]
  int v125; // [esp+2D5h] [ebp-AFh]
  int v126; // [esp+2D9h] [ebp-ABh]
  int v127; // [esp+2DDh] [ebp-A7h]
  int v128; // [esp+2E1h] [ebp-A3h]
  int v129; // [esp+2E5h] [ebp-9Fh]
  __int16 v130; // [esp+2E9h] [ebp-9Bh]
  char v131; // [esp+2EBh] [ebp-99h]
  char char_array_29_2[29]; // [esp+2ECh] [ebp-98h]
  __int16 v133; // [esp+309h] [ebp-7Bh]
  char v134; // [esp+30Bh] [ebp-79h]
  char char_array_29_1[29]; // [esp+30Ch] [ebp-78h]
  __int16 v136; // [esp+329h] [ebp-5Bh]
  char v137; // [esp+32Bh] [ebp-59h]
  char char_array_29_3[29]; // [esp+32Ch] [ebp-58h]
  __int16 v139; // [esp+349h] [ebp-3Bh]
  char v140; // [esp+34Bh] [ebp-39h]
  char char_array_29_4[29]; // [esp+34Ch] [ebp-38h]
  __int16 v142; // [esp+369h] [ebp-1Bh]
  char v143; // [esp+36Bh] [ebp-19h]
  char month_day; // [esp+36Ch] [ebp-18h]
  int v145; // [esp+36Dh] [ebp-17h]
  int v146; // [esp+380h] [ebp-4h]

  pThis = this;
  v41 = 0;
  v146 = 0;
  username = 0;
  v40 = sub_421680("@hbxy", 0);
  if ( v40 != -1 )
  {
    v33 = sub_421630((int)&v11, 0, v40);
    std::basic_string<char,std::char_traits<char>,std::allocator<char>>::operator=(v33);
    std::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string<char,std::char_traits<char>,std::allocator<char>>(&v11);
  }
  username = (const char *)get_username(&a3);
  userName = username;
  v25 = username + 1;
  userName += strlen(userName);
  v24 = ++userName - (username + 1);
  lenUsername = userName - (username + 1);
  month_day = 0;
  v145 = 0;
  strftime(&month_day, 5u, "%m%d", (const struct tm *)(pThis + 8));
  monthDay = &month_day;
  v23 = &v145;
  monthDay += strlen(monthDay);
  v21 = ++monthDay - (char *)&v145;
  lenMonthDay = monthDay - (char *)&v145;
  (*(void (**)(char *, const char *, ...))(*(_DWORD *)pThis + 4))(pThis, ">>> GetHBKey: %s >>>", &month_day);
  v18 = 1;
  SizeInBytes = lenMonthDay + lenUsername + 2;
  mem_17 = (char *)malloc(SizeInBytes);
  DstBuf = mem_17;
  memset(mem_17, 0, SizeInBytes);
  sprintf_s(DstBuf, SizeInBytes, "%c%s%s", pThis[4], username, &month_day);// "b177628979080516"
  bUsernameMonthDay = DstBuf;
  v16 = DstBuf + 1;
  bUsernameMonthDay += strlen(bUsernameMonthDay);
  len_bUsernameMonthDay = ++bUsernameMonthDay - (DstBuf + 1);
  md5_bUsernameMonthDay = md5_StrWithLength(DstBuf, bUsernameMonthDay - (DstBuf + 1));// 5e64fdaa6449e2abb9693f2757c11652
  (*(void (**)(char *, const char *, ...))(*(_DWORD *)pThis + 4))(
    pThis,
    "[HBKEY] mdata1: %s [%s]",
    DstBuf,
    md5_bUsernameMonthDay);
  memset(DstBuf, 0, SizeInBytes);
  sprintf_s(DstBuf, SizeInBytes, "%s%c%s", username, pThis[4], &month_day);// "17762897908b0516"
  username_b_MonthDay = DstBuf;
  v14 = DstBuf + 1;
  username_b_MonthDay += strlen(username_b_MonthDay);
  len_username_b_MonthDay = ++username_b_MonthDay - (DstBuf + 1);
  md5_username_b_MonthDay = (_DWORD *)md5_StrWithLength(DstBuf, username_b_MonthDay - (DstBuf + 1));// 16dffe496172e2fb1bdb9b2002bfb5a5
  (*(void (**)(char *, const char *, ...))(*(_DWORD *)pThis + 4))(
    pThis,
    "[HBKEY] mdata2: %s [%s]",
    DstBuf,
    md5_username_b_MonthDay);
  memset(DstBuf, 0, SizeInBytes);
  sprintf_s(DstBuf, SizeInBytes, "%s%s%c", username, &month_day, pThis[4]);// "177628979080516b"
  username_MonthDay_b = DstBuf;
  v12 = DstBuf + 1;
  username_MonthDay_b += strlen(username_MonthDay_b);
  len_username_MonthDay_b = ++username_MonthDay_b - (DstBuf + 1);
  md5_username_MonthDay_b = (_DWORD *)md5_StrWithLength(DstBuf, username_MonthDay_b - (DstBuf + 1));// 6614da7943beed0e7baafc0be7fb624c
  (*(void (**)(char *, const char *, ...))(*(_DWORD *)pThis + 4))(
    pThis,
    "[HBKEY] mdata3: %s [%s]",
    DstBuf,
    md5_username_MonthDay_b);
  memset(DstBuf, 0, SizeInBytes);
  sprintf_s(DstBuf, SizeInBytes, "%s%s%c", &month_day, username, pThis[4]);// "051617762897908b"
  monthDay_Username_b = DstBuf;
  v37 = DstBuf + 1;
  monthDay_Username_b += strlen(monthDay_Username_b);
  len_monthDay_Username_b = ++monthDay_Username_b - (DstBuf + 1);
  md5_monthDay_Username_b = (_DWORD *)md5_StrWithLength(DstBuf, monthDay_Username_b - (DstBuf + 1));// 2b28feebb48c0cb98b9f3da404fff646
  (*(void (**)(char *, const char *, ...))(*(_DWORD *)pThis + 4))(
    pThis,
    "[HBKEY] mdata4: %s [%s]",
    DstBuf,
    md5_monthDay_Username_b);
  md5_1 = 0;
  md5_2 = 0;
  md5_3 = 0;
  md5_4 = 0;
  if ( *(char *)(md5_bUsernameMonthDay + 1) % 2 )
  {
    md5_1 = md5_bUsernameMonthDay;
    md5_2 = md5_username_MonthDay_b;
    md5_3 = md5_username_b_MonthDay;
    md5_4 = md5_monthDay_Username_b;
  }
  else
  {
    md5_1 = md5_bUsernameMonthDay;
    md5_2 = md5_monthDay_Username_b;
    md5_3 = md5_username_b_MonthDay;
    md5_4 = md5_username_MonthDay_b;
  }
  hbKeyGa = 0;
  memset(&mem_64_a, 0, 0x40u);
  md5_1_pLus3remainder4 = *(char *)(md5_1 + 3) % 4;
  // 以下一连串的赋值是使 char_array_29_1 = md5_1, char_array_29_2 = md5_2
  char_array_29_1[0] = 0;
  *(_DWORD *)&char_array_29_1[1] = 0;
  *(_DWORD *)&char_array_29_1[5] = 0;
  *(_DWORD *)&char_array_29_1[9] = 0;
  *(_DWORD *)&char_array_29_1[13] = 0;
  *(_DWORD *)&char_array_29_1[17] = 0;
  *(_DWORD *)&char_array_29_1[21] = 0;
  *(_DWORD *)&char_array_29_1[25] = 0;
  v136 = 0;
  v137 = 0;
  char_array_29_2[0] = 0;
  *(_DWORD *)&char_array_29_2[1] = 0;
  *(_DWORD *)&char_array_29_2[5] = 0;
  *(_DWORD *)&char_array_29_2[9] = 0;
  *(_DWORD *)&char_array_29_2[13] = 0;
  *(_DWORD *)&char_array_29_2[17] = 0;
  *(_DWORD *)&char_array_29_2[21] = 0;
  *(_DWORD *)&char_array_29_2[25] = 0;
  v133 = 0;
  v134 = 0;
  *(_DWORD *)char_array_29_1 = *(_DWORD *)md5_1;
  *(_DWORD *)&char_array_29_1[4] = *(_DWORD *)(md5_1 + 4);
  *(_DWORD *)&char_array_29_1[8] = *(_DWORD *)(md5_1 + 8);
  *(_DWORD *)&char_array_29_1[12] = *(_DWORD *)(md5_1 + 12);
  *(_DWORD *)&char_array_29_1[16] = *(_DWORD *)(md5_1 + 16);
  *(_DWORD *)&char_array_29_1[20] = *(_DWORD *)(md5_1 + 20);
  *(_DWORD *)&char_array_29_1[24] = *(_DWORD *)(md5_1 + 24);
  *(_DWORD *)&char_array_29_1[28] = *(_DWORD *)(md5_1 + 28);
  *(_DWORD *)char_array_29_2 = *md5_2;
  *(_DWORD *)&char_array_29_2[4] = md5_2[1];
  *(_DWORD *)&char_array_29_2[8] = md5_2[2];
  *(_DWORD *)&char_array_29_2[12] = md5_2[3];
  *(_DWORD *)&char_array_29_2[16] = md5_2[4];
  *(_DWORD *)&char_array_29_2[20] = md5_2[5];
  *(_DWORD *)&char_array_29_2[24] = md5_2[6];
  *(_DWORD *)&char_array_29_2[28] = md5_2[7];
  v81 = md5_1_pLus3remainder4;                  // 0
  v82 = abs(md5_1_pLus3remainder4 - 5) % 4;     // 1
  v8 = (md5_1_pLus3remainder4 + 2) % 4;         // 2
  v83 = (md5_1_pLus3remainder4 + 2) % 4;        // 2
  v84 = abs(md5_1_pLus3remainder4 - 3);         // 3
  v96[0] = 0;
  *(_DWORD *)&v96[1] = 0;
  *(_DWORD *)&v97[1] = 0;
  v98 = 0;
  v99 = 0;
  v100 = 0;
  v101 = 0;
  v102 = 0;
  v103 = 0;
  v104 = 0;
  v105[0] = 0;
  *(_DWORD *)&v105[1] = 0;
  *(_DWORD *)&v106[1] = 0;
  v107 = 0;
  v108 = 0;
  v109 = 0;
  v110 = 0;
  v111 = 0;
  v112 = 0;
  v113 = 0;
  *(_DWORD *)v96 = *(_DWORD *)&char_array_29_1[8 * md5_1_pLus3remainder4];
  *(_DWORD *)v97 = *(_DWORD *)&char_array_29_1[8 * md5_1_pLus3remainder4 + 4];
  *(_DWORD *)&v97[4] = *(_DWORD *)&char_array_29_2[8 * v82];
  *(int *)((char *)&v98 + 3) = *(_DWORD *)&char_array_29_2[8 * v82 + 4];
  *(int *)((char *)&v99 + 3) = *(_DWORD *)&char_array_29_1[8 * v8];
  *(int *)((char *)&v100 + 3) = *(_DWORD *)&char_array_29_1[8 * v8 + 4];
  *(int *)((char *)&v101 + 3) = *(_DWORD *)&char_array_29_2[8 * v84];
  *(int *)((char *)&v102 + 3) = *(_DWORD *)&char_array_29_2[8 * v84 + 4];
  *(_DWORD *)v105 = *(_DWORD *)&char_array_29_2[8 * md5_1_pLus3remainder4];
  *(_DWORD *)v106 = *(_DWORD *)&char_array_29_2[8 * md5_1_pLus3remainder4 + 4];
  *(_DWORD *)&v106[4] = *(_DWORD *)&char_array_29_1[8 * v82];
  *(int *)((char *)&v107 + 3) = *(_DWORD *)&char_array_29_1[8 * v82 + 4];
  *(int *)((char *)&v108 + 3) = *(_DWORD *)&char_array_29_2[8 * v8];
  *(int *)((char *)&v109 + 3) = *(_DWORD *)&char_array_29_2[8 * v8 + 4];
  *(int *)((char *)&v110 + 3) = *(_DWORD *)&char_array_29_1[8 * v84];
  *(int *)((char *)&v111 + 3) = *(_DWORD *)&char_array_29_1[8 * v84 + 4];
  mix_md5_1 = (void *)md5_StrWithLength(v96, 32);// 第一个参数  5e64fdaa43beed0eb9693f27e7fb624c6614da796449e2ab7baafc0b57c11652  
                                                // 返回值  5008ef506febfc228802dd43b99c1869
                                                // 为 5e64fdaa43beed0eb9693f27e7fb624c 的 md5
  mix_md5_2 = (void *)md5_StrWithLength(v105, 32);// 第一个参数  6614da796449e2ab7baafc0b57c11652
                                                // 返回值  46e4a9da513469a20da82e3136f46951
  sprintf_s(&hbKeyGa, 0x41u, "%s%s", mix_md5_1, mix_md5_2);// hbKeyGa = "5008ef506febfc228802dd43b99c186946e4a9da513469a20da82e3136f46951"
  lp_mix_md5_1 = mix_md5_1;
  j_j___free_base(mix_md5_1);
  if ( lp_mix_md5_1 )
  {
    mix_md5_1 = (void *)33059;
    v35 = 33059;
  }
  else
  {
    v35 = 0;
  }
  v44 = mix_md5_2;
  j_j___free_base(mix_md5_2);
  if ( v44 )
  {
    mix_md5_2 = (void *)33059;
    v34 = 33059;
  }
  else
  {
    v34 = 0;
  }
  (*(void (**)(char *, const char *, ...))(*(_DWORD *)pThis + 4))(pThis, "[HBKEY] ga: %s", &hbKeyGa);
  hbKeyGb = 0;
  memset(&mem_64_b, 0, 0x40u);
  md5_4_plus5remainer4 = *((char *)md5_4 + 5) % 4;
  // 以下一连串的赋值是使 char_array_29_3 = md5_3, char_array_29_4 = md5_4
  char_array_29_3[0] = 0;
  *(_DWORD *)&char_array_29_3[1] = 0;
  *(_DWORD *)&char_array_29_3[5] = 0;
  *(_DWORD *)&char_array_29_3[9] = 0;
  *(_DWORD *)&char_array_29_3[13] = 0;
  *(_DWORD *)&char_array_29_3[17] = 0;
  *(_DWORD *)&char_array_29_3[21] = 0;
  *(_DWORD *)&char_array_29_3[25] = 0;
  v139 = 0;
  v140 = 0;
  char_array_29_4[0] = 0;
  *(_DWORD *)&char_array_29_4[1] = 0;
  *(_DWORD *)&char_array_29_4[5] = 0;
  *(_DWORD *)&char_array_29_4[9] = 0;
  *(_DWORD *)&char_array_29_4[13] = 0;
  *(_DWORD *)&char_array_29_4[17] = 0;
  *(_DWORD *)&char_array_29_4[21] = 0;
  *(_DWORD *)&char_array_29_4[25] = 0;
  v142 = 0;
  v143 = 0;
  *(_DWORD *)char_array_29_3 = *md5_3;
  *(_DWORD *)&char_array_29_3[4] = md5_3[1];
  *(_DWORD *)&char_array_29_3[8] = md5_3[2];
  *(_DWORD *)&char_array_29_3[12] = md5_3[3];
  *(_DWORD *)&char_array_29_3[16] = md5_3[4];
  *(_DWORD *)&char_array_29_3[20] = md5_3[5];
  *(_DWORD *)&char_array_29_3[24] = md5_3[6];
  *(_DWORD *)&char_array_29_3[28] = md5_3[7];
  *(_DWORD *)char_array_29_4 = *md5_4;
  *(_DWORD *)&char_array_29_4[4] = md5_4[1];
  *(_DWORD *)&char_array_29_4[8] = md5_4[2];
  *(_DWORD *)&char_array_29_4[12] = md5_4[3];
  *(_DWORD *)&char_array_29_4[16] = md5_4[4];
  *(_DWORD *)&char_array_29_4[20] = md5_4[5];
  *(_DWORD *)&char_array_29_4[24] = md5_4[6];
  *(_DWORD *)&char_array_29_4[28] = md5_4[7];
  v85 = md5_4_plus5remainer4;                   // 1
  v86 = abs(md5_4_plus5remainer4 - 5) % 4;      // 0
  v9 = (md5_4_plus5remainer4 + 2) % 4;          // 3
  v87 = (md5_4_plus5remainer4 + 2) % 4;         // 3
  v88 = abs(md5_4_plus5remainer4 - 3);          // 2
  v114[0] = 0;
  *(_DWORD *)&v114[1] = 0;
  *(_DWORD *)&v115[1] = 0;
  v116 = 0;
  v117 = 0;
  v118 = 0;
  v119 = 0;
  v120 = 0;
  v121 = 0;
  v122 = 0;
  v123[0] = 0;
  *(_DWORD *)&v123[1] = 0;
  *(_DWORD *)&v124[1] = 0;
  v125 = 0;
  v126 = 0;
  v127 = 0;
  v128 = 0;
  v129 = 0;
  v130 = 0;
  v131 = 0;
  *(_DWORD *)v114 = *(_DWORD *)&char_array_29_3[8 * md5_4_plus5remainer4];
  *(_DWORD *)v115 = *(_DWORD *)&char_array_29_3[8 * md5_4_plus5remainer4 + 4];
  *(_DWORD *)&v115[4] = *(_DWORD *)&char_array_29_4[8 * v86];
  *(int *)((char *)&v116 + 3) = *(_DWORD *)&char_array_29_4[8 * v86 + 4];
  *(int *)((char *)&v117 + 3) = *(_DWORD *)&char_array_29_3[8 * v9];
  *(int *)((char *)&v118 + 3) = *(_DWORD *)&char_array_29_3[8 * v9 + 4];
  *(int *)((char *)&v119 + 3) = *(_DWORD *)&char_array_29_4[8 * v88];
  *(int *)((char *)&v120 + 3) = *(_DWORD *)&char_array_29_4[8 * v88 + 4];
  *(_DWORD *)v123 = *(_DWORD *)&char_array_29_4[8 * md5_4_plus5remainer4];
  *(_DWORD *)v124 = *(_DWORD *)&char_array_29_4[8 * md5_4_plus5remainer4 + 4];
  *(_DWORD *)&v124[4] = *(_DWORD *)&char_array_29_3[8 * v86];
  *(int *)((char *)&v125 + 3) = *(_DWORD *)&char_array_29_3[8 * v86 + 4];
  *(int *)((char *)&v126 + 3) = *(_DWORD *)&char_array_29_4[8 * v9];
  *(int *)((char *)&v127 + 3) = *(_DWORD *)&char_array_29_4[8 * v9 + 4];
  *(int *)((char *)&v128 + 3) = *(_DWORD *)&char_array_29_3[8 * v88];
  *(int *)((char *)&v129 + 3) = *(_DWORD *)&char_array_29_3[8 * v88 + 4];
  v58 = (void *)md5_StrWithLength(v114, 32);    // 返回值 1ed63dc9a269d8705e297c03dcda7cf0
                                                // 为 6172e2fb2b28feeb02bfb5a58b9f3da4 的 md5
  v57 = (void *)md5_StrWithLength(v123, 32);    // 返回值 25928da86463ce9beba8110d2d514464
                                                // 为 b48c0cb916dffe4904fff6461bdb9b20 的 md5

  sprintf_s(&hbKeyGb, 0x41u, "%s%s", v58, v57); // hbKeyGb = "1ed63dc9a269d8705e297c03dcda7cf025928da86463ce9beba8110d2d514464"
  v43 = v58;
  j_j___free_base(v58);
  if ( v43 )
  {
    v58 = (void *)33059;
    v22 = 33059;
  }
  else
  {
    v22 = 0;
  }
  v42 = v57;
  j_j___free_base(v57);
  if ( v42 )
  {
    v57 = (void *)33059;
    v32 = 33059;
  }
  else
  {
    v32 = 0;
  }
  (*(void (**)(char *, const char *, ...))(*(_DWORD *)pThis + 4))(pThis, "[HBKEY] gb: %s", &hbKeyGb);
  if ( v95 % 2 )                                // 从反汇编中可看到 v95 为 hbkey_gb[7]
  {
    temp1 = 0;
    p_HbKeyGa = &hbKeyGa;
    pMem_64_a = &mem_64_a;
    p_HbKeyGa += strlen(p_HbKeyGa);
    lenHbKeyGa = ++p_HbKeyGa - &mem_64_a;
    len_HbKeyGa = p_HbKeyGa - &mem_64_a;
    while ( temp1 < len_HbKeyGa )               // 把 HbKeyGa 里面的小写字母全替换为大写
    {
      if ( *(&hbKeyGa + temp1) >= 97 && *(&hbKeyGa + temp1) <= 122 )
        *(&hbKeyGa + temp1) -= 32;
      ++temp1;
    }
  }
  else
  {
    temp2 = 0;
    p_HbKeyGb = &hbKeyGb;
    pMem_64_b = &mem_64_b;
    p_HbKeyGb += strlen(p_HbKeyGb);
    lenHbKeyGb = ++p_HbKeyGb - &mem_64_b;
    len_HbKeyGb = p_HbKeyGb - &mem_64_b;
    while ( temp2 < len_HbKeyGb )               // 把 HbKeyGb 里面的小写字母全替换为大写
    {
      if ( *(&hbKeyGb + temp2) >= 97 && *(&hbKeyGb + temp2) <= 122 )
        *(&hbKeyGb + temp2) -= 32;
      ++temp2;
    }
  }
  pHbKeyGa = &hbKeyGa;
  pHbKeyGb = &hbKeyGb;
  (*(void (**)(char *, const char *, ...))(*(_DWORD *)pThis + 4))(pThis, "[HBKEY] sga: %s", &hbKeyGa);
  (*(void (**)(char *, const char *, ...))(*(_DWORD *)pThis + 4))(pThis, "[HBKEY] sgb: %s", pHbKeyGb);
  hbKey = 0;
  memset(&v90, 0, 0x80u);
  if ( pHbKeyGb[9] % 2 )
  {
    index1 = 0;
    index2 = 0;
    index3 = 63;
    while ( index1 < 128 )
    {
      *(&hbKey + index1++) = pHbKeyGa[index2++];
      *(&hbKey + index1++) = pHbKeyGb[index3--];
    }
  }
  else
  {
    index4 = 0;
    index5 = 63;
    index6 = 0;
    while ( index4 < 128 )
    {
      *(&hbKey + index4++) = pHbKeyGa[index5--];
      *(&hbKey + index4++) = pHbKeyGb[index6++];
    }
  }
  (*(void (**)(char *, const char *, ...))(*(_DWORD *)pThis + 4))(pThis, "[HBKEY] key: %s", &hbKey);// hbKey = &"115e9d6643Fd6c391a32E6298dA8D70025Ae9269473c1053AdDc9dAa47Ec6f4092658912C89d9aB83644D6D32c0e898b2e2bCaF8B1E1F06d025dF5E184040654"
  sub_40EC40((void *)a2, &hbKey);
  v41 |= 1u;
  v146 = -1;
  std::basic_string<char,std::char_traits<char>,std::allocator<char>>::~basic_string<char,std::char_traits<char>,std::allocator<char>>(&a3);
  return a2;
}
```

上面的就是 AidcRes.generateKey 的整个流程，这个坑多并且复杂，简要说一下，具体看代码（b_Username_MonthDay 代指 'b177111122220517'，不再赘述）
1. 算出 b_Username_MonthDay，username_b_MonthDay，username_MonthDay_b，monthDay_Username_b 四个东西的 md5
2. 根据 d5_b_Username_MonthDay[1] 的 ascii的奇偶性，重排四个 md5 的顺序并复制给四个变量，分别为 md5_1，md5_2，md5_3，md5_4，
3. 此时会用到第二步的四个变量，根据他们的特定位来计算得出 hbkey_ga 与 hbkey_gb 的值
   - 根据 `md5_1_pLus3remainder4 = *(char *)(md5_1 + 3) % 4;` 这步的值取 md5_1 和 md5_2 排列算出 hbkey_ga
   - 根据 `md5_4_plus5remainer4 = *((char *)md5_4 + 5) % 4;` 这步的值取 md5_3 和 md5_4 排列算出 hbkey_gb
4. 根据 hbkey_gb[7] 的 ascii，如果奇数就把 hbkey_ga 中的字母都大写，偶数就把 hbkey_gb 中的字母都大写
5. 根据 hbkey_gb[9] 的 ascii 的奇偶性对 hbkey_ga 与 hbkey_gb 的值用简单算法进行重排，得到真实的 hbkey

这就是上面所有代码的大致流程，代码中我也有大量注释，大家可以看看。

## 总结

这个难点在分析算法上面，分析算法主要还是要靠动态调试，过程中遇到了很多很难的地方，参数和函数的重命名主要还是靠动态调试，
然后去猜测它的作用进行重命名。  

这些文件我都保存了分析记录，大家可以跟着看看，总结如下

AidcComm.idb 看导出表可以看出是干嘛的，直接点进GetPWD即可看到我的分析
AidcRes.idb 里面也有我的分析，具体查看我改过的函数名 generateKey，然后 x 一下看调用地方
x32dbg_AidcRes.dd32 为我在用 x32dbg 分析AidcRes.exe的时候的记录，有一些我改过的函数名以及简要分析
简单的分析流程为 bp LoadLibrary，断到 AidcComm.dll，然后具体看eax和栈的变化，找到加密函数，再一层一层分析。

建议 ida 与 x32dbg 结合分析，最好起个 pppoe 服务器拦截账号密码协助分析，见我上一篇文章 [PPPoE中间人拦截以及校园网突破漫谈](https://www.anquanke.com/post/id/178484)中的代码。

调用流程为
AidcRes.generateKey(分析大头) --> AidcComm.GetRegularAccount --> AidcComm.GetPWD --> AidcComm.encryptPwdWithKey(分析大头，注意里面有个地方 f5 显示不出来，就是把一个key中的字母全大写的那部分，请结合汇编分析)

AidcRes.generateKey大致流程，这个坑多并且复杂，简要说一下，具体看代码
（b_Username_MonthDay 代指 'b177111122220517'，不再赘述）
1. 算出 b_Username_MonthDay，username_b_MonthDay，username_MonthDay_b，monthDay_Username_b 四个东西的 md5
2. 根据 d5_b_Username_MonthDay[1] 的 ascii的奇偶性，重排四个 md5 的顺序并复制给四个变量
3. 此时会用到第二步的四个变量，根据他们的特定位来计算得出 hbkey_ga 与 hbkey_gb 的值
4. 根据 hbkey_gb[7] 的 ascii，如果奇数就把 hbkey_ga 中的字母都大写，偶数就把 hbkey_gb 中的字母都大写
5. 根据 hbkey_gb[9] 的 ascii 的奇偶性对 hbkey_ga 与 hbkey_gb 的值用简单算法进行重排，得到真实的 hbkey

AidcComm.encryptPwdWithKey大致流程
1. password 用 key RC4 一下得到 A
2. 把 A md5 一下得到 B，如果第 11 位为奇数，取 B 的前 16 位，偶数就后 16 位，得到 C
3. C 再用 key RC4 一下得到 D
4. D 再 md5 一下，取 [8:24]得到 E
5. E[今天几号日期 % 16] 替换为 'b' 得到最后的密码

为了防止被商业利用，就不公开逆向得出的加密脚本了，喜欢折腾校园网的可以自行根据本文摸索。

## 分析文件打包

- [飞Young宽带_带分析.7z](https://www.lanzous.com/i48toqb)