---
title: metasploit使用外部数据库（TODO）
date: 2020-09-30 20:36:00
tags:
- msf
- 红队
- 工具
- Tips
categories:
- 红队
---

metasploit不能使用外部的pgsql数据库搞得一直很蛋疼，这篇小记只是记录下如何一步步让metasploit使用外部的pgsql，本篇文章中使用pgsql的docker

<!--more-->


## 安装ruby

此处使用 rbenv 安装 ruby

克隆rbenv仓库
```bash
git clone --depth=1 https://github.com/rbenv/rbenv.git ~/.rbenv
```

编译bash扩展加速rbenv，可选

```bash
cd ~/.rbenv && src/configure && make -C src
```

把rbenv加到环境变量

```bash
echo 'export PATH="$HOME/.rbenv/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

rbenv设置

```bash
rbenv init # 跟随命令的输出设置rbenv shell
```

安装ruby-build插件，为了支持rbenv install 命令

```bash
git clone https://github.com/rbenv/ruby-build.git "$(rbenv root)"/plugins/ruby-build
```

如果是国内用户，可以加上rbenv cache镜像

```bash
git clone https://github.com/andorchen/rbenv-china-mirror.git "$(rbenv root)"/plugins/rbenv-china-mirror
```

查看 metasploit 官方开发使用版本，https://github.com/rapid7/metasploit-framework/blob/master/.ruby-version

我这里看到的是 2.6.6，就安装这个版本

```bash
rbenv install 2.6.6
rbenv local 2.6.6
```

如果你是国内用户，可以设置一些镜像


```bash
gem sources --add https://gems.ruby-china.com/ --remove https://rubygems.org/
```

安装bundler并设置镜像

```bash
gem install bundler

bundle config mirror.https://rubygems.org https://gems.ruby-china.com
```

## 安装 metasploit

详细可参见 https://github.com/rapid7/metasploit-framework/wiki/Setting-Up-a-Metasploit-Development-Environment

我们已经安装了ruby，紧接着安装依赖

```bash
sudo apt update && sudo apt install -y git autoconf build-essential libpcap-dev libpq-dev zlib1g-dev libsqlite3-dev
```

克隆 metasploit

```bash
git clone --depth=1 https://github.com/rapid7/metasploit-framework.git
```

安装metasploit运行所需的ruby库

```bash
cd metasploit-framework && bundler install
```

至此，metasplot 已经可以使用

```bash
./msfconsole
```

如果进入了 msf console 证明已经正确安装，并且运行后会在你的创建一个 ~/.msf4 文件夹，这个我们后面会用到


## 设置metasploit使用外部数据库

### 启动pgsql

首先启动一个postgresql docker

参见 https://hub.docker.com/_/postgres

这里我直接使用官方提供的命令

```bash
docker run -d -p 5432:5432\
    --name some-postgres \
    -e POSTGRES_PASSWORD=mysecretpassword \
    -e PGDATA=/var/lib/postgresql/data/pgdata \
    -v /custom/mount:/var/lib/postgresql/data \
    postgres
```

或者你可以使用 docker-compose，但是记得改掉密码和挂载目录

然后我们创建两个数据库 msf 和 msftest，具体怎么创建这里不展开，可以使用数据库管理工具

### 配置 msf 数据库连接

在 ~/.msf4 文件夹下面创建一个文件 database.yml，即 ~/.msf4/database.yml

```yaml
development: &pgsql
  adapter: postgresql
  database: msf
  username: postgres
  password: mysecretpassword
  host: 127.0.0.1
  port: 5432
  pool: 200

production: &production
  <<: *pgsql

test:
  <<: *pgsql
  database: msftest
```