---
title: Bad owner or permissions on .ssh/config win10问题解决
date: 2019-07-15 10:35:06
categories: 
- 问题解决
tags: 
- 问题解决
---


最近向系统添加了新用户账号后出现了问题，尝试使用私钥登陆服务器，提示了 Bad owner or permissions on .ssh/config 这个报错，就是如题中的问题


![](https://raw.githubusercontent.com/akkuman/pic/master/img/1106918-20190715102859616-1893463244.png)

<!--more-->

## 修复

按照Windows 10 GUI中的这些步骤解决权限问题：

1. 找到.ssh文件夹。它通常位于C:\Users\，例如C:\Users\Akkuman。
2. 右键单击.ssh文件夹，然后单击“属性”。
3. 找到并点击“安全”标签。
4. 然后单击“高级”。
5. 单击“禁用继承”，单击“确定”。
6. 将出现警告弹出窗口。单击“从此对象中删除所有继承的权限”。
7. 你会注意到所有用户都将被删除。让我们添加所有者。在同一窗口中，单击“编辑”按钮。
8. 接下来，单击“添加”以显示“选择用户或组”窗口。
9. 单击“高级”，然后单击“立即查找”按钮。应显示用户结果列表。
10. 选择您的用户帐户。

![](https://raw.githubusercontent.com/akkuman/pic/master/img/微信截图_20190715111545.png)

11. 然后单击“确定”（大约三次）以关闭所有窗口。

完成所有操作后，再次关闭并打开cmder应用程序并尝试连接到远程SSH主机。

现在这个问题应该解决了。