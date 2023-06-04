---
layout: blog
title: photoprism+rclone搭建
date: 2023-06-04T06:44:26.647Z
showToc: true
draft: false
description: 本文以onedrive为例使用rclone来搭建photoprism相册管理工具
cover:
  # only hide on current single page
  hidden: false
---
vps空间小，所以使用onedrive为例作为存储来搭建 photoprism

主要分为以下几步：

1. 使用rclone挂载onedrive
2. 部署photoprism

## 获得rclone.conf

首先在本地电脑上安装rclone

然后运行 `rclone config`

参照 [https://rclone.org/onedrive/](https://rclone.org/onedrive/) 进行远程配置

然后配置完成后，`~/.config/rclone/rclone.conf` 内容类似

```
[onedrive]
type = myonedrive
token = {"access_token":"EwCAA8l6BA1","token_type":"Bearer","refresh_token":"M.C106eExJ7edYrxNdb3","expiry":"2023-06-03T16:20:11.7705715+08:00"}
drive_id = 19fe142286d457
drive_type = personal
```

## docker plugin rclone配置

可按照下面，或者参见 [https://rclone.org/docker/](https://rclone.org/docker/)

首先创建两个文件夹

```bash
sudo mkdir -p /var/lib/docker-plugins/rclone/config
sudo mkdir -p /var/lib/docker-plugins/rclone/cache
```

然后安装 docker 插件 rclone

```bash
docker plugin install rclone/docker-volume-rclone:latest args="-v" --alias rclone --grant-all-permissions
```

然后将上面在本地电脑上生成的 rclone.conf 内容拷贝到 vps 的 `/var/lib/docker-plugins/rclone/config/rclone.conf` 文件中

## 部署 photoprism

docker-compose.yml

```yaml
version: '3.5'

# Example Docker Compose config file for PhotoPrism (Linux / AMD64)
#
# Note:
# - Running PhotoPrism on a server with less than 4 GB of swap space or setting a memory/swap limit can cause unexpected
#   restarts ("crashes"), for example, when the indexer temporarily needs more memory to process large files.
# - If you install PhotoPrism on a public server outside your home network, please always run it behind a secure
#   HTTPS reverse proxy such as Traefik or Caddy. Your files and passwords will otherwise be transmitted
#   in clear text and can be intercepted by anyone, including your provider, hackers, and governments:
#   https://docs.photoprism.app/getting-started/proxies/traefik/
#
# Setup Guides:
# - https://docs.photoprism.app/getting-started/docker-compose/
# - https://docs.photoprism.app/getting-started/raspberry-pi/
# - https://www.photoprism.app/kb/activation
#
# Troubleshooting Checklists:
# - https://docs.photoprism.app/getting-started/troubleshooting/
# - https://docs.photoprism.app/getting-started/troubleshooting/docker/
# - https://docs.photoprism.app/getting-started/troubleshooting/mariadb/
#
# CLI Commands:
# - https://docs.photoprism.app/getting-started/docker-compose/#command-line-interface
#
# All commands may have to be prefixed with "sudo" when not running as root.
# This will point the home directory shortcut ~ to /root in volume mounts.

services:
  photoprism:
    ## Use photoprism/photoprism:preview for testing preview builds:
    image: photoprism/photoprism:preview
    container_name: photoprism
    ## Don't enable automatic restarts until PhotoPrism has been properly configured and tested!
    ## If the service gets stuck in a restart loop, this points to a memory, filesystem, network, or database issue:
    ## https://docs.photoprism.app/getting-started/troubleshooting/#fatal-server-errors
    # restart: unless-stopped
    stop_grace_period: 10s
    security_opt:
      - seccomp:unconfined
      - apparmor:unconfined
    ports:
      - "12342:2342" # HTTP port (host:container)
    environment:
      PHOTOPRISM_ADMIN_USER: "admin"                 # 管理员登陆用户名
      PHOTOPRISM_ADMIN_PASSWORD: "密码"              # 管理员密码
      PHOTOPRISM_AUTH_MODE: "password"               # authentication mode (public, password)
      PHOTOPRISM_SITE_URL: "http://photoprism.me:12342/"  # 服务器url，格式： "http(s)://domain.name(:port)/(path)"
      PHOTOPRISM_ORIGINALS_LIMIT: 5000               # 文件大小限制 MB (increase for high-res video)
      PHOTOPRISM_HTTP_COMPRESSION: "gzip"            # improves transfer speed and bandwidth utilization (none or gzip)
      PHOTOPRISM_LOG_LEVEL: "info"                   # 日志等级: trace, debug, info, warning, error, fatal, or panic
      PHOTOPRISM_READONLY: "false"                   # do not modify originals directory (reduced functionality)
      PHOTOPRISM_EXPERIMENTAL: "true"               # enables experimental features
      PHOTOPRISM_DISABLE_CHOWN: "false"              # disables updating storage permissions via chmod and chown on startup
      PHOTOPRISM_DISABLE_WEBDAV: "false"             # disables built-in WebDAV server
      PHOTOPRISM_DISABLE_SETTINGS: "false"           # disables settings UI and API
      PHOTOPRISM_DISABLE_TENSORFLOW: "false"         # disables all features depending on TensorFlow
      PHOTOPRISM_DISABLE_FACES: "false"              # disables face detection and recognition (requires TensorFlow)
      PHOTOPRISM_DISABLE_CLASSIFICATION: "false"     # disables image classification (requires TensorFlow)
      PHOTOPRISM_DISABLE_VECTORS: "false"            # disables vector graphics support
      PHOTOPRISM_DISABLE_RAW: "false"                # disables indexing and conversion of RAW images
      PHOTOPRISM_RAW_PRESETS: "false"                # enables applying user presets when converting RAW images (reduces performance)
      PHOTOPRISM_JPEG_QUALITY: 85                    # a higher value increases the quality and file size of JPEG images and thumbnails (25-100)
      PHOTOPRISM_DETECT_NSFW: "false"                # automatically flags photos as private that MAY be offensive (requires TensorFlow)
      PHOTOPRISM_UPLOAD_NSFW: "true"                 # allows uploads that MAY be offensive (no effect without TensorFlow)
      PHOTOPRISM_DATABASE_DRIVER: "sqlite"         # SQLite is an embedded database that doesn't require a server
      PHOTOPRISM_SITE_CAPTION: ""
      PHOTOPRISM_SITE_DESCRIPTION: ""                # meta site description
      PHOTOPRISM_SITE_AUTHOR: ""                     # meta site author
      ## Run/install on first startup (options: update https gpu tensorflow davfs clitools clean):
      # PHOTOPRISM_INIT: "https gpu tensorflow"
      ## Hardware Video Transcoding:
      # PHOTOPRISM_FFMPEG_ENCODER: "software"        # FFmpeg encoder ("software", "intel", "nvidia", "apple", "raspberry")
      # PHOTOPRISM_FFMPEG_BITRATE: "32"              # FFmpeg encoding bitrate limit in Mbit/s (default: 50)
      ## Run as a non-root user after initialization (supported: 0, 33, 50-99, 500-600, and 900-1200):
      # PHOTOPRISM_UID: 1000
      # PHOTOPRISM_GID: 1000
      # PHOTOPRISM_UMASK: 0000
    ## Start as non-root user before initialization (supported: 0, 33, 50-99, 500-600, and 900-1200):
    # user: "1000:1000"
    ## Share hardware devices with FFmpeg and TensorFlow (optional):
    # devices:
    #  - "/dev/dri:/dev/dri"                         # Intel QSV
    #  - "/dev/nvidia0:/dev/nvidia0"                 # Nvidia CUDA
    #  - "/dev/nvidiactl:/dev/nvidiactl"
    #  - "/dev/nvidia-modeset:/dev/nvidia-modeset"
    #  - "/dev/nvidia-nvswitchctl:/dev/nvidia-nvswitchctl"
    #  - "/dev/nvidia-uvm:/dev/nvidia-uvm"
    #  - "/dev/nvidia-uvm-tools:/dev/nvidia-uvm-tools"
    #  - "/dev/video11:/dev/video11"                 # Video4Linux Video Encode Device (h264_v4l2m2m)
    working_dir: "/photoprism" # do not change or remove
    ## Storage Folders: "~" is a shortcut for your home directory, "." for the current directory
    volumes:
      # "/host/folder:/photoprism/folder"                # Example
      - "onedrive_photos:/photoprism/originals"               # Original media files (DO NOT REMOVE)
      # - "/example/family:/photoprism/originals/family" # *Additional* media folders can be mounted like this
      # - "photoprism_import:/photoprism/import"                  # *Optional* base folder from which files can be imported to originals
      - "./storage:/photoprism/storage"                  # *Writable* storage folder for cache, database, and sidecar files (DO NOT REMOVE)

  ## Watchtower upgrades services automatically (optional)
  ## see https://docs.photoprism.app/getting-started/updates/#watchtower
  ## activate via "COMPOSE_PROFILES=update docker compose up -d"
  watchtower:
    restart: unless-stopped
    image: containrrr/watchtower
    profiles: ["update"]
    environment:
      WATCHTOWER_CLEANUP: "true"
      WATCHTOWER_POLL_INTERVAL: 7200 # checks for updates every two hours
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock"
      - "~/.docker/config.json:/config.json" # optional, for authentication if you have a Docker Hub account

volumes:                               #储存卷配置：
  onedrive_photos:                     #卷名 onedrive_photos
    driver: rclone                     #磁盘名 rclone
    driver_opts:                       #磁盘配置
      remote: onedrive:/图片/本机照片   #同步 onedrive 下 /图片/本机照片 文件
      allow_other: 'true'              #类似rclone mount配置
      vfs_cache_mode: full             #类似rclone mount配置
```

如果你不需要自动更新photoprism版本，你可以去除 watchtower 的容器

一般onedrive默认情况下备份相册照片到 `/图片/本机照片` ，如果你有更改过，可以换成你更改的文件夹路径

然后使用 docker compose up -d 启动

访问在 docker-compose.yml 中定义的服务器url即可

上传图片的话，可以使用 photosync（官方推荐） 或者使用 syncthing，或者直接使用 onedrive 的同步功能

photosync是通过webdav功能来同步，photoprism只有当使用webdav同步时才会触发索引，所以syncthing或onedrive的同步都没法自动索引

所以需要手动使用命令进行触发，可以使用 crontab 来定时同步

```bash
crontab -e
# 设置每天晚上1点自动导入
0 1 * * * /usr/bin/docker exec photoprism photoprism index
```

或者你可以使用 syncthing + https://github.com/signalkraft/photoprism-syncthing-indexer 来自动索引

## 参考

[自建云相册PhotoPrism](https://wurang.net/photoprism/)

[Docker Volume Plugin](https://rclone.org/docker/)

[在Docker中使用Rclone作为储存卷](https://blog.learnonly.xyz/p/13d3.html)

[Microsoft OneDrive](https://rclone.org/onedrive/)

[Syncthing and photoprism](https://www.reddit.com/r/photoprism/comments/mjbr0a/syncthing_and_photoprism/)
