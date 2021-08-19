---
title: RAP2 前后端开发利器搭建
date: 2019-10-12 20:55:12
tags:
- 问题解决
- 配置与搭建
categories:
- 配置与搭建
---


RAP2 是一个api管理系统，前后端协作开发的利器。

在线体验地址<http://rap2.taobao.org>

Web接口管理工具，开源免费，接口自动化，MOCK数据自动生成，自动化测试，企业级管理。

<!--more-->

有一份一键搭建的docker-compose.yml，但是已经是比较老的前端了，具体可以查看<https://hub.docker.com/r/taomaree/rap2>

我这里把他的docker-compose.yml贴出来

```
version: '2.2'

services:
  delos:
    container_name: rap2-delos
    image: taomaree/rap2:1.0.6
    environment:
      - MYSQL_URL=rap2-mysql
      - MYSQL_PORT=3306
      - MYSQL_USERNAME=rap2
      - MYSQL_PASSWD=rap2delos
      - MYSQL_SCHEMA=RAP2_DELOS_APP
      - REDIS_URL=rap2-redis
      - REDIS_PORT=6379
      - NODE_ENV=production
    working_dir: /app/rap2-delos/dist
    volumes:
      - "/srv/rap2-mysql/mysql-backup:/backup"
    ports:
      - "38080:80"  # expose 38080
    links:
      - redis
      - mysql
    depends_on:
      - redis
      - mysql


  redis:
    container_name: rap2-redis
    image: redis:4.0


  mysql:
    container_name: rap2-mysql
    image: mysql:8.0
    #ports:
    #   - 33306:3306
    volumes:
      - "/srv/rap2-mysql/mysql-data:/var/lib/mysql"
    command: mysqld --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci --init-connect='SET NAMES utf8mb4;' --default-authentication-plugin=mysql_native_password --innodb-flush-log-at-trx-commit=0 
    environment:
      - MYSQL_ALLOW_EMPTY_PASSWORD=yes
      - MYSQL_DATABASE=RAP2_DELOS_APP
      - MYSQL_USER=rap2
      - MYSQL_PASSWORD=rap2delos

  rap2-init:
    container_name: rap2-init
    image: taomaree/rap2:1.0.6
    environment:
      - MYSQL_URL=rap2-mysql
      - MYSQL_PORT=3306
      - MYSQL_USERNAME=rap2
      - MYSQL_PASSWD=rap2delos
      - MYSQL_SCHEMA=RAP2_DELOS_APP
      - REDIS_URL=rap2-redis
      - REDIS_PORT=6379
      - NODE_ENV=production
    working_dir: /app/rap2-delos
    #command: 'mysql -h${MYSQL_URL} -u${MYSQL_USERNAME} -p${MYSQL_PASSWD} -e "select * from ${MYSQL_SCHEMA}.Users;" || npm run create-db'
    command: ["bash", "-c", "sleep 30 && mysql -h$${MYSQL_URL} -u$${MYSQL_USERNAME} -p$${MYSQL_PASSWD} -e \"select * from $${MYSQL_SCHEMA}.Users;\" || node dist/scripts/init"]
    links:
      - redis
      - mysql
    depends_on:
      - redis
      - mysql
```

注意一下数据挂载目录就行了。然后访问38080端口就ok了

但是我想要最新的前端。

这个搭建是稍微有点复杂的

启动后端

使用官方贴出的docker-compose.yml

```
mkdir rap2
cd rap2

wget -c https://raw.githubusercontent.com/thx/rap2-delos/master/docker-compose.yml

sudo docker-compose up -d
```

docker起来后，默认是监听38080端口，你可以按照自己的喜好编辑docker-compose.yml，并且这个是允许跨域的，跨域规则比较松，Allow-Origin是*，所以你可以把前端部署在任何地方，不过我习惯部署在同一个域名下。

部署前端

首先下载前端

```
git clone https://github.com/thx/rap2-dolores.git
```

然后修改前端的配置，这一步是为了与后端对接

我是打算把整个服务部署在 mock.test.com 域名下，然后 http://mock.test.com/api 作为接口的根url（这里需要靠nginx来重写）

那么我们需要修改前端的配置文件

进入我们刚才clone下来的目录 rap2-dolores/src/config下，修改 config.prod.ts 文件

![](https://raw.githubusercontent.com/akkuman/pic/master/img/1106918-20191012205633755-1398708534.png)


只需要修改 serve 字段的值即可。

然后编译前端，这里我使用淘宝的源

```
cd rap2-dolores

npm  install --registry=https://registry.npm.taobao.org

npm run build
```

编译完成后，rap2-dolores 目录下会出现一个名字为 build 或者 dist 的文件夹，把这个文件夹放到你刚才放docker-compose.yml的目录下（为了以后迁移方便，可以放在任意位置，只需要修改对应的nginx配置即可）

这里我假定编译出来的是 build 文件夹，放置到docker-compose.yml所在的目录

那么现在你的目录结构应该是这样

```
lab@lab-desktop:~/dockers/rap2$ pwd
/home/lab/dockers/rap2
lab@lab-desktop:~/dockers/rap2$ tree -L 1
.
├── docker-compose.yml
├── build
└── docker

2 directories, 1 file
```

然后新建nginx配置文件

```
sudo vim /etc/nginx/sites-enabled/mock.test.com.conf
```

写入以下内容

```
server {
        listen 80;
        listen [::]:80;

        server_name mock.test.com;
        root /home/lab/dockers/rap2/build;

        # reverse proxy
        location /api/ {
                # 38080后面加/是为了把http://127.0.0.1:38080/api/*反代到http://127.0.0.1:38080/*
                proxy_pass http://127.0.0.1:38080/;  # 38080后面的/是必要的，是否会附加location配置路径与proxy_pass配置的路径后是否有"/"有关，有"/"则不附加
                # 代理配置，可选
                proxy_http_version      1.1;
                proxy_cache_bypass      $http_upgrade;
                
                proxy_set_header Upgrade                        $http_upgrade;
                proxy_set_header Connection             "upgrade";
                proxy_set_header Host                           $host;
                proxy_set_header X-Real-IP                      $remote_addr;
                proxy_set_header X-Forwarded-For        $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto      $scheme;
                proxy_set_header X-Forwarded-Host       $host;
                proxy_set_header X-Forwarded-Port       $server_port;
        }
        location / {
                # 路由在前端，后端没有真实路由，在路由不存在的 404状态的页面返回 /index.html
                # 这个方式使用场景，你在写React或者Vue项目的时候，没有真实路由
                try_files $uri /index.html;
        }
}
```

然后重启一下nginx，访问mock.test.com就可以了

这里给出一份比较详尽的nginx配置教程

-   Nginx 代理转发，让生产和测试环境 React、Vue 项目轻松访问 API，前端路由不再 404 <https://juejin.im/entry/58df166a0ce463005821e9d9>

## Reference

-   [Nginx------location常见配置指令，alias、root、proxy_pass](https://blog.csdn.net/zhangliangzi/article/details/78257593)
-   <https://github.com/taomaree/docker-rap2>
-   <https://github.com/thx/rap2-delos/wiki/docker>
-   <https://github.com/thx/rap2-delos/issues/119#issuecomment-392762261>
-   <https://github.com/thx/rap2-dolores>
-   [Api 文档管理系统 RAP2环境搭建](https://incoder.org/2018/03/27/rap2/)