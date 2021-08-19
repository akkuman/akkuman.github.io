---
title: 使用Travis CI自动部署博客到github pages和coding pages
date: 2018-09-07 19:25:20
tags:
- git
- blog
categories:
- git
---

每次换系统或换电脑之后重新部署博客总是很苦恼？想像jekyll那样，一次性部署完成后，以后本地不用安装环境直接 `git push` 就能生成博客？那我推荐你应该使用使用 `Travis CI`了。

这篇文章我们来讲讲如何利用 `Travis CI`把你 `push` 上去的博客源文件直接生成可访问的站点，并且同步部署到 `github pages` 和 `coding pages` 。

这篇文章假设你已经对这些采用 `git` 版本控制系统的静态博客托管服务有所了解，并且知道怎么去简单的使用 `git` 以及了解 `hexo` 写博客发布到这些 `pages` 服务的流程。因此本文会写的较为**简略，旨在指出关键的地方以及我遇到的问题、问题产生的原因和提供的解决方案**，希望能够帮助到大家。

<!--more-->

如果大家有什么问题可以直接在下方评论（独立博客采用Disqus，可能需要翻墙），或者直接给我邮件（akkuamns@qq.com），我可能会在以后的时间逐步把详细的流程写出来，时间不多，匆忙之际下笔，望大家见谅。

看完上面的话，是不是有一种“复恐匆匆说不尽，行人临发又开封。”的感觉，可能废话太多了，那么直接开始吧！

## 令牌的获取

### 问个为什么

首先我们说一下为什么要获取令牌？他的作用是什么？

先给大家几个流程图，来自于[liolok的博客(前两张)](https://liolok.github.io/Hexo-Travis-CI/)和[CodingLife的博客(第三张)](http://magicse7en.github.io/2016/03/27/travis-ci-auto-deploy-hexo-github/)

首先是当我们未采用 `Travis CI` ，直接使用 `hexo` 的插件 `hexo-deployer-git` 执行命令 `hexo d -g` 部署的流程：

![liolok的博客-旧流程](https://raw.githubusercontent.com/akkuman/pic/master/img/c0264382gy1fv189l6c01j20xh0j9q4c.jpg)

然后是使用 `Travis CI` 进行将仓库中的站点源文件自动生成站点然后部署到特定仓库(或特定分支)的流程：

![liolok的博客-新流程](https://raw.githubusercontent.com/akkuman/pic/master/img/c0264382gy1fv18c106iaj219a0k3q4s.jpg)

还有一张图大家也可以看看：

![TravisCI自动构建hexo博客流程图](https://raw.githubusercontent.com/akkuman/pic/master/img/c0264382gy1fv18deh3foj20tx0sfafg.jpg)

现在假设一种情况：我们把 `username/username.github.io` 仓库 `clone` 了下来，然后在它里面新建了一个分支 `hexo` 并放置我们的站点源文件（也就是你 `hexo init blog` 出来的 `blog` 目录下的所有文件），然后把这个 `hexo` 分支 `push` 了上去。

那么你设置这个仓库到 `Travis CI` 之后会做什么呢？它会寻找 `.travis.yml` 这个文件，如果存在的话，它就会根据 `.travis.yml` 来自动执行一些命令，这些命令就可以完成我们的需求。

然后我们回到刚才的话题，为什么要获取令牌？

令牌相当于一个通行证，比如要实现我们的需求，我们的 `.travis.yml` 中需要把 `hexo` 分支下的站点源文件文件使用 `hexo g` 生成静态站点后把这个静态站点 `push` 到我们的仓库，那 `github` 总不可能让人想 `push` 到谁的仓库就可以直接 `push` 上去吧，所以它就是靠这个通行证来验证你的身份。

所以我们把令牌的key字段加到 `Travis CI` 后就可以让 `github` 知道：哦，这个人是已授权的。

### 那么怎么做

那应该怎么去获取这个令牌并加到  `Travis CI` 呢？

哦哦，忘了说一个东西，如果你仔细看了我刚才的描述，那么你可能对这个  `Travis CI` 还是不了解，只是大致知道了他可以用来做什么，借用一下维基百科上的解释：

> Travis CI是在软件开发领域中的一个在线的，分布式的持续集成服务，用来构建及测试在GitHub托管的代码。

你可以把它简单的认为是一个用来 `读取你的仓库 -> 读取仓库下的 .travis.yml 文件 -> 根据 .travis.yml 的内容对这个仓库来执行一系列linux和git命令去达到你的目的` 的工具。

那么谈到令牌的获取，这个并不麻烦。

如果是 `github`，登陆后打开设置，然后进入 `Developer settings ->Personal access tokens` 点击 `Generate new token`，然后会提示你选择这个令牌拥有的权限，因为我们只需要对仓库进行操作，选中 `repo`即可。

![](https://raw.githubusercontent.com/akkuman/pic/master/img/c0264382gy1fv193cmo02j20sy0g1q46.jpg)

然后复制那一串 `token` 先保存下来。

如果是 `coding`，打开 `个人设置 -> 访问令牌`，然后点击 `新建令牌`，同样的给予仓库的控制权限，然后复制保存生成的 `token` 。

![](https://raw.githubusercontent.com/akkuman/pic/master/img/c0264382gy1fv1978v3jhj20r80cj754.jpg)

然后打开[Travis CI](https://travis-ci.org) 网站，然后点击右上角的用github登录，然后同步你的仓库，再打开你需要自动部署的仓库开关，点击设置进去添加 `token` 即可。直接给两张图。

![](https://raw.githubusercontent.com/akkuman/pic/master/img/c0264382gy1fv19ce3p5xj20up0ieq4h.jpg)

![](https://raw.githubusercontent.com/akkuman/pic/master/img/c0264382gy1fv19fuupr5j21hc0u0ad1.jpg)

需要注意的是
- 每个`Token` 自定义的 `Name` 你需要记住，待会在写 `.travis.yml` 的时候会用到
- `Display value in build log` 这个选项千万不要打开，因为log是公网可见的

## 仓库的结构

上面完成了，我们来说说仓库的结构。

1. 你可以把站点源文件部署到一个新仓库（假如是 `new_repo`），那么你需要更改一下上面的设置，不是打开博客仓库的开关了，而是换成打开你需要操作的仓库 `new_repo`的开关，然后  `Travis CI` 再通过我们设置好的 `.travis.yml` 自动部署到博客仓库

2. 你也可以把站点源文件部署到博客仓库（下文我以 `akkuman.github.io` 代替）的新分支，然后 `Travis CI` 再通过这个新分支下我们设置好的 `.travis.yml` 自动部署到博客仓库 `akkuman.github.io` 。

这里我们采用第二种方案，只是个人爱好，不想再多开一个仓库。

## 仓库的改造

### 新分支的建立

直接看下面的命令和注释吧。

```bash
# 首先把自己的博客仓库clone到本地
git clone git@github.com:akkuman/akkuman.github.io.git
cd akkuman.github.io.git
# 我们假设仓库下的部署分支是master
# 我们先新建并切换到一个新分支，分支名我这里取为hexo
git checkout -b hexo
```

现在我们已经切换到了新分支 `hexo`，紧接着我们删除 `akkuman.github.io` 文件夹下除了 `.git` 文件夹的其他所有文件。

我们把其他地方 `hexo init blog` 出来的 `blog` 站点文件夹下所有文件复制到刚才的 `akkuman.github.io` 文件夹下。

### 站点主题的处理

这里我们需要注意:
不知道你的主题是怎么下载来的，我就分为 1.主题是一个 `git` 仓库 2.主题不是一个 `git` 仓库，所以主题可能也是一个 `git` 仓库，如果你对 `git` 不熟悉，建议不要 `git clone` 主题仓库，而是下载别人的 `release` 版。

判断一个文件夹是不是 `git` 仓库，就是看该文件夹目录下有没有一个 `.git`文件夹，注意它是一个隐藏文件夹，所以你发现你的主题是一个 `git` 仓库的时候，你可以删除这个隐藏的 `.git`文件夹。

那么我们这么做的目的是什么呢？

如果我们的主题文件夹也是一个 `git` 仓库，那么我们的这个博客仓库的 `hexo` 分支下就嵌套了一个仓库，当然，`git` 也给出了解决方案，那就是子模块。所以目的就是告诉你：图省事可以直接使用非 `git` 仓库的主题，不用折腾子模块。

多说一点吧：

说到子模块，子模块是SSH协议还是HTTPS协议对后面有影响，不过我后面会给一个通用的模板，看后面的注释即可。

这个子模块你是使用SSH协议还是HTTPS协议就看个人爱好了，我是自己 `fork` 了别人的仓库然后修改了一下，所以我为了方便期间还是使用了SSH协议的仓库。

然后子模块怎么使用呢？

比如我使用的主题仓库是`git@github.com:akkuman/hexo-theme-next.git`，现在假设我们在博客仓库 `akkuman.github.io` 下，然后执行下面命令把这个主题仓库下的所有文件复制到站点目录下的 `themes/next` 文件夹下。

```bash
git submodule add git@github.com:akkuman/hexo-theme-next.git themes/next
```
然后你的目录下会出现一个 `.gitmodules` 文件，内容格式大致是

```
[submodule "themes/next"]
	path = themes/next
	url = git@github.com:akkuman/hexo-theme-next.git
```

关于子模块的知识可以自己查阅资料，我这里不细说了，待会在后面我会给出参考资料。

### git需要忽略的文件

`git` 依靠 `.gitignore` 文件判断那些文件不纳入仓库，一般通过 `hexo init` 命令出来的站点文件夹下都会有这么个文件。没有也没关系，自己新建一个 `.gitignore` 文件，内容为

```
.DS_Store
Thumbs.db
db.json
*.log
node_modules/
public/
.deploy*/
```

> node_modules目录是hexo博客实例的npm环境依赖,，据说是质量比黑洞还大的物体， 我们选择忽略它， 反正最后到了Travis那里也会重新跑一遍npm install,，这些东西本来也会删了重来, 没有同步的意义.
> public目录是hexo生成的静态文件， db.json是数据库文件,，同理,，由于Travis构建流程中会执行hexo clean,，都不需要同步。

### .travis.yml的设置

上面的操作完成后，我们开始着手写 `.travis.yml`了，先提供一个最简单也是网上博客教程里面最多的版本

```yaml
language: node_js # 设置语言
node_js: stable # 设置相应版本
install:
    - npm install # 安装hexo及插件
script:
    - hexo clean # 清除
    - hexo g # 生成
after_script:
    - cd ./public
    - git init
    - git config user.name "yourname" # 修改name
    - git config user.email "your email" # 修改email
    - git add .
    - git commit -m "Travis CI Auto Builder"
    - git push --force --quiet "https://${GH_TOKEN}@${GH_REF}" master:master # GH_TOKEN是在Travis中配置token的名称
branches:
    only:
        - hexo #只监测hexo分支，hexo是我的分支的名称，可根据自己情况设置
env:
    global:
        - GH_REF: github.com/yourname/yourname.github.io.git #设置GH_REF，注意更改yourname
```

这个是针对 `github` 仓库的最简版本，不过有个问题，我们从执行的命令中也能看到，就是部署到 `master` 分支的站点文件每次都会 `init` 后在提交，所以每次都只有一次 `commit` 记录，我建议你把下面的看完。

我先把文件给出来：

`.travis.yml` 文件：

```yaml
language: node_js

node_js: stable

cache:
    apt: true
    directories:
        - node_modules

notifications:
    email:
        recipients:
            - akkumans@qq.com
        on_success: change
        on_failure: always

# turn off the clone of submodules for change the SSH to HTTPS in .gitmodules to avoid the error
git:
  submodules: false
        
before_install:
    # Use sed to replace the SSH URL with the public URL if .gitmodules exists
    - test -e ".gitmodules" && sed -i 's/git@github.com:/https:\/\/github.com\//' .gitmodules
    # update the submodule in repo by manual
    - git submodule update --init --recursive
    - export TZ='Asia/Shanghai'
    - npm install hexo-cli -g
    - chmod +x ./publish-to-gh-pages.sh

install:
    - npm install

script:
    - hexo clean
    - hexo g

after_script:
    - ./publish-to-gh-pages.sh

branches:
    only:
        - hexo

env:
    global:
        # Github Pages
        - GH_REF: github.com/akkuman/akkuman.github.io.git
        # Coding Pages
        - CD_REF: git.coding.net/Akkuman/Akkuman.git
```

我把需要执行的脚本放到了 `publish-to-gh-pages.sh` 文件。

`publish-to-gh-pages.sh` 文件：

```yaml
#!/bin/bash
set -ev


# get clone master
git clone https://${GH_REF} .deploy_git
cd .deploy_git
git checkout master

cd ../
mv .deploy_git/.git/ ./public/

cd ./public

git config user.name "Akkuman"
git config user.email "akkumans@qq.com"

# add commit timestamp
git add .
git commit -m "Travis CI Auto Builder at `date +"%Y-%m-%d %H:%M"`"

# Github Pages
git push --force --quiet "https://${GITHUB_TOKEN}@${GH_REF}" master:master

# Coding Pages
git push --force --quiet "https://Akkuman:${CODING_TOKEN}@${CD_REF}" master:master
```

请把对应的 `Akkuman` 和 `email` 还有 `username` 改成你的配置。

这里我不详解配置，因为这篇文章已经花了很长时间了，如果大家有需要我再详细写。下面我会给出我的仓库地址，如果有不懂可以去看看我仓库下的例子。

说着不详解，但是我还是有点自己踩过的坑需要提点一下，`Travis CI` 进行 `git clone` 操作的时候，默认是开启 `--recursive` 参数的，也就是克隆库的时候会默认初始化子模块。这个操作本来是没问题的，那么我为什么要单独提出来说？

我上面说到了：

> 说到子模块，子模块是SSH协议还是HTTPS协议对后面有影响

问题就是这里了，如果你是用的HTTPS协议，根据 `.gitmodules` 文件默认初始化子模块的时候是没问题。但是如果使用SSH协议，不管是 `clone`、`push`还是其他等等操作， 是要求本机上有私钥，并且仓库那边要有对应的公钥才可以。但是`Travis CI` 自动部署执行 `clone` 的时候没有这个公私钥，所以我们只能使用HTTPS协议，但是我使用的是 `.gitmodules` 文件里面定义的子模块SSH协议呀！我在这里也查了一下，解决方案就是上面的那样。节选出来：

```yaml
# turn off the clone of submodules for change the SSH to HTTPS in .gitmodules to avoid the error
git:
  submodules: false
        
before_install:
    # Use sed to replace the SSH URL with the public URL if .gitmodules exists
    - test -e ".gitmodules" && sed -i 's/git@github.com:/https:\/\/github.com\//' .gitmodules
    # update the submodule in repo by manual
    - git submodule update --init --recursive
```

先关闭了 `Travis CI` 的默认初始化子模块功能，然后后面我们先判断子模块配置文件是否存在（所以我刚才说最省事的就是使用 `releases` 主题，也就是不含 `.git` 文件夹的，具体见上面），然后判断子模块配置文件如果存在存在，就使用 `sed` 把命令把 `.gitmodules` 子模块配置文件中的SSH协议换成HTTPS协议再执行后面的操作。

## 开启自动构建之旅

现在你的博客仓库 `akkuman.github.io` 文件夹下的 `hexo` 分支下的东西已经配置好了。

新分支有了，`.travis.yml` 文件也有了。

你现在可以直接 `push` 上去：

```bash
git add .
git commit -m ":constructin_worker: The introduction of Travis CI"
git push origin hexo:hexo
```

然后打开 `Travis CI` 网站即可看到你的网站正在构建，如果构建失败，上面也有详细的报错可以帮你分析原因。构建成功后即可看到你焕然一新的网站了。

以后更新 `md` 就可以用上面的命令 `push` 到仓库，然后 `Travis CI` 会自动帮你构建到 `master` 分支

### 题外话

为了以后不用打

```bash
git push origin hexo:hexo
```

而是直接可以使用

```bash
git push
```

我们可以设置上游分支，如果是第一次执行 `git push origin hexo:hexo`，它会提示你使用

```bash
git push --set-upstream origin hexo
```

使用上面的命令即可把本地的 `hexo` 的上游分支设置为远程仓库的 `hexo` 分支，以后 `push` 就可以简化命令为 `git push` 了。

当然你也可以手动设置上游分支，使用下面的命令把本地的 `hexo` 的上游分支设置为远程仓库的 `hexo` 分支：

```bash
git branch --set-upstream-to=origin/hexo hexo
```

## 我的站点仓库配置示例

见 [akkuman/akkuman.github.io](https://github.com/akkuman/akkuman.github.io/tree/hexo)

## 参考资料

- [Hexo + Travis CI 博客管理](https://liolok.github.io/Hexo-Travis-CI/)
- [使用Travis CI自动构建hexo博客](http://magicse7en.github.io/2016/03/27/travis-ci-auto-deploy-hexo-github/#坑3：-travis-CI自动构建部署之后，博客页面空白，什么也没有)
- [使用Travis CI自动部署Hexo博客](http://www.itfanr.cc/2017/08/09/using-travis-ci-automatic-deploy-hexo-blogs/#创建-travis-yml-文件)
- [Travis CI官方帮助文档](https://docs.travis-ci.com/user/languages/r/#configuration-options)
- [git中submodule子模块的添加、使用和删除](https://blog.csdn.net/guotianqing/article/details/82391665)
- [Git Submodule 用法筆記](https://blog.chh.tw/posts/git-submodule/)
- [CODING帮助文档-个人访问令牌](https://coding.net/help/doc/account/access-token.html)
> 提一句上面的git push --force --quiet "https://Akkuman:${CODING_TOKEN}@${CD_REF}" 网址格式是查询的CODING帮助文档


