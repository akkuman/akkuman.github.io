---
categories:
- 工具
date: '2021-12-10T07:51:00.000Z'
showToc: true
tags:
- 工具
- 笔记
title: notion实现自动发布到hugo github博客

---



notion是用来记录笔记的，hugo是我用来作为github博客自动构建发布的

我目前设置了一个github action是：当我的博客仓库hugo分支有push事件时，自动构建文章发布到master分支，并且发布到博客园。

但是会有这样的不便：在notion中写了一篇笔记或文章，想要发布到github静态博客上，发现需要先将文章转化成markdown，图片需要上传到图床，然后贴入markdown，然后再推送到github，等待action自动构建静态博客

既然我使用notion记录笔记，何不继续All-in-one，将notion作为我的博客发布工具。

只需要在 notion 中建立一个用于博客发布的 database，然后写完笔记后填入这个 database，再使用一些手段触发 CI 即可完成博客文章的发布

## 工具介绍

说干就干，写了两个工具

- [https://github.com/akkuman/notiontomd](https://github.com/akkuman/notiontomd)

- [https://github.com/akkuman/notion_to_github_blog](https://github.com/akkuman/notion_to_github_blog)

`notiontomd` 是用来notion中的某个page转化为markdown的库，当然，当前支持的block是有限的，详细信息可以查看该仓库

`notion_to_github_blog`则是一个github action模板，用来自动从指定格式的database中拉取需要更新发布的文章，然后利用 `notiontomd` 转化为markdown，然后推送到github仓库，再触发另外的github aciton进行博客静态文件构建

## 使用

怎么建仓怎么自动从某分支拉取推到github pages所在分支我就不展开说明了，感兴趣的可以去网上搜索相关资料，本文所关注的流程是从notion database到博客源文件

### 基础环境

本文所涉及到的例子环境可以前往我的博客仓库 [https://github.com/akkuman/akkuman.github.io](https://github.com/akkuman/akkuman.github.io) 进行查看

- hugo分支用来存放博客源文件，其中有一个github action的功能是push时触发，然后自动构建推送到master分支

- master分支用来存放hugo构建之后生成的站点静态文件

- 博客相关的图片我会推送到 [https://github.com/akkuman/pic](https://github.com/akkuman/pic) 仓库

- hugo作为主分支，master设置为github pages分支（原因后面描述）

### workflows编写

要使用该action，首先你需要在 notion 中创建一个 database，这个 database 需要有几个字段，字段名如下:

- Name (title): 文章标题

- Article (text): 文章链接

- MDFilename (text): 创建的 markdown 文件名

- Category (select): 文章分类

- Tags (multi_select): 文章标签

- IsPublish (checkbox): 文章是否发布

- NeedUpdate (checkbox): 文章是否有更新

- CreateAt (Created time): 创建时间

- UpdateAt (Last edited time): 更新时间

默认当 `IsPublish` 未勾选或 `NeedUpdate` 勾选的项目才会触发流程，即 `IsPublish=false || NeedUpdate=true` 时触发

样例如下

![](https://raw.githubusercontent.com/akkuman/pic/master/notionimg/4d/60/4d60d48a62a039ed0ff78ddb5161629b.png)

然后你需要在你存放博客源文件的仓库进行一些设置，放置上workflows

下面以我的github博客仓库 [akkuman/akkuman.github.io](https://github.com/akkuman/akkuman.github.io) 为例进行说明

我们创建一个workflows: [akkuman/akkuman.github.io/.github/workflows/xxx.yml](https://github.com/akkuman/akkuman.github.io/blob/hugo/.github/workflows/notion_to_blog.yml)

```yaml
name: Notion To Blog

on:
  issues:
    types: [opened]

jobs:
  notion-to-blog:
    if: ${{ github.event.issue.user.login == github.actor && contains(github.event.issue.title, 'notion-ci') }}
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2
      with:
        # Workflows are only triggered when commits (and tags I think, but it would need to be tested) are created pushed using a Personal Access Token (PAT).
        # ref: https://github.com/EndBug/add-and-commit/issues/311#issuecomment-948749635
        token: ${{ secrets.CHECKOUT_TOKEN }}

    - name: Markdown From Notion
      uses: akkuman/notion_to_github_blog@master
      with:
        notion_token: ${{ secrets.NOTION_TOKEN }}
        notion_database_id: ${{ secrets.NOTION_DATABASE_ID }}
        img_store_type: github
        img_store_path_prefix: notionimg
        # img_store_url_path_prefix: ${{ secrets.IMG_STORE_URL_PATH_PREFIX }}
        # Actions run as an user, but when they are running in a fork there are potential security problems, so they are degraded to "read-only"
        # ref: https://github.com/actions/first-interaction/issues/10#issuecomment-546628432
        # ref: https://docs.github.com/en/actions/security-guides/automatic-token-authentication#permissions-for-the-github_token
        # so you should set another token
        img_store_github_token: ${{ secrets.CHECKOUT_TOKEN }}
        img_store_github_repo: akkuman/pic
        img_store_github_branch: master
        # md_store_path_prefix: ${{ secrets.MD_STORE_PATH_PREFIX }}

    - name: push to github
      uses: EndBug/add-and-commit@v7
      with:
        branch: hugo
        message: 'Notion CI'
```

字段解释：

- **notion_token**: notion申请的app的api token

- **notion_database_id**: notion中需要作为博客发布的database的id，这是一个uuid，可以通过Share->Copy link获取，注意需要把其中的id转化为uuid的格式，比如 Copy link出来为 `https://www.notion.so/akkuman/7bf568e946b946189b2b4af0c61b9e78?v=c45b5e45e96541f4bf81994ab4af1a6e`，则notion_database_id为 `7bf568e9-46b9-4618-9b2b-4af0c61b9e78`，并且你所要发布的文章以及该database都需要invite我们上面申请的app（为了token能够获取到内容）

- **img_store_type**: notion中提取出来的图片保存到哪，可选 local 或者 github，local代表保存到源仓库，github代表保存到另一个github仓库（图床）中去，默认为 `local`

- **img_store_path_prefix**: 图片保存的路径前缀，默认为 `static/notionimg`

- **img_store_url_path_prefix**： 当 `img_store_type=local` 时需要，设置在markdown图片链接中的前缀，和上面的 `img_store_path_prefix` 不相同，比如 `img_store_path_prefix='static/notionimg' img_store_url_path_prefix：='/notionimg/'` 的情况下，则图片保存路径为 './static/notionimg/{img_md5}{img_ext}', 而在markdown文件中的体现为 `![](/notionimg/{img_md5}{img_ext})`

- **img_store_github_token**: 当 `img_store_type=github` 时需要，设置保存图片到github图床所使用的token（`secrets.GITHUB_TOKEN` 只有读权限，所以需要另外使用）

- **img_store_github_repo**: 当 `img_store_type=github` 时需要，你把哪个仓库当作github图床

- **img_store_github_branch**: 当 `img_store_type=github` 时需要，你把哪个github图床仓库的哪一个分支当作图床

- **md_store_path_prefix**: 最后生成的markdown文件保存在哪，默认是当前仓库目录的 `content/posts` 目录下

其中需要**关注**的是

1. `token: ${{ secrets.CHECKOUT_TOKEN }}` 是为了后面的 `push to github` 推送后能够触发另外一个action流程，否则无法触发，其中的 `CHECKOUT_TOKEN` 为你创建的 Personal Access Token，具体可以查看我上面的注释

1. `on: issues: types: [opened]` 的主要作用是当打开或提交一个issue时触发该action

1. `if: ${{ github.event.issue.user.login == github.actor && contains(github.event.issue.title, 'notion-ci') }}` 的主要作用是：当提交issue的人是你自己，并且issue标题包含 notion-ci 时进行action流程

**注意**: 只有当workflows在主分支时，使用 `issues` 作为触发条件才会生效，所以我个人是将 `hugo` 作为主分支，将 `master` 作为 `Github Pages` 分支

### 测试

首先申请一个token，在 [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations) 点击 `+ New integration` ，然后配置好你想要的app名称，以及设置到的工作区，这里我取的名称是 `api`

然后我们需要把指定的databse以及所需要发布的文章都集成我们申请的app

![](https://raw.githubusercontent.com/akkuman/pic/master/notionimg/bb/33/bb33654f889882ac7fb38de6697fa52a.png)

以及需要发布的文章

![](https://raw.githubusercontent.com/akkuman/pic/master/notionimg/6a/a6/6aa60818454a687bc86f572250467e4e.png)

**注意**：database中的Article列，按下 `@` 号来搜索选择文章

github配置好相关的 `Secrets` ，

![](https://raw.githubusercontent.com/akkuman/pic/master/notionimg/cb/7e/cb7e76a06ed876124cefb5dcc886aac7.png)



我们在仓库中提交一个标题包含 `notion-ci` 的issue，即可触发workflows

![](https://raw.githubusercontent.com/akkuman/pic/master/notionimg/c4/38/c438703c70a9bdeaeb734292448d409c.png)

![](https://raw.githubusercontent.com/akkuman/pic/master/notionimg/8b/55/8b556bb350c5204fb8212059204da3f7.png)

## 全自动整个流程

### 平台调研

根据官方文章 [Connect your tools to Notion with the API](https://www.notion.so/guides/connect-tools-to-notion-api) 中所提到的，我们可以得到一些可以用于notion的自动化集成平台，对比了一下，[automate.io](http://automate.io/) 应该是最实惠的平台，免费用户每个月可以触发300次，一般而言，对于博客来说够了

### 自动化集成

在 [https://automate.io/app/signup](https://automate.io/app/signup) 注册好账号后，打开 [Add an Issue in GitHub on a New Database Item in Notion](https://automate.io/app/bots/add?actionAppId=github&actionId=add-issue&triggerAppId=notion&triggerId=new-page) ，在database添加条目时在指定的github仓库添加一条issue

![](https://raw.githubusercontent.com/akkuman/pic/master/notionimg/07/89/0789bdaf483a9e38d51f1af19aaad439.png)

首先点选 `Link Notion` ，一路下一步，出现下面的页面时，点选我们的databse

![](https://raw.githubusercontent.com/akkuman/pic/master/notionimg/1e/cf/1ecf7335767a17aa7559364b91eb007e.png)

然后确认后点选我们的database

![](https://raw.githubusercontent.com/akkuman/pic/master/notionimg/54/f4/54f4dc858e3329d159be8fdcf287722c.png)

然后继续 `Link Github` 授予github权限（注意，这个应用所需的权限较大）

然后配置一下相关属性

![](https://raw.githubusercontent.com/akkuman/pic/master/notionimg/97/cf/97cf5c12518a0f7c13557f843d522f56.png)

注意选好相关仓库，以及 `Title` 中需要包含 `notion-ci`

确认就好了，当然，有一些缺陷，免费的是每五分钟检查一次，等不及的话，你还是可以手动提交issue触发

现在尝试在database中使用右上角的 `New` 新增一个条目，查看会有什么变化

**注意**：所有涉及到的文章，都需要invite我们先前创建的app，否则github action无法读取到



