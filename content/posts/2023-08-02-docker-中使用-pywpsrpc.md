---
layout: blog
title: docker 中使用 pywpsrpc
date: 2023-08-02T08:39:33.909Z
showToc: true
draft: false
cover:
  # only hide on current single page
  hidden: false
---
一般如果使用带桌面环境的 docker，比如 dorowu/ubuntu-desktop-lxde-vnc，然后安装 wps 后，使用 https://github.com/timxx/pywpsrpc 是没啥问题的，需要注意的是 wps 第一次打开后，需要同意 EULA，然后按照 [https://github.com/timxx/pywpsrpc/issues/44#issuecomment-1032304847](https://github.com/timxx/pywpsrpc/issues/44#issuecomment-1032304847) 中提到的改为 multi-module mode，然后就可以愉快使用了，但是对于无图形环境的 docker，似乎是连 wps 都无法启动

## 解决WPS无法启动的问题

wps安装之前需要安装一些依赖环境，这个后文给出完整的安装流程，此处主要解决 wps 安装完成后，启动无输出，直接闪退的问题

此处安装 [https://github.com/timxx/pywpsrpc/wiki/Run-on-Server](https://github.com/timxx/pywpsrpc/wiki/Run-on-Server) 配置了环境，但是wps依旧闪退

首先执行 `whereis wps` ，我们找到 wps 的执行文件路径，一般位于 `/usr/bin/wps`

然后我们编辑该文件

```docker
function run()
{
        oldPwd="${PWD}"
        if [ -e "${gInstallPath}/office6/${gApp}" ] ; then
                if [ 1 -eq ${gDaemon} ]; then
                        nohup ${gInstallPath}/office6/${gApp} ${gOpt} > /dev/null 2>&1 &
                elif [ 1 -eq ${gIsUrl} ]; then
                        { ${gInstallPath}/office6/${gApp}  ${gOptExt} ${gOpt} "${gFilePaths[@]}"; } > /dev/null 2>&1
                elif [ 1 -eq ${gIsFushion} ] && [ "$1" != "/prometheus" ]; then
                        { unset GIO_LAUNCHED_DESKTOP_FILE && ${gInstallPath}/office6/${gApp} /prometheus ${gOptExt} ${gOpt} "$@"; } > /dev/null 2>&1
                else
                        { ${gInstallPath}/office6/${gApp}  ${gOptExt} ${gOpt} "$@"; }
                fi
        else
                echo "${gApp} does not exist!"
        fi
}
```

将最后一个 else 的输出重定向去除，此时我们再运行 wps 就有报错输出了

```
dlopen /opt/kingsoft/wps-office/office6/libwpsmain.so failed , error: libxslt.so.1: cannot open shared object file: No such file or directory
```

然后我们运行下面的命令来解决他

```
apt-get install -y libxslt1.1
```

然后再运行wps即可，如果还是有缺失的问题，继续找补

或者可以直接运行 `xvfb-run /opt/kingsoft/wps-office/office6/wps` 来看报错

## 整体安装流程(for ubuntu)

```bash
apt-get install -y wget
# 下载 deb 安装包
wget https://wps-linux-personal.wpscdn.cn/wps/download/ep/Linux2019/11698/wps-office_11.1.0.11698_amd64.deb
# 防止 debconf (no usable dialog-like program 报错 ref:https://www.kaijia.me/2015/09/unable-to-initialize-frontend-dialog-issue-solved/
apt-get install -y dialog
# 安装 wps 所需依赖（安装wps时需要）
apt-get install -y bsdmainutils xdg-utils
# 安装 wps
apt-get install -y ./wps-office_11.1.0.11698_amd64.deb
# 安装运行 wps 时的依赖
apt-get install -y libxslt1.1 qtbase5-dev
# 安装虚拟显示器
apt-get install -y xvfb
# 使用 xvfb 来运行 wps
xvfb-run wps
```

但是此时如果你使用 pywpsrpc，还是启动不起来的

需要同意 wps 的 EULA 并且将 wps 改为多组件模式

```bash
# 将 wps 改为多组件模式
echo 'wpsoffice\Application%20Settings\AppComponentMode=prome_independ' >> ~/.config/Kingsoft/Office.conf
echo 'wpsoffice\Application%20Settings\AppComponentModeInstall=prome_independ' >> ~/.config/Kingsoft/Office.conf
# 同意 wps 的EULA
echo 'common\AcceptedEULA=true' >> ~/.config/Kingsoft/Office.conf
```

注意此时调用 pywpsrpc 其实还会出现一个错误

```
/tmp/64742_asso/assocheck.sh: line 18: gvfs-info: command not found
/tmp/64742_asso/assocheck.sh: line 19: gvfs-mime: command not found
/tmp/13013_desktop/desktopcheck.sh: line 23: gvfs-info: command not found
/tmp/13013_desktop/desktopcheck.sh: line 24: gvfs-mime: command not found
```

测试后感觉该错误不影响使用，如果在意的话可以通过 `apt install gvfs-bin` 来解决

## 封装的 Docker

为了更精简，qtbase5-dev 可替换为 libqt5gui5

但注意，导入使用 pywpsrpc 时可能会报错 `ImportError: libQt5Xml.so.5: cannot open shared object file: No such file or directory` ，还需要安装 `libQt5Xml`

```bash
apt-get install -y libqt5xml5
```

如果不差空间，使用 pywpsrpc 前更建议安装 qtbase5-dev

根据上面的测试，我做了一个镜像

该镜像只安装了 wps，并且做好了可使用的配置，可参照readme进行使用

[https://github.com/akkuman/headless-wps](https://github.com/akkuman/headless-wps)

针对arm64的我也做了测试，结果发现实际上 wps 无法在 鲲鹏920+麒麟V10 上正常运行，当然，可能是因为这个系统内核的内存对齐比较特殊，连chrome也没法在这个系统上跑

## References

- https://github.com/timxx/pywpsrpc/issues/19#issuecomment-1075996867
- https://github.com/timxx/pywpsrpc/issues/44#issuecomment-1032304847
- https://github.com/timxx/pywpsrpc/wiki/Run-on-Server
