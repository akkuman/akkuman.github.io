---
title: 湖北掌大协议拨号Python脚本
date: 2017-12-15 18:04:58
tags:
- life
- Python
categories:
- life
---

湖北定制版协议拨号  
本来之前我e信账号被加小黑屋就没弄了，没想到又被放出小黑屋了，可以上了  
据说1月份换协议，且用且珍惜，另外感谢[陈大的项目](https://github.com/miao1007/Openwrt-NetKeeper)

<!--more-->
使用的第三方库
```
requests
BeautifulSoup4
wxPython
```

支持老毛子固件（登录账号密码均为admin），如果不是老毛子请手动填写路由器wan口获取的ip
```python
import wx
import wx.xrc
import re
import sys
import os
import requests
import binascii
import time
from Cryptodome.Cipher import AES
from requests.auth import HTTPBasicAuth


###########################################################################
## Class MyFrame1
###########################################################################
class HubeiPortal:
    AES_KEY_PASSWORD = "pass012345678910"
    AES_KEY_SESSION = "jyangzi5@163.com"
    def __init__(self, username, password, localIpAddress, useragent):
        self.UserName = username
        self.Password = password
        self.Headers = {
            'Charset': 'UTF-8', 
            'Content-Type': 'application/x-www-form-urlencoded', 
            'App': 'HBZD', 
            'User-Agent': useragent,
            #'User-Agent': 'Mozilla/Android/6.0.1/SM-G9250/ffffffff-f56d-7f76-ffff-ffffd097bd08',
        }
        self.Host = '58.53.196.165:8080'
        self.LocalIpAddress = localIpAddress
        self.AccessToken = ''
        self.Cookie = {}

    def getSecret(self):
        url = 'http://' + self.Host + '/wf.do?clientType=android&code=1&version=6.0.1&clientip=' + self.LocalIpAddress
        # url=http://58.53.196.165:8080/wf.do?device=Phone%3ALetv+X620%5CSDK%3A23&clientType=android&code=1&version=6.0&clientip=100.64.64.76
        hRequest = requests.get(url, headers=self.Headers, timeout=10)
        self.AccessToken = self.parseToHtml(hRequest)
        self.Cookie['JSESSIONID'] = hRequest.cookies['JSESSIONID']
    
    def authenticate(self):
        url = 'http://' + self.Host + '/wf.do'
        postData = {
            'password': self.getPasswordEnc(self.Password), 
            'clientType': 'android', 
            'username': self.UserName, 
            'key': self.getSessionEnc(self.AccessToken), 
            'code': 8,
            'clientip': self.LocalIpAddress, 
        }
        hRequest = requests.post(url, data=postData, cookies=self.Cookie, headers=self.Headers)
        resp = self.parseToHtml(hRequest)
        return resp
        
    def getPasswordEnc(self, sPasswd):
        return self.toHex(self.aesEcbEnc(sPasswd, self.AES_KEY_PASSWORD))

    def getSessionEnc(self, sSession):
        return self.toHex(self.aesEcbEnc(sSession, self.AES_KEY_SESSION))

    def aesEcbEnc(self, sText, aes_key):
        aes_key = bytes(aes_key, encoding='utf-8')
        sText = bytes(sText, encoding='utf-8')
        cipher = AES.new(aes_key, AES.MODE_ECB)
        if len(sText) <= 16:
            while len(sText) % 16 != 0:
                sText += b'\n'
        else:
            while len(sText) % 48 != 0:
                sText += b'\x10'
        cipher_text = cipher.encrypt(sText)
        return cipher_text

    def toHex(self, sEncrypt):
        return binascii.b2a_hex(sEncrypt).decode('utf-8').upper()

    def parseToHtml(self, hRequest):
        return hRequest.text

    def Connect(self):
        self.getSecret()
        return self.authenticate()

class MyFrame1 ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"snk", pos = wx.DefaultPosition, size = wx.Size( 246,246 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
        
        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
        
        fgSizer2 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer2.SetFlexibleDirection( wx.BOTH )
        fgSizer2.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
        
        self.m_staticText2 = wx.StaticText( self, wx.ID_ANY, u"账号", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText2.Wrap( -1 )
        fgSizer2.Add( self.m_staticText2, 0, wx.ALL, 5 )
        
        self.m_textCtrl4 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        fgSizer2.Add( self.m_textCtrl4, 0, wx.ALL, 5 )
        
        self.m_staticText3 = wx.StaticText( self, wx.ID_ANY, u"密码", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText3.Wrap( -1 )
        fgSizer2.Add( self.m_staticText3, 0, wx.ALL, 5 )
        
        self.m_textCtrl5 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_PASSWORD )
        fgSizer2.Add( self.m_textCtrl5, 0, wx.ALL, 5 )
        
        self.m_staticText4 = wx.StaticText( self, wx.ID_ANY, u"UA", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText4.Wrap( -1 )
        fgSizer2.Add( self.m_staticText4, 0, wx.ALL, 5 )
        
        self.m_textCtrl6 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        fgSizer2.Add( self.m_textCtrl6, 0, wx.ALL, 5 )
        
        self.m_staticText5 = wx.StaticText( self, wx.ID_ANY, u"内网IP", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText5.Wrap( -1 )
        fgSizer2.Add( self.m_staticText5, 0, wx.ALL, 5 )
        
        self.m_textCtrl7 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        fgSizer2.Add( self.m_textCtrl7, 0, wx.ALL, 5 )
        
        self.m_checkBox1 = wx.CheckBox( self, wx.ID_ANY, u"记住信息", wx.DefaultPosition, wx.DefaultSize, 0 )
        fgSizer2.Add( self.m_checkBox1, 0, wx.ALL|wx.EXPAND, 5 )
        
        self.m_button1 = wx.Button( self, wx.ID_ANY, u"点击更新IP(需2s)", wx.DefaultPosition, wx.DefaultSize, 0 )
        fgSizer2.Add( self.m_button1, 0, wx.ALL|wx.EXPAND, 5 )

        self.m_button2 = wx.Button( self, wx.ID_ANY, u"开始连接", wx.DefaultPosition, wx.DefaultSize, 0 )
        fgSizer2.Add( self.m_button2, 0, wx.ALL|wx.EXPAND, 5 )
        
        
        self.SetSizer( fgSizer2 )
        self.Layout()
        
        self.Centre( wx.BOTH )
        
        # Connect Events
        r_internet = requests.get('http://192.168.1.1/status_wanlink.asp', headers={'Authorization':'Basic YWRtaW46YWRtaW4='})
        ip4_wan = re.search(r"function\ wanlink\_ip4\_wan\(\)\ \{ return\ \'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\'\;\}", r_internet.text).group(1)
        self.m_textCtrl7.SetValue(ip4_wan)

        # get info from config file
        if os.path.exists("SnkGui.ini"):
            for line in open("SnkGui.ini",'r'):
                config = line.split(' : ')
                if config[0] == 'username':
                    self.m_textCtrl4.SetValue(config[1].strip())
                if config[0] == 'password':
                    self.m_textCtrl5.SetValue(config[1].strip())
                if config[0] == 'useragent':
                    self.m_textCtrl6.SetValue(config[1].strip())
        self.m_checkBox1.Bind( wx.EVT_CHECKBOX, self.SaveConfig )
        self.m_button1.Bind( wx.EVT_BUTTON, self.getWANIP4 )
        self.m_button2.Bind( wx.EVT_BUTTON, self.Connect )
    
    def __del__( self ):
        pass
    
    
    # Virtual event handlers, overide them in your derived class
    def SaveConfig( self, event ):
        with open("SnkGui.ini",'w') as f:
            config = []
            config.append('username : '+self.m_textCtrl4.GetValue() + '\n')
            config.append('password : '+self.m_textCtrl5.GetValue() + '\n')
            config.append('useragent : '+self.m_textCtrl6.GetValue() + '\n')
            f.writelines(config)
    
    # get ip4_wan from 192.168.1.1(老毛子路由器)
    def getWANIP4( self, event ):
        headers = {
			# 其中YWRtaW46YWRtaW4=是admin:admin（路由器账号密码）的base64编码，可以自己根据格式进行编码修改
            'Authorization' : 'Basic YWRtaW46YWRtaW4=',
        }
        payload = {
            'wan_action' : 'Connect', 
            'modem_prio' : '1',
        }
        r_reconnect = requests.post('http://192.168.1.1/device-map/wan_action.asp', headers=headers, data=payload)
        time.sleep(2)
        r_internet = requests.get('http://192.168.1.1/status_wanlink.asp', headers=headers)
        ip4_wan = re.search(r"function\ wanlink\_ip4\_wan\(\)\ \{ return\ \'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\'\;\}", r_internet.text).group(1)
        self.m_textCtrl7.SetValue(ip4_wan)


    def Connect( self, event ):
        username = self.m_textCtrl4.GetValue()
        password = self.m_textCtrl5.GetValue()
        localIpAddress = self.m_textCtrl7.GetValue()
        useragent = self.m_textCtrl6.GetValue()
        eXin = HubeiPortal(username,password,localIpAddress,useragent)
        ConnInfo = eXin.Connect()
        if "auth00" in ConnInfo:
            wx.MessageBox(u"连接成功")
        else:
            wx.MessageBox(ConnInfo)


def main():
    app = wx.App(False) 
    frame = MyFrame1(None) 
    frame.Show(True) 
    #start the applications 
    app.MainLoop() 

if __name__ == '__main__':
    main()
```


供测试UA
```
Mozilla/Android/6.0.1/SM-G925f/ffffffff-f78d-7f76-ffff-ffffd097bd08
```
其中SM-G925f(格式不限)与ffffffff-f78d-7f76-ffff-ffffd097bd08(格式需相同)均可修改

如果不是老毛子，ip获取不到，直接手动填写ip即可

![](https://raw.githubusercontent.com/akkuman/pic/master/img/c0264382gy1fmhmk6pu9zj206u06uq34.jpg)
