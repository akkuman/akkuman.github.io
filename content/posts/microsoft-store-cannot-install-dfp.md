---
title: 微软商店一直安装不上Intel Media SDK DFP
date: 2019-08-30 20:11:00
tags:
- Tips
categories:
- Tips
---

具体表现为一直安装失败，但是下载进度条一直在，无法去除。

<!--more-->

此方法来自 https://answers.microsoft.com/en-us/windows/forum/all/error-code-0x80070057-when-installing-intel-media/725eff00-5f06-4336-8d41-2cb2f5999b88


1. If you are able to open MS Store, open MS Store > Click on your profile picture on top right and sign-out. Then sign-in again. 

2. Run Windows Store Apps Troubleshooter 
Windows Key+X > Click Settings > Click Update & security > Click Troubleshoot > Scroll down to the bottom > Click Windows Store Apps > Click Run the Troubleshooter 

3. Reset Windows Store through Command Prompt 
Type cmd in Windows Search box > Right click on Command Prompt > Run As Administrator > Type WSreset.exe and click Enter > Reboot your computer 

4. Re-register All Store apps (You will get many Reds, ignore them) 
Windows Key+X > Windows Powershell (Admin) > Copy the following from below and right click in Powershell to paste > Enter > Restart your computer 

Get-AppXPackage -AllUsers | Foreach {Add-AppxPackage -DisableDevelopmentMode -Register "$($_.InstallLocation)\AppXManifest.xml"} 

5. Uninstall & Reinstall Store 
Windows Key+X > Windows Powershell (Admin) > Copy the following from below and right click in Powershell to paste > Enter 

Get-AppxPackage -allusers Microsoft.WindowsStore | Remove-AppxPackage 

Copy the following from below and right click in Powershell to paste > Enter > Reboot your computer 

Get-AppxPackage -allusers Microsoft.WindowsStore | Foreach {Add-AppxPackage -DisableDevelopmentMode -Register “$($_.InstallLocation)\AppXManifest.xml”} 

    

这些一个个试，根据大家的反馈，基本第三个可以成功，我也是第三个方法成功的