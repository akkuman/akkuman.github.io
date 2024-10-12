---
categories:
- 工具
date: '2021-12-10T09:00:00.000Z'
showToc: true
tags:
- 工具
- 笔记
title: 自建bitwarden备份同步到坚果云

---



因为bitwarden的氪金玩家才能使用双因子认证，恰好手上有个vps，搭建个bitwarden服务端来使用2fa

## 自建bitwarden

vps比较垃圾，所以选用一个资源开销比较小的服务端比较有必要，我这里选择的是 [https://github.com/mprasil/bitwarden_rs](https://github.com/mprasil/bitwarden_rs)

这里采用 docker-compose 进行部署

```yaml
version: '3'

services:
  bitwarden:
    image: bitwardenrs/server:latest
    container_name: bitwarden
    restart: unless-stopped
    volumes:
      - ./bw-data:/data
    environment:
      - WEBSOCKET_ENABLED=true
      - SIGNUPS_ALLOWED=true
      - WEB_VAULT_ENABLED=true
      - ADMIN_TOKEN=xxxxxxxxxxxxxxxxxxxx
    ports:
      - "127.0.0.1:8889:80"
      - "127.0.0.1:8810:3012"
```

其中的3012是websocket通知端口

- `WEBSOCKET_ENABLED` 代表启用 websocket

- `SIGNUPS_ALLOWED` 代表是否启用注册

- `WEB_VAULT_ENABLED` 代表是否启用web界面

- `ADMIN_TOKEN` 是管理界面的密码，用来启用管理界面，启用后可通过 `[https://你的域名/admin](https://你的域名/admin)` 进行访问

然后我们需要创建一个反向代理，这里我使用的是 nginx，下面给出 nginx 配置

```yaml
upstream bitwarden-default { server 127.0.0.1:8889; }
upstream bitwarden-ws { server 127.0.0.1:8810; }

server {
    listen 80;
    listen [::]:80;
    server_name bitwarden.example.tld;

    client_max_body_size 128M;

    # reverse proxy
    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_pass http://bitwarden-default;
    }

    location /notifications/hub/negotiate {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_pass http://bitwarden-default;
    }

    location /notifications/hub {
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $http_connection;
        proxy_set_header X-Real-IP $remote_addr;

        proxy_pass http://bitwarden-ws;
    }
}
```

你现在可以访问域名看看界面了

当然，现在还只是http，http协议下bitwarden是不允许进行一些密码操作的，你可以配置证书接入ssl，或者使用cloudflare接入ssl

注册完自己的用户后建议修改上面的 `SIGNUPS_ALLOWED` 然后重启docker关闭注册。

然后你可以使用bitwarden的客户端了

## 创建挂载目录备份数据

密码数据最好备份一下，要是哪天vps坏了就gg了

bitwarden_rs的数据库是sqlite3，直接打包压缩备份，然后同步到坚果云

### 坚果云配置webdav

首先我们在坚果云后端创建一个备份应用，点击进入 `账户信息 - 安全选项`

![](https://raw.githubusercontent.com/akkuman/pic/master/notionimg/ee/d4/eed4420ab0cd95b0a601d58d9f6a8c89.png)

然后点击下面的添加应用，随便填写一个名字，然后复制生成的应用密码

然后在坚果云根目录下创建一个目录名为 `bitwarden_backup` 作为我们后续的同步文件夹

### 服务器挂载webdav

首先安装rclone，为什么使用rclone而不是davfs2，主要是因为davfs2不支持 vfs 缓存（将直接从远程读取并直接写入远程），对于后续的同步会有比较大的问题（主要是同步程序对于文件的操作）

```shell
curl https://rclone.org/install.sh | sudo bash
```

挂载需要使用fuse，所以需要安装一下

```shell
apt install fuse
```

然后使用 `rclone config` 配置webdav

然后创建目录进行挂载

```shell
mkdir /mnt/rclone_bitwarden_backup

#挂载
#rclone mount <网盘名称:网盘路径> <本地路径> [参数] --daemon
#取消挂载
#fusermount -qzu <本地路径>

rclone mount jianguoyun:/bitwarden_backup /mnt/rclone_bitwarden_backup --allow-non-empty --daemon --vfs-cache-mode full --log-file /var/log/rclone_bitwarden_backup.lo
```

上面的是手动挂载，如果你希望开机自动挂载可以查看 [Rclone 使用教程 - 挂载 OneDrive、Google Drive 等网盘(Linux)](https://p3terx.com/archives/linux-vps-uses-rclone-to-mount-network-drives-such-as-onedrive-and-google-drive.html)

### 监听文件变化进行同步

其实也可以直接将上面的 `docker-compose` 挂载目录设置到webdav的挂载目录上去，但是icon_cache这个目录下很多文件，调用webdav次数过多会触发坚果云风控，如果不在意的话也可以采取该方案

我这里采用 `inotify` 进行监控同步的方案

首先安装 `rsync`和`inotifywait`

```shell
apt install -y rsync inotify-tools
```

然后监控文件变更，同步到webdav的挂载目录

```shell
inotifywait -mrq --timefmt '%d/%m/%y %H:%M' --format '%T %w %f %e' -e modify,create,delete,move /root/bitwarden_rs/bw-data | while read -r event; do rsync -aHv --exclude icon_cache /root/bitwarden_rs/bw-data/ /mnt/rclone_bitwarden_backup/; done
```

注意该命令最好使用tmux之类的程序来启动，因为需要跑在后台

## 后记

发现监听变化就同步，坚果云的上传流量用得太猛了，所以还是采用了crontab定时同步的方案

## 参考链接

- [https://rs.bitwarden.in/configuration/enabling-websocket-notifications](https://rs.bitwarden.in/configuration/enabling-websocket-notifications)

- [https://gythialy.github.io/deploy-bitwarden-rs-with-traefik/](https://gythialy.github.io/deploy-bitwarden-rs-with-traefik/)

- [https://github.com/dani-garcia/vaultwarden/wiki/Proxy-examples](https://github.com/dani-garcia/vaultwarden/wiki/Proxy-examples)

- [https://pianshen.com/article/4173217148/](https://pianshen.com/article/4173217148/)

- [https://p3terx.com/archives/linux-vps-uses-rclone-to-mount-network-drives-such-as-onedrive-and-google-drive.html](https://p3terx.com/archives/linux-vps-uses-rclone-to-mount-network-drives-such-as-onedrive-and-google-drive.html)

- [https://rclone.org/commands/rclone_mount/#vfs-cache-mode-full](https://rclone.org/commands/rclone_mount/#vfs-cache-mode-full)

- [https://www.myfreax.com/how-to-exclude-files-and-directories-with-rsync/](https://www.myfreax.com/how-to-exclude-files-and-directories-with-rsync/)

- [https://segmentfault.com/a/1190000038351925](https://segmentfault.com/a/1190000038351925)

