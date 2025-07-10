---
title: Dagger 支持导出镜像到本机了
slug: dagger-supports-exporting-images-to-the-local-machine-z2afl2o
date: '2025-07-10 14:41:36+08:00'
lastmod: '2025-07-10 14:58:39+08:00'
tags:
  - Dagger
keywords: Dagger
description: >-
  Dagger最新功能支持将构建的容器镜像直接导出到本地运行时环境，无需再通过tarball中转。新增`export-image`命令和`_EXPERIMENTAL_DAGGER_RUNNER_IMAGESTORE`环境变量，支持containerd（默认）和docker-image两种导出方式。其中docker-image方式仍依赖docker-cli进行加载，而containerd可直接使用默认socket地址或通过CONTAINERD_ADDRESS自定义。该功能简化了镜像导出流程，但docker-image的实现方式仍存在优化空间。
toc: true
isCJKLanguage: true
---





原文链接: [Dagger 支持导出镜像到本机了 | Akkuman 的技术博客](https://www.hacktech.cn/post/2025/07/dagger-supports-exporting-images-to-the-local-machine-z2afl2o/)

[✨ Import image to local container runtime · Issue #8025 · dagger/dagger](https://github.com/dagger/dagger/issues/8025) 这个 issue 从 2024.07 挂到现在（2025.07），官方总算是实现了

之前想使用 dagger 构建镜像并且导出到本地，需要先导出成 tarball 包，然后再使用本地的 docker load 进行导入

在昨天（2025.07.09），[Allow loading `Container`s to host by jedevc · Pull Request #10662 · dagger/dagger](https://github.com/dagger/dagger/pull/10662)   这个 PR 被合并了，后续就可以直接将 dagger 构建的镜像导出到本地了

等 Dagger 新版发布后，我们就可以使用如下命令进行导出了

- ​`dagger call base export-image --name myimage`​
- ​`dagger -c 'base | export-image myimage'`​

并且暴露了一个环境变量 `_EXPERIMENTAL_DAGGER_RUNNER_IMAGESTORE`​

该变量支持两个值

- containerd
- docker-image

根据 [Allow loading `Container`s to host by jedevc · Pull Request #10662 · dagger/dagger](https://github.com/dagger/dagger/pull/10662/files#diff-448541f65c746ae84ee147ae015fba3b5ec91860e9a57cc4507795041ad79dd7)   和 [Allow loading `Container`s to host by jedevc · Pull Request #10662 · dagger/dagger](https://github.com/dagger/dagger/pull/10662/files#diff-448541f65c746ae84ee147ae015fba3b5ec91860e9a57cc4507795041ad79dd7)   这两部分代码，我们可以看出这两个值的效果

- containerd：默认使用 "github.com/containerd/containerd/defaults".DefaultAddress，如果想自定义 containerd 地址，需配合 CONTAINERD_ADDRESS 环境变量使用
- docker-image：需要保证 docker 命令存在（即存在 docker-cli），实际上内部的操作依旧是生成 tarball，然后管道调用 docker load，最后将对应的 imageid 设置为你定义的名称

总的来说，内置支持比之前自己写管道命令要省事一些，唯一的不爽就是 docker-image 居然是调用 docker-cli，就不能像 containerd 一样，直接调用 docker.sock 暴露的 api 吗
