---
layout: blog
title: hugo+NetlifyCMS部署
date: 2022-06-25T08:02:47.978Z
showToc: true
draft: false
description: 本文记录了怎么为已经存在CI(Github Action)的hugo博客添加 Netlify CMS
cover:
  # only hide on current single page
  hidden: false
---
网上的博客很多关于Netlify CMS的部署都是使用了Netlify的服务，因为我自己的博客已经使用了GithubAction作为CI来自动部署，我的博客源文件放在hugo分支下，对hugo分支commit会触发GithubAction，然后使用进行网站构建并推送到master分支下，并且自定义域名是使用的其他域名提供商来解析的，本文主要是记录一下在这种情况下怎么为博客添加NetlifyCMS

- - -

## Netlify CMS 做什么

安装之前我们需要了解一下Netlify CMS是什么。Netlify CMS 和 Forestry 等工具一样，它可以帮助你管理你的git仓库，我们一般的主要用途就是拿它来管理git仓库中的 blog 源文件，它提供了一个友好的界面来帮助你编写你的 blog 源文件，然后后续的 git commit push 它会帮你效劳，你可以拿它来作为CI，自动帮你构建好网站，也可以只使用他的编辑推送功能，把它当作一个管理后台，让其他的CI来帮你做后面的事情。

举个例子，我有一个博客托管在 github pages，拥有自己的CI来进行博客部署，我只需要推送 markdown 博文源文件到指定分支下，即可触发构建，但是我不想每次都在本地写博客，我希望有个简单的方式来让我随时随地在线编辑发布博客，那我就可以使用 Netlify CMS，当然，你也可以使用 github.dev，不过缺点是你需要另外的工具来处理你的图片，因为 github.dev 不支持图片粘贴（相应的插件也无法安装），但是 Netlify CMS 能够通过配置来完成粘贴图片的功能，麻雀虽小五脏俱全。

## 如何部署

可能你看了不少说明文档，但是还是处于不可用的状态。其实有很大一部分原因是没有使用 Netlify 的服务，比如你的自定义域名没有托管在 Netlify。

我决定使用 Netlfify 提供给我的 `xxxx.netlify.app` 域名。最终效果是我可以直接访问该域名(`xxxx.netlify.app`) 即可管理我的博客后台。

### 建立新分支

从这里开始可能你就会发现和[说明文档](https://www.netlifycms.org/docs/add-to-your-site/)有点不一样。因为我不打算把它放置在子文件夹（`admin`）下。

首先我们 clone 我们的博客仓库。拿我自己的仓库举例子，[hugo](https://github.com/akkuman/akkuman.github.io/tree/96f4e480342a806ac633b15909155684eac53319) 是我放置博客源文件的分支。

```shell
git clone git@github.com:akkuman/akkuman.github.io.git
cd akkuman.github.io
```

然后我们新建一个分支用来托管 Netlify CMS。

```shell
git checkout --orphan netlifycms # 新建一个没有历史的分支
git rm -rf . # 把当前内容全部删除，得到一个空分支
```

当然，你可以用你自己习惯的办法创建一个新分支然后删除所有的文件，我们只需要有一个新分支，这个分支上没有任何文件。

### 创建 Netlify CMS 所需的文件

我们需要创建两个文件，一个 `index.html`，一个 `config.yml`

* index.html

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <script src=" https://identity.netlify.com/v1/netlify-identity-widget.js"></script>
  <title>Content Manager</title>
</head>
<body>
  <!-- Include the script that builds the page and powers Netlify CMS -->
  <script src="https://cdn.jsdelivr.net/npm/netlify-cms@2.10.192/dist/netlify-cms.min.js"></script>
  <script>
    if (window.netlifyIdentity) {
        window.netlifyIdentity.on("init", user => {
        if (!user) {
            window.netlifyIdentity.on("login", () => {
            document.location.href = "/";
            });
        }
        });
    }
  </script>
</body>
</html>
```

* config.yml

```yaml
backend:
  name: git-gateway
  branch: hugo # Branch to update (optional; defaults to master)
  squash_merges: true

# This line should *not* be indented
publish_mode: editorial_workflow

# These lines should *not* be indented
media_folder: "static/images/uploads" # Media files will be stored in the repo under static/images/uploads
public_folder: "/images/uploads" # The src attribute for uploaded media will begin with /images/uploads

collections:
  - name: "post" # Used in routes, e.g., /admin/collections/blog
    label: "Blog posts" # Used in the UI
    folder: "content/posts" # The path to the folder where the documents are stored
    extension: md
    create: true # Allow users to create new documents in this collection
    slug: "{{year}}-{{month}}-{{day}}-{{slug}}" # Filename template, e.g., YYYY-MM-DD-title.md
    fields: # The fields for each document, usually in front matter
      - {label: "Layout", name: "layout", widget: "hidden", default: "blog"}
      - {label: "Title", name: "title", widget: "string"}
      - {label: "Publish Date", name: "date", widget: "datetime"}
      - {label: "Show TOC", name: "showToc", widget: "boolean", default: true}
      - {label: "Draft", name: "draft", widget: "boolean", required: false, default: false}
      - {label: "Description", name: "description", widget: "string", required: false}
      - widget: object
        name: cover
        label: Cover
        required: false
        fields:
          - {label: Image, name: image, widget: string, required: false, comment: image path/url}
          - {label: Alt, name: alt, widget: string, required: false, comment: alt text}
          - {label: Caption, name: caption, widget: string, required: false, comment: display caption under cover}
          - {label: Relative, name: relative, widget: string, required: false, comment: when using page bundles set this to true}
          - {label: Hidden, name: hidden, widget: "hidden", required: false, default: false, comment: only hide on current single page}
      - {label: "Body", name: "body", widget: "markdown"}
      
```

* backend.name: 这个主要是和认证相关
* backend.branch: 这是主要是指明你的博客源文件（编写 markdown）的分支
* backend.squash_merges: 这个主要是当下面设置 `publish_mode: editorial_workflow` 时，会启用编辑文件的工作流，启用该工作流后，你编辑博客后，可以保存，Netlify CMS 会自动将你保存但未发布的 markdown 放置到一个新建的分支中去，然后你可以多次编辑保存，会在该分支上生成多次 commit，等待你发布的时候，会合并到你的 `backend.branch` 分支上去，启用 `squash_merges` 后，会将你的多次编辑 commit 合并成一个提交合并上去
* media_folder: 指明你的静态文件实际保存在哪里（在博客源文件分支中）
* public_folder: 指明你的静态文件在发布分支（即博客构建部署生成html的分支）的位置
* collections: 该配置定义了你的站点需要编辑的文件的结构，比如我需要编辑我的博客 posts，我就建立了一个 `name: "post"` 的 `collection`

  * `label: "Blog posts"`: 在NetlifyCMS中显示的标题，随便填
  * `folder: "content/posts"`: 你的博文文件放在哪
  * `extension: md`: 你的博文的后缀是什么，一般是 md
  * `slug: "{{year}}-{{month}}-{{day}}-{{slug}}"`: 博文文件命名格式
  * `fields`: 该配置下面放置你的博文header的配置，这部分配置的细节可以查看官方关于这部分内容的说明 (<https://www.netlifycms.org/docs/add-to-your-site/#collections>)

配置完成后，将这些文件发布到你仓库的 `netlifycms` 分支下，样例可参见 <https://github.com/akkuman/akkuman.github.io/tree/netlifycms>, 如果我这边文章提到的分支已经不存在，可以查看该 commit <https://github.com/akkuman/akkuman.github.io/tree/de1cc353fd345870f8e0d148593d6ee86132152b>

### NetlifyCMS 配置

配置好上面的内容后，我们需要在 Netlify 上做相关的网站配置

首先我们打开网站 <https://netlify.app/> 并注册登录，打开个人资料配置界面 

<https://app.netlify.com/user/settings#connected-accounts>，关联你的github账号

![](/images/uploads/qq截图20220713092942.png)

然后打开你的主页，按照下图创建一个站点

![](/images/uploads/qq截图20220713093707.png)

然后点击从github导入

![](/images/uploads/qq截图20220713093818.png)

选择你的博客仓库，接着按照下图配置

![](/images/uploads/c4950bb2-db81-4e52-871b-d204a3648a01.png)

其中 `Branch to deploy` 选择我们刚才为 NetlifyCMS 建立的分支，部署相关的内容全部置空，然后点击 `Deploy Site`，然后你会看到这个页面

![](/images/uploads/qq截图20220713104646.png)

等待站点部署完成后，你可以看到netlify给你提供的网站，类似于 `xxxx.netlify.app`，点击 `Site settings`，你可以在 `Site details -> Site information` 更改你的url。

访问这个网站，会提示你无法登录

![](/images/uploads/qq截图20220713105503.png)

我们打开 `Site settings -> Identity` 然后启用身份认证

首先我们需要关闭注册功能，只能邀请，否则我们的 NetlifyCMS 可能会被人滥用

![](/images/uploads/qq截图20220713105747.png)

我们进入身份管理邀请一个用户，填入邮箱

![](/images/uploads/qq截图20220713110033.png)

然后你的邮箱里面应该会收到一个邀请链接，访问后设置上密码。

此时你应该还是无法登录，会提示你需要先配置 git-gateway。

我们打开 `Site settings -> Identity -> Services -> Git Gateway`，然后启用（Enable Git Gateway）

现在你再进入你配置的 NetlifyCMS，现在你可以看到你的博客管理后台了。

功能比较简单，就不介绍如何使用了。

因为我们在配置中启用了工作流，你可以尝试尝试如何使用，具体原理是 NetlifyCMS 会给你新建一个分支来保存还未发布的在工作流中的文章，等待发布后会合并上去，详细细节可以自行研究。