---
title: 国产化系统的适配
slug: adaptation-of-domesticization-system-oo8gs
url: /post/adaptation-of-domesticization-system-oo8gs.html
date: '2024-10-10 16:39:09+08:00'
lastmod: '2024-10-11 17:50:28+08:00'
toc: true
isCJKLanguage: true
---

# 国产化系统的适配

## 关于 Docker 的安装

如果你是使用docker，不要使用源安装docker，因为国产化操作系统百花齐放，使用源安装docker会很老旧，官版的新版又需要加入 centos7 的源，经过编写测试，可以参考下面的两个文件进行安装

[docker-install-arm.sh](assets/notion/05/05c26ead6d7186421f427351cd9d3852.sh)

[docker-ce.repo](assets/notion/3c/3c33c98a69d4b03d7115482b40920f49.repo)

不过此种方式反而不如手动安装二进制文件来的痛快

下面给出一份手动安装二进制文件的文档，以及一份安装的 ansible task

*  

  * 手动安装

    ```markdown
    ### docker 依赖安装

    #### docker 安装
    首先前往 https://download.docker.com/linux/static/stable/ 下载对应架构的 docker 20 最新版本

    然后将该文件解压，解压出来后将内层 docker-proxy 所在文件夹的所有文件拷贝到 /usr/bin 目录下

    使用命令类似

    ‍```shell
    wget 'https://download.docker.com/linux/static/stable/x86_64/docker-20.10.9.tgz'
    tar zxvf docker-20.10.9.tgz
    cp docker/* /usr/bin/
    ```
    #### docker compose 安装

    然后前往 https://github.com/docker/compose/releases/tag/v2.21.0 下载对应架构的 compose 二进制文件，下载完成后将类似于 docker-compose-linux-x86_64 的文件重命名为 docker-compose，然后将该文件移至 /usr/libexec/docker/cli-plugins/ 目录下

    使用命令类似于

    ```shell
    wget https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-linux-x86_64
    mv docker-compose-linux-x86_64 docker-compose
    chmod +x ./docker-compose
    mkdir -p /usr/libexec/docker/cli-plugins/
    mv docker-compose /usr/libexec/docker/cli-plugins/
    ```
    #### 配置文件与初始化

    创建 `/etc/docker`​ 文件夹，然后将下面的内容写入 `/etc/docker/daemon.json`​

    ```json
    {
        "registry-mirrors": ["https://docker.mirrors.sjtug.sjtu.edu.cn"],
        "live-restore": true,
        "experimental": true,
        "features": {
            "buildkit": true
        },
        "builder": {
            "gc": {
            "enabled": true,
            "defaultKeepStorage": "10GB"
            }
        },
        "log-driver": "local"
    }
    ```
    将下面的内容写入 `/etc/systemd/system/docker.service`​

    ```
    [Unit]
    Description=Docker Application Container Engine
    Documentation=https://docs.docker.com
    After=network-online.target firewalld.service
    Wants=network-online.target

    [Service]
    Type=notify
    ExecStart=/usr/bin/dockerd
    ExecReload=/bin/kill -s HUP $MAINPID
    LimitNOFILE=infinity
    LimitNPROC=infinity
    TimeoutStartSec=0
    Delegate=yes
    KillMode=process
    Restart=on-failure
    StartLimitBurst=3
    StartLimitInterval=60s

    [Install]
    WantedBy=multi-user.target
    ```
    然后使用命令 `systemctl start docker && systemctl enable docker`​ 来启动docker服务并将其设置为开机自启动

    然后可以使用命令 `docker ps`​ 和 `docker compose -h`​ 来检查这两个组件是否安装成功

    ```
    ```
  *  

    * ansible task

      ```yaml
      ---
      # 安装离线二进制版 docker
      - name: 上传 docker 二进制到指定文件夹
        block:
          - name: 上传 docker 二进制到指定文件夹(x86_64)
            ansible.builtin.unarchive:
              src: "{{ playbook_dir }}/deps/docker/docker-23.0.3-x86_64.tgz"
              dest: "/usr/bin"
              extra_opts:
                - "--strip-components=1"
            when: ansible_architecture == 'x86_64'
          - name: 上传 docker 二进制到指定文件夹(arm64)
            ansible.builtin.unarchive:
              src: "{{ playbook_dir }}/deps/docker/docker-23.0.3-aarch64.tgz"
              dest: "/usr/bin"
              extra_opts:
                - "--strip-components=1"
            when: ansible_architecture != 'x86_64'

      - name: 写入systemd配置文件
        ansible.builtin.copy:
          dest: /etc/systemd/system/docker.service
          mode: '0644'
          content: |
            [Unit]
            Description=Docker Application Container Engine
            Documentation=https://docs.docker.com
            After=network-online.target firewalld.service
            Wants=network-online.target

            [Service]
            Type=notify
            ExecStart=/usr/bin/dockerd
            ExecReload=/bin/kill -s HUP $MAINPID
            LimitNOFILE=infinity
            LimitNPROC=infinity
            TimeoutStartSec=0
            Delegate=yes
            KillMode=process
            Restart=on-failure
            StartLimitBurst=3
            StartLimitInterval=60s

            [Install]
            WantedBy=multi-user.target

      - name: 创建 docker 配置文件目录
        ansible.builtin.file:
          path: "/etc/docker"
          state: "directory"

      - name: 写入 docker 配置文件
        ansible.builtin.copy:
          dest: "/etc/docker/daemon.json"
          content: |
            {
              "registry-mirrors": ["https://docker.mirrors.sjtug.sjtu.edu.cn"],
              "live-restore": true,
              "experimental": true,
              "features": {
                "buildkit": true
              },
              "builder": {
                "gc": {
                  "enabled": true,
                  "defaultKeepStorage": "10GB"
                }
              },
              "log-driver": "local"
            }

      - name: 添加 docker-compose plugin
        block:
          - name: 创建 docker cli-plugins 目录
            ansible.builtin.file:
              path: "/usr/libexec/docker/cli-plugins/"
              state: directory
          - name: 安装 docker-compose plugin (x86_64)
            ansible.builtin.copy:
              src: "{{ playbook_dir }}/deps/docker/docker-compose-linux-x86_64"
              dest: "/usr/libexec/docker/cli-plugins/docker-compose"
              mode: '0755'
            when: ansible_architecture == 'x86_64'
          - name: 安装 docker-compose plugin (arm64)
            ansible.builtin.copy:
              src: "{{ playbook_dir }}/deps/docker/docker-compose-linux-aarch64"
              dest: "/usr/libexec/docker/cli-plugins/docker-compose"
              mode: '0755'
            when: ansible_architecture != 'x86_64'

      - name: 启动 docker 守护进程
        ansible.builtin.systemd:
          daemon_reload: true
          enabled: true
          state: "started"
          name: "docker"

      - name: 检查 docker 是否安装成功
        ansible.builtin.command:
          cmd: docker ps
        register: docker_ps_result
        changed_when: true
        failed_when: docker_ps_result.rc != 0

      - name: 检查 docker compose 是否安装成功
        ansible.builtin.command:
          cmd: docker compose version
        register: docker_compose_version_result
        changed_when: true
        failed_when: docker_compose_version_result.rc != 0
      ```

  都是经过大量测试的

  ## 关于 Redis 的安装

  可能你会图配置方便使用 `bitnami/redis`​ 镜像（这个镜像所有配置可以通过环境变量来配置），但是这个镜像的 jemalloc pagesize 有问题  
  会导致它在 国产化arm64 cpu(如鲲鹏920) + 麒麟V10 上跑不起来  
  主要原因是这个镜像的 jemalloc 配置内存对齐为 4k，而这一批国产化系统，大多沿用centos7或更高系统的配置，在 arm64 的 cpu 上内核的内存对齐采用 64k  
  要解决要不就是不采用 jemalloc，要不就是编译时将 jemalloc 的对齐改成 64k，或者重新编译内核改对齐为4k  
  4k jemalloc 不能在 64k 对齐上面运行，反之可以  
  相关内容可参考以下地址

  > [!bookmark]🔖
  >
  > Redis - 适配全国产操作系统的那些坑\_小小工匠的博客-CSDN博客
  >
  > 文章目录JEMALLOCJEMALLOC
  >
  > [https://blog.csdn.net/yangshangwei/article/details/114959048](https://blog.csdn.net/yangshangwei/article/details/114959048)
  >

  所以我们需要使用官版的 redis，个人测试 redis:7-bullseye 可正常运行，唯一一点比较难受的是一些高级配置（比如开启acl）需要挂载配置文件，不如环境变量好用  
  这里给出个人使用的 docker-compose.yml 文件和 ansible task

  *  

    * docker-compose.yml

      ```yaml
      version: '3'

      x-extra_hosts:
        &default-extra_hosts
        - "host.docker.internal:host-gateway"

      services:
        redis.peien:
          image: redis:7-bullseye
          command: redis-server /data/redis.conf
          container_name: redis.peien
          restart: on-failure:5
          ports:
            - '6379:6379'
          volumes:
            - ./redis-data:/data
          healthcheck:
            test: redis-cli -a '{{REDIS_PASSWORD}}' ping
            interval: 1s
            timeout: 3s
            retries: 5
          extra_hosts: *default-extra_hosts
      ```
    *  

      * ansible task

        ```yaml
        - name: 创建 redis 挂载数据文件夹
          become: true
          become_method: sudo
          ansible.builtin.file:
            path: /dockers/mw/redis-data
            mode: 0777
            state: directory

        - name: 创建 redis aclfile 和默认用户
          become: true
          become_method: sudo
          ansible.builtin.copy:
            dest: /dockers/mw/redis-data/users.acl
            content: "user default on >{{ REDIS_PASSWORD }} ~* &* +@all"
            mode: 0777

        - name: 创建 redis.conf
          become: true
          become_method: sudo
          ansible.builtin.copy:
            dest: /dockers/mw/redis-data/redis.conf
            mode: '0777'
            content: |
              bind 0.0.0.0 ::
              protected-mode no
              port 6379
              timeout 0
              tcp-keepalive 300
              port 6379
              pidfile /var/run/redis.pid
              loglevel notice
              logfile ""
              databases 16
              always-show-logo no
              set-proc-title yes
              proc-title-template "{title} {listen-addr} {server-mode}"
              stop-writes-on-bgsave-error yes
              rdbcompression yes
              rdbchecksum yes
              dbfilename dump.rdb
              rdb-del-sync-files no
              dir /data
              replica-serve-stale-data yes
              replica-read-only yes
              repl-diskless-sync yes
              repl-diskless-sync-delay 5
              repl-diskless-sync-max-replicas 0
              repl-diskless-load disabled
              repl-disable-tcp-nodelay no
              replica-priority 100
              acllog-max-len 128
              aclfile '/data/users.acl'
              lazyfree-lazy-eviction no
              lazyfree-lazy-expire no
              lazyfree-lazy-server-del no
              replica-lazy-flush no
              lazyfree-lazy-user-del no
              lazyfree-lazy-user-flush no
              oom-score-adj no
              oom-score-adj-values 0 200 800
              disable-thp yes
              appendonly yes
              appendfilename "appendonly.aof"
              appenddirname "appendonlydir"
              appendfsync everysec
              no-appendfsync-on-rewrite no
              auto-aof-rewrite-percentage 100
              auto-aof-rewrite-min-size 64mb
              aof-load-truncated yes
              aof-use-rdb-preamble yes
              aof-timestamp-enabled no
              slowlog-log-slower-than 10000
              slowlog-max-len 128
              latency-monitor-threshold 0
              notify-keyspace-events ""
              hash-max-listpack-entries 512
              hash-max-listpack-value 64
              list-max-listpack-size -2
              list-compress-depth 0
              set-max-intset-entries 512
              zset-max-listpack-entries 128
              zset-max-listpack-value 64
              hll-sparse-max-bytes 3000
              stream-node-max-bytes 4096
              stream-node-max-entries 100
              activerehashing yes
              client-output-buffer-limit normal 0 0 0
              client-output-buffer-limit replica 256mb 64mb 60
              client-output-buffer-limit pubsub 32mb 8mb 60
              hz 10
              dynamic-hz yes
              aof-rewrite-incremental-fsync yes
              rdb-save-incremental-fsync yes
              jemalloc-bg-thread yes
              # bgsave 需要大量内存，可能会导致卡住，已经开启aof，所以关闭 save
              save ""
              # 防止内存爆掉
              maxmemory 6144mb
              # 从已设置过期时间的数据集挑选使用频率最低的数据淘汰。
              maxmemory-policy volatile-lfu

        - name: 启动一些中间件
          become: true
          become_method: sudo
          ansible.builtin.command:
            cmd: docker compose -f docker-compose.mw.yml up -d --remove-orphans
            chdir: /dockers/mw/
          changed_when: true
        ```

    ## 关于 mysql 的安装

    ​![893ea15e532f560f23ad66b33bedbbc8.webp](https://raw.githubusercontent.com/akkuman/akkuman.github.io/hugo/images/893ea15e532f560f23ad66b33bedbbc8.webp)​

    ## 关于 chorme 的使用

    有些功能可能依赖 chrome/chromium ，但你可能会发现在国产化arm64 cpu + 国产化系统上压根跑不起来，直接crash，也是内存对齐的问题  
    找遍全网，你可能也只找到这篇文档

    > [!bookmark]🔖
    >
    > 鲲鹏920(ARM64) chromium移植指南 for centos7.6-云社区-华为云
    >
    > 1 简介Chromium是一个由Google主导开发的开源网页浏览器。官方链接：https://www.
    >
    > [https://web.archive.org/web/20221224191112/https://bbs.huaweicloud.com/blogs/148360](https://web.archive.org/web/20221224191112/https://bbs.huaweicloud.com/blogs/148360)
    >

    但实际上这篇文章也是教你怎么重新编译内核改成 4k 对齐  
    如果你使用的是 playwright，建议直接换firefox，别和自己过不去，golang 也有 playwright  
    如果迁移成本实在太大，我这里也找同事要了一份支持内存64k对齐的 chromium （不知道他从哪来的）

    ```plain
    https://akkuman.lanzoue.com/iulx2179m6xe
    密码:dhk7
    ```
    这里面解压出来有两个文件，一个 chromium-common 一个 chromium  
    大致安装流程（其中有一些依赖，我测试了一下，能在 AlmaLinux/RockyLinux:9 上正常安装）

    ```shell
    # 启用 devel repo
    dnf install 'dnf-command(config-manager)'
    dnf config-manager --enable devel
    # 启用 epel repo
    yum install -y epel-release
    # 安装 chromium
    yum install -y ./chromium-common-*
    yum install -y ./chromium-*
    # 测试 chromium 是否安装成功
    chromium-browser --version
    ```
    ## 总结

    在进行国产化适配时，建议使用 docker buildkit 本身基于qemu的能力对项目进行多架构镜像构建，不然依赖环境是比较头疼的问题  
    接着你可能会遇到各种奇奇怪怪的兼容问题，只能是拜拜灶王爷了
