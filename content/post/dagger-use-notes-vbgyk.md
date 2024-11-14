---
title: Dagger 使用札记
slug: dagger-use-notes-vbgyk
url: /post/dagger-use-notes-vbgyk.html
date: '2024-11-04 15:30:22+08:00'
lastmod: '2024-11-12 18:01:13+08:00'
toc: true
isCJKLanguage: true
tags:
  - DevOps
  - Dagger
keywords: DevOps,Dagger
description: Dagger 用来简化和标准化复杂的 CI/CD 管道，本文介绍了它的使用技巧
---

# Dagger 使用札记

## 工具介绍

用于构建 DevOps 工作流的开源平台，旨在简化和标准化复杂的 CI/CD 管道。

Dagger 提供了 Go/Python/TypeScript 等语言的 sdk，使你能使用这些语言来操作 BuildKit 来生成或推送你想要的文件或镜像

## 用法

以下的安装和初始化给出了国内网络环境下的使用

### 安装

工欲善其事必先利其器，首先就是需要下载使用

首先可以按照官网 [Installation | Dagger](https://docs.dagger.io/install/) 来进行安装

```bash
curl -fsSL https://dl.dagger.io/dagger/install.sh | BIN_DIR=/usr/local/bin sudo -E sh
```

### 初始化

我们可以使用如下命令对我们已有的项目进行初始化

```bash
dagger init --sdk=go --source=./dagger
```

但是你可能会碰到如下错误

```plaintext
✘ connect 17.0s
! start engine: failed to pull image: failed to run command: exit status 1
  ✘ starting engine 17.0s
  ! failed to pull image: failed to run command: exit status 1
    ✘ create 17.0s
    ! failed to pull image: failed to run command: exit status 1
      ✔ exec docker ps -a --no-trunc --filter name=^/dagger-engine- --format {{.Names}} 0.3s
      ✘ exec docker inspect --type=image registry.dagger.io/engine:v0.13.7 0.0s
      ! failed to run command: exit status 1
      ┃ []                                                                                                                                                                                                       
      ┃ Error response from daemon: No such image: registry.dagger.io/engine:v0.13.7                                                                                                                             
      ✘ exec docker pull registry.dagger.io/engine:v0.13.7 16.7s
      ! failed to run command: exit status 1
      ┃ Error response from daemon: Get "https://registry.dagger.io/v2/": net/http: request canceled while waiting for connection (Client.Timeout exceeded while awaiting headers)                               

Error: start engine: failed to pull image: failed to run command: exit status 1
```

错误提示我们拉取不到镜像，很明显是网络问题

根据以下链接

* [记录如何在私有 Intranet 中运行 dagger · 问题 #6275 · dagger/dagger --- Document how to run dagger in a private intranet · Issue #6275 · dagger/dagger](https://github.com/dagger/dagger/issues/6275)
* [缺少有关如何在公司代理后面使用 dagger 的文档 · 问题 #5240 · dagger/dagger --- Missing documentation on how to use dagger behind a corporate proxy · Issue #5240 · dagger/dagger](https://github.com/dagger/dagger/issues/5240)
* [支持本地调试远程引擎·问题#25852·airbytehq/airbyte --- Support for debugging remote engines locally · Issue #25852 · airbytehq/airbyte](https://github.com/airbytehq/airbyte/issues/25852)

我们可以得到一个解决方案（文档参见 [Custom Runner | Dagger](https://docs.dagger.io/configuration/custom-runner)）

```bash
export _EXPERIMENTAL_DAGGER_RUNNER_HOST=docker-image://ghcr.nju.edu.cn/dagger/engine:v0.13.7
dagger init --sdk=go --source=./dagger
```

但可能还是会报错

```plaintext
✔ connect 7m19.9s
✔ cache request: mkfile /schema.json 0.0s
✔ mkfile /schema.json 0.1s
✔ cache request: blob://sha256:ccfd910d90eb8e37ae8d9131e99f63cec19c582e841db89062a05342514c2165 0.0s
✔ blob://sha256:ccfd910d90eb8e37ae8d9131e99f63cec19c582e841db89062a05342514c2165 0.0s
✔ moduleSource(refString: "."): ModuleSource! 0.0s
✔ ModuleSource.kind: ModuleSourceKind! 0.0s
✔ ModuleSource.resolveContextPathFromCaller: String! 0.0s
✔ ModuleSource.withName(name: "z_deploy"): ModuleSource! 0.0s
✔ ModuleSource.withSDK(sdk: "go"): ModuleSource! 0.0s
✔ ModuleSource.withInit: ModuleSource! 0.0s
✔ ModuleSource.withSourceSubpath(path: "dagger"): ModuleSource! 0.0s
✔ ModuleSource.resolveFromCaller: ModuleSource! 0.2s
✘ ModuleSource.asModule(engineVersion: "latest"): Module! 45.2s
! failed to create module: select: failed to update codegen and runtime: failed to generate code: failed to get modified source directory for go module sdk codegen: select: process "codegen --output /src --module-context-path /src/z_deploy/dagger --module-name z_deploy --introspection-json-path /schema.json --merge=false" did not complete successfully: exit code: 1

Error: failed to generate code: input: moduleSource.withContextDirectory.withName.withSDK.withSourceSubpath.withInit.asModule resolve: failed to create module: select: failed to update codegen and runtime: failed to generate code: failed to get modified source directory for go module sdk codegen: select: process "codegen --output /src --module-context-path /src/z_deploy/dagger --module-name z_deploy --introspection-json-path /schema.json --merge=false" did not complete successfully: exit code: 1

Stdout:
generating go module: z_deploy
creating directory . [skipped]
creating directory z_deploy [skipped]
creating directory z_deploy/dagger [skipped]
writing z_deploy/dagger/dagger.gen.go
writing z_deploy/dagger/go.mod
writing z_deploy/dagger/go.sum
creating directory z_deploy/dagger/internal
creating directory z_deploy/dagger/internal/dagger
writing z_deploy/dagger/internal/dagger/dagger.gen.go
creating directory z_deploy/dagger/internal/querybuilder
writing z_deploy/dagger/internal/querybuilder/marshal.go
writing z_deploy/dagger/internal/querybuilder/querybuilder.go
creating directory z_deploy/dagger/internal/telemetry
writing z_deploy/dagger/internal/telemetry/attrs.go
writing z_deploy/dagger/internal/telemetry/env.go
writing z_deploy/dagger/internal/telemetry/exporters.go
writing z_deploy/dagger/internal/telemetry/init.go
writing z_deploy/dagger/internal/telemetry/live.go
writing z_deploy/dagger/internal/telemetry/logging.go
writing z_deploy/dagger/internal/telemetry/metrics.go
writing z_deploy/dagger/internal/telemetry/proxy.go
writing z_deploy/dagger/internal/telemetry/span.go
writing z_deploy/dagger/internal/telemetry/transform.go
writing z_deploy/dagger/main.go
creating directory z_deploy/dagger/internal [skipped]
creating directory z_deploy/dagger/internal/dagger [skipped]
writing z_deploy/dagger/internal/dagger/dagger.gen.go [skipped]
creating directory z_deploy/dagger/internal/querybuilder [skipped]
writing z_deploy/dagger/internal/querybuilder/marshal.go [skipped]
writing z_deploy/dagger/internal/querybuilder/querybuilder.go [skipped]
creating directory z_deploy/dagger/internal/telemetry [skipped]
writing z_deploy/dagger/internal/telemetry/attrs.go [skipped]
writing z_deploy/dagger/internal/telemetry/env.go [skipped]
writing z_deploy/dagger/internal/telemetry/exporters.go [skipped]
writing z_deploy/dagger/internal/telemetry/init.go [skipped]
writing z_deploy/dagger/internal/telemetry/live.go [skipped]
writing z_deploy/dagger/internal/telemetry/logging.go [skipped]
writing z_deploy/dagger/internal/telemetry/metrics.go [skipped]
writing z_deploy/dagger/internal/telemetry/proxy.go [skipped]
writing z_deploy/dagger/internal/telemetry/span.go [skipped]
writing z_deploy/dagger/internal/telemetry/transform.go [skipped]
running post-command: go mod tidy
post-command failed: exit status 1
Stderr:
go: downloading github.com/stretchr/testify v1.9.0
go: github.com/go-logr/stdr@v1.2.2 requires
        github.com/go-logr/logr@v1.2.2: Get "https://proxy.golang.org/github.com/go-logr/logr/@v/v1.2.2.mod": dial tcp 142.250.217.113:443: i/o timeout
Error: exit status 1
```

我搜索了一下，在这里找到了方案

* [🐞 Dagger 模块在企业环境中崩溃 · Issue #6599 · dagger/dagger --- 🐞 Dagger modules break in corporate environments · Issue #6599 · dagger/dagger](https://github.com/dagger/dagger/issues/6599)
* [engine: support for system proxy settings by sipsma · Pull Request #7255 · dagger/dagger](https://github.com/dagger/dagger/pull/7255)

我们可以设置 `_DAGGER_ENGINE_SYSTEMENV_GOPROXY`​ 环境变量，让我们试试

```bash
export _DAGGER_ENGINE_SYSTEMENV_GOPROXY=https://goproxy.cn,direct
# 使用 -vvv 打印更丰富的日志
dagger init --sdk=go --source=./dagger -vvv
```

我们会发现还是报同样的错误，我在 [🐞 Dagger 模块在企业环境中崩溃 · Issue #6599 · dagger/dagger --- 🐞 Dagger modules break in corporate environments · Issue #6599 · dagger/dagger](https://github.com/dagger/dagger/issues/6599#issuecomment-2455461588) 问了下大家，发现这个环境变量并不是作用于客户端，而是引擎。

通过我们上面 `-vvv`​ 可以看到实际调用的 `docker run`​ 命令是

```bash
docker run --name dagger-engine-v0.13.7 -d --restart always -v /var/lib/dagger --privileged ghcr.nju.edu.cn/dagger/engine:v0.13.7 --debug
```

所以最终的处理方案是

```bash
export _EXPERIMENTAL_DAGGER_RUNNER_HOST=docker-image://ghcr.nju.edu.cn/dagger/engine:v0.13.7
docker run --name dagger-engine-v0.13.7 -d --restart always -v /var/lib/dagger -e _DAGGER_ENGINE_SYSTEMENV_GOPROXY=https://goproxy.cn,direct --privileged ghcr.nju.edu.cn/dagger/engine:v0.13.7 --debug
dagger init --sdk=go --source=./dagger -vvv
```

将 `_EXPERIMENTAL_DAGGER_RUNNER_HOST`​ 设置为 `docker-image://ghcr.nju.edu.cn/dagger/engine:v0.13.7`​ 将会指示 dagger 客户端查找当前是否有对应镜像的容器正在运行，如果没有，则按照内置的命令创建一个。或者你也可以使用 `docker-container://dagger-engine-v0.13.7`​ 直接指定容器。

## 使用样例

这里给出一个使用样例，我们希望有的功能清单为

* 编译出二进制
* 编译多架构 Docker 镜像并推送到远端

### 目录结构

```plaintext
.
├── dagger.json
├── dagger
│   ├── ...
│   └── main.go
├── .goreleaser.yaml
├── makefile
├── go.mod
└── go.sum
```

### 文件内容

#### dagger/main.go

```go
package main

import (
	"context"
	"fmt"
	"strings"
	"time"

	"dagger/peien-engine/internal/dagger"
)

type MyEngine struct{}

func (m *MyEngine) joinCommands(cmds []string) string {
	return strings.Join(cmds, " && ")
}

func (m *MyEngine) BuildApp(ctx context.Context, src *dagger.Directory, token *dagger.Secret) *dagger.Container {
	// build app
	builder := dag.Container().
		From("golang:1.22-bullseye").
		WithSecretVariable("GITEA_TOKEN", token).
		WithWorkdir("/src").
		WithMountedCache("/go/pkg/mod", dag.CacheVolume("go-mod")).
		WithEnvVariable("GOMODCACHE", "/go/pkg/mod").
		WithMountedCache("/go/build-cache", dag.CacheVolume("go-build")).
		WithEnvVariable("GOCACHE", "/go/build-cache").
		WithEnvVariable("CGO_ENABLED", "0").
		WithEnvVariable("GOPROXY", "https://goproxy.cn,direct").
		WithEnvVariable("GOINSECURE", "gitprivate.com").
		WithEnvVariable("GOPRIVATE", "gitprivate.com").
		WithExec([]string{"sh", "-c", m.joinCommands([]string{
			"curl -L -o goreleaser_Linux_x86_64.tar.gz https://files.m.daocloud.io/github.com/goreleaser/goreleaser/releases/download/v2.3.2/goreleaser_Linux_x86_64.tar.gz",
			"tar -xzvf goreleaser_Linux_x86_64.tar.gz -C /usr/local/bin goreleaser",
			"chmod +x /usr/local/bin/goreleaser",
			"rm -rf goreleaser_Linux_x86_64.tar.gz",
		})}).
		WithExec([]string{"sh", "-c", `git config --global url."http://${GITEA_TOKEN}@gitprivate.com".insteadOf "http://gitprivate.com"`}).
		WithDirectory("/src", src).
		WithExec([]string{"sh", "-c", m.joinCommands([]string{
			"goreleaser build --skip=validate --clean",
			"mv dist/my-engine_linux_amd64_v1 dist/my-engine_linux_amd64",
		})})
	return builder
}



func (m *MyEngine) buildImage(platform dagger.Platform, src *dagger.Directory, appName string, version string, builder *dagger.Container) *dagger.Container {
	osArch := strings.Split(string(platform), "/")[1]
	ctr := dag.Container(dagger.ContainerOpts{Platform: platform}).
		From("debian:bullseye-slim").
		WithLabel("org.opencontainers.image.version", version).
		WithLabel("org.opencontainers.image.created", time.Now().String()).
		WithWorkdir("/app").
		WithEnvVariable("TZ", "Asia/Shanghai").
		WithExec([]string{"sh", "-c", m.joinCommands([]string{
			"sed -i 's|http://deb.debian.org/debian|http://mirror.sjtu.edu.cn/debian|g' /etc/apt/sources.list",
			"sed -i '/security.debian.org/d' /etc/apt/sources.list",
			"apt-get update",
			"apt-get -qq install -y --no-install-recommends ca-certificates curl openssl firefox-esr firefox-esr-l10n-zh-cn wget fontconfig",
			// 清理 apt 缓存
			"apt-get clean -y",
			"rm -rf /var/lib/apt/lists/*",
		})}).
		WithFile(fmt.Sprintf("/app/%s", appName), builder.File(fmt.Sprintf("/src/dist/%s_linux_%s/%s", appName, osArch, appName))).
		WithEntrypoint([]string{fmt.Sprintf("/app/%s", appName)})
	return ctr
}

func (m *MyEngine) BuildOneImage(
	ctx context.Context,
	src *dagger.Directory,
	// GITEA TOKEN
	token *dagger.Secret,
	// +optional
	// +default=""
	imageName string,
	// +optional
	// +default="unknown"
	version string,
) (*dagger.Container, error) {
	builder := m.BuildApp(ctx, src, token)
	appName := "my-engine"
	ctr := m.buildImage("linux/amd64", src, appName, version, builder)
	if imageName == "" {
		imageName = fmt.Sprintf("docker-registry.com/akkuman/%s:easm-dev", appName)
	}
	ctr = ctr.WithAnnotation("io.containerd.image.name", imageName)
	return ctr, nil
}

func (m *MyEngine) BuildAllImagePublish(
	ctx context.Context,
	src *dagger.Directory,
	token *dagger.Secret,
	version string,
	registryUser string,
	registryPass *dagger.Secret,
) ([]string, error) {
	builder := m.BuildApp(ctx, src, token)
	var platforms = []dagger.Platform{
		"linux/amd64", // a.k.a. x86_64
		"linux/arm64", // a.k.a. aarch64
	}
	var imageRepos []string
	appName := "my-engine"
	platformVariants := make([]*dagger.Container, 0, len(platforms))
	for _, platform := range platforms {
		ctr := m.buildImage(platform, src, appName, version, builder)
		platformVariants = append(platformVariants, ctr)
	}
	imageRepo := []string{
		fmt.Sprintf("docker-registry.com/akkuman/%s:latest", appName),
		fmt.Sprintf("docker-registry.com/akkuman/%s:%s", appName, version),
	}
	for _, repoAddr := range imageRepo {
		addr, err := dag.Container().WithRegistryAuth("docker-registry.com/", registryUser, registryPass).Publish(ctx, repoAddr, dagger.ContainerPublishOpts{
			PlatformVariants: platformVariants,
		})
		if err != nil {
			return nil, err
		}
		imageRepos = append(imageRepos, addr)
	}
	return imageRepos, nil
}
```

#### makefile

```makefile
build:
	goreleaser build --skip=validate --clean
dagger-build:
	# 编译后可在 dist 目录下查看
	dagger call build-app --src=. --token=env:GITEA_TOKEN directory --path="/src/dist" export --path="./dist"
image-build-export:
	# 构建 amd64 镜像并导出到 my-engine.tgz
	dagger call build-one-image --src=. --token=env:GITEA_TOKEN export --path=my-engine.tgz
build-all-publish:
	# 构建多架构镜像并推送
	dagger call build-all-image-publish --src=. --token=env:GITEA_TOKEN --version="$GIT_TAG" --registry-user="$DOCKER_USERNAME" --registry-pass=env:DOCKER_PASSWORD

```

## 一些 Tips

### Dagger CLI 某些功能可以和代码等同

拿 Golang 编译然后导出到本地目录做演示

```go
package main

import (
	"context"
	"fmt"
	"strings"
	"time"

	"dagger/peien-engine/internal/dagger"
)

type PeienEngine struct{}

func (m *PeienEngine) joinCommands(cmds []string) string {
	return strings.Join(cmds, " && ")
}

func (m *PeienEngine) BuildApp(ctx context.Context, src *dagger.Directory, token *dagger.Secret) *dagger.Container {
	// build app
	builder := dag.Container().
		...
		WithExec([]string{"sh", "-c", m.joinCommands([]string{
			"goreleaser build --skip=validate --clean",
			"mv dist/engine_linux_amd64_v1 dist/engine_linux_amd64",
		})})

	return builder
}
```

1. 可以使用如下命令导出编译产物

    ```bash
    # 编译后可在 dist 目录下查看
    dagger call build-app --src=. --token=env:GITEA_TOKEN directory --path="/src/dist" export --path="./dist"
    ```

2. 也可以新建一个函数

    ```go
    func (m *PeienEngine) BuildAndExport(ctx context.Context, src *dagger.Directory, token *dagger.Secret) (string, error) {
    	return m.BuildApp(ctx, src, token).Directory("/src/dist").Export("./dist")
    }
    ```

    然后执行命令 `dagger call build-and-export --src=. --token=env:GITEA_TOKEN`​

### WithExec 不会合并成一层

我们写 Dockerfile 的时候，常常为了体积考虑，会把几行命令写成一行，比如上面的

```dockerfile
RUN goreleaser build --skip=validate --clean && \
	mv dist/engine_linux_amd64_v1 dist/engine_linux_amd64
```

如果写成两行的话，则编译出来会占用编译产物的所有体积，然后下面的 `mv`​ 又会占用一次体积。

而 Dagger 官方示例中处处都是类似下面这种

```go
...
WithExec([]string{"goreleaser", "build", "--skip=validate", "--clean"}).
WithExec([]string{"mv", "dist/engine_linux_amd64_v1", "dist/engine_linux_amd64"})
```

最开始我以为既然官方示例这么写，那应该会自动合并，但是我使用 [dive](https://github.com/wagoodman/dive) 查看后，发现并没有合并，上面这种写法基本等同下面两行 `RUN`​

```dockerfile
RUN goreleaser build --skip=validate --clean
RUN mv dist/engine_linux_amd64_v1 dist/engine_linux_amd64
```

所以需要合并的，最好使用 `sh -c`​ 来合并，例如

```go
WithExec([]string{"sh", "-c","goreleaser build --skip=validate --clean && mv dist/engine_linux_amd64_v1 dist/engine_linux_amd64")})
```

### 操作是有序的

可能我们会看到很多 WithX 操作，比如

```go
builder := dag.Container().
		From("golang:1.22-bullseye").
		WithSecretVariable("GITEA_TOKEN", token).
		WithWorkdir("/src").
		WithMountedCache("/go/pkg/mod", dag.CacheVolume("go-mod")).
		WithEnvVariable("GOMODCACHE", "/go/pkg/mod").
		WithMountedCache("/go/build-cache", dag.CacheVolume("go-build")).
		WithEnvVariable("GOCACHE", "/go/build-cache").
		WithEnvVariable("CGO_ENABLED", "0").
		WithEnvVariable("GOPROXY", "https://goproxy.cn,direct").
		WithExec([]string{"sh", "-c", m.joinCommands([]string{
			"curl -L -o goreleaser_Linux_x86_64.tar.gz https://github.com/goreleaser/goreleaser/releases/download/v2.3.2/goreleaser_Linux_x86_64.tar.gz",
			"tar -xzvf goreleaser_Linux_x86_64.tar.gz -C /usr/local/bin goreleaser",
			"chmod +x /usr/local/bin/goreleaser",
			"rm -rf goreleaser_Linux_x86_64.tar.gz",
		})}).
		WithDirectory("/src", src).
		WithExec([]string{"sh", "-c", m.joinCommands([]string{
			"goreleaser build --skip=validate --clean",
			"mv dist/peien-engine_linux_amd64_v1 dist/peien-engine_linux_amd64",
			"mv dist/peien-node_linux_amd64_v1 dist/peien-node_linux_amd64",
		})})
```

需要注意这些操作都是有序的，比如官方很多样例把 `WithDirectory("/src", src)`​ 放在最前面，就导致任何一点变动都会影响后续所有流程，正确的方法是放在编译前，就和我们平时写 Dockerfile 考虑的层级构造一样，是有序的，变动多的往后放。

### Dagger 开发环境恢复

TLDR: `dagger develop`​ 即可安装 SDK

当我们使用 `init`​ 创建一个 Dagger 流程后，会发现它生成的文件夹里面排除了生成的 sdk，参见以下 `.gitignore`​ 示例

```plaintext
/dagger.gen.go
/internal/dagger
/internal/querybuilder
/internal/telemetry
```

也就是这些文件不会签入 git 仓库，和其他人协作开发时，这些文件不会同步，虽说这对于 Dagger 各种命令的运行不影响（Dagger内部会构建环境），这些文件是供我们开发 Dagger 流程的。

我们可以使用命令 `dagger develop`​ 来生成这些 SDK 文件，这个命令会找到项目下面生成的 dagger.json 文件，然后根据里面的配置在对应的文件夹生成 SDK

以上说明可参见

* [✨ Cannot update SDK when using newer version of Dagger · Issue #7964 · dagger/dagger](https://github.com/dagger/dagger/issues/7964)
* [CLI Reference | Dagger](https://docs.dagger.io/reference/cli/#dagger-develop)

### dagger.gen.go 报错

有时候你想改变 `main.go`​ 的导出函数名称，会看到类似这样的报错

```plaintext
(*PeienEngine).BuildOneImage undefined (type *PeienEngine has no field or method BuildOneImage)
```

此时你需要使用上面提到的 `dagger develop`​ 来重新生成 `dagger.gen.go`​

不过不运行也没关系，就是 IDE 或编辑器会有错误提示而已，实际运行不影响

### 导出镜像 tarball 设置镜像tag

问题描述：使用 export 导出的镜像 tarball 是没有 tag 的

解决方案：添加 `io.containerd.image.name`​ 的 `annotation`​ 即可，代码示例如下

```go
...
builder := dag.Container().
		From("golang:1.22-bullseye").
		...
		WithAnnotation("io.containerd.image.name", fmt.Sprintf("akkuman/testapp:%s", version))
...
```

其中 `WithAnnotation("io.containerd.image.name", fmt.Sprintf("akkuman/testapp:%s", version))`​ 将会设置镜像 tag

相关 issue:

* [✨ `.AsTarball` Add OCI manifest RepoTags · Issue #7368 · dagger/dagger](https://github.com/dagger/dagger/issues/7368)
* [[Container.Export] Support custom annotations for exporting oci tar. · Issue #6999 · dagger/dagger](https://github.com/dagger/dagger/issues/6999)
* [✨ Import image to local container runtime · Issue #8025 · dagger/dagger](https://github.com/dagger/dagger/issues/8025#issuecomment-2250667221)

### .dockerignore 不起效

我们知道，Docker 构建时可以使用 .dockerignore 来排除一些文件的导入，但似乎 Dagger 不会依照 .dockerignore

查阅文档 [Directory Filters | Dagger](https://docs.dagger.io/api/filters/)，发现需要指定

例如

```go
package main

import (
	"context"
	"dagger/my-module/internal/dagger"
)

type MyModule struct{}

func (m *MyModule) Foo(
	ctx context.Context,
	// +ignore=[".git", "**/.gitignore"]
	source *dagger.Directory,
) (*dagger.Container, error) {
	return dag.Container().
		From("alpine:latest").
		WithDirectory("/src", source).
		Sync(ctx)
}
```

可以查看其中的 `+ignore`​，详情参阅 [Directory Filters | Dagger](https://docs.dagger.io/api/filters/)

### 如何限制某个参数是特定选项值

这是一个类似枚举的需求，如果没有仔细查阅文档，可能会这样做

```go
func (m *MyApp) BuildOneImage(
	ctx context.Context,
	src *dagger.Directory,
	appTag string,
) (*dagger.Container, error) {
	if appTag != "engine" && appTag != "node" {
		return nil, fmt.Errorf("appTag 必须为 engine 或者 node")
	}
	...
}
```

但实际上 Dagger 支持枚举，可以改成

```go
type AppTag string

const (
	EngineAppTag AppTag = "engine"
	NodeAppTag AppTag = "node"
)

func (m *MyApp) BuildOneImage(
	ctx context.Context,
	src *dagger.Directory,
	appTag AppTag,
) (*dagger.Container, error) {
	...
}
```

这样除了可以简化自己的判断之外，也可以使用 `dagger call build-one-image --help`​ 在帮助中查看到

```go
ARGUMENTS
      --app-tag engine,node   [required]
```

详情参见 [Enumerations | Dagger](https://docs.dagger.io/api/enumerations)

### 使用 dag.Container().From("alpine:latest") 无法拉取镜像

国内因为网络问题，无法拉取到 docker.io 上的镜像，但是 `dagger call`​ 的执行实际上在 dagger engine 容器中，所以拉取时不会依照本地设置的 `/etc/docke/daemon.json`​

这时我们可以采用手动运行 Dagger Engine 服务容器的方式，指定 Dagger Eninge 的 engine.toml

例如，创建文件 `engine.toml`​，注意：其中的镜像换成自己的要使用的镜像地址

```toml
[registry."docker.io"]
  mirrors = ["mirror.a.com", "mirror.b.com"]
```

然后手动运行 Engine

```bash
docker run --rm -v /var/lib/dagger --name customized-dagger-engine --privileged --volume $PWD/engine.toml:/etc/dagger/engine.toml ghcr.nju.edu.cn/dagger/engine:v0.13.7
```

然后配置环境变量指定 Dagger CLI 使用该 Dagger Engine 服务

```bash
export _EXPERIMENTAL_DAGGER_RUNNER_HOST=docker-container://customized-dagger-engine
```

接下来再使用 Dagger CLI 执行 `dagger call`​ 各种 `From`​ 拉取就不会有问题了

详情参见

* [Custom Registry Mirrors | Dagger](https://docs.dagger.io/configuration/custom-registry)
* [Custom Runner | Dagger](https://docs.dagger.io/configuration/custom-runner)

### Dagger 缓存占据了很大空间，如何清理

缓存大小可以使用 BuildKit 垃圾收集配置来控制，也可以使用如下命令清理 Dagger Engine 的所有缓存

```bash
dagger query <<EOF
{
  daggerEngine {
    localCache {
      prune
    }
  }
}
EOF
```

### Github Action 中如何保留缓存

不幸的是，很难用，因为 Docker 构建在 GHA 中是二等公民，这里提供一些链接参考

* [No information on caching for CI environments · Issue #6911 · dagger/dagger](https://github.com/dagger/dagger/issues/6911)
* [🐞 Fail to export cache with _EXPERIMENTAL_DAGGER_CACHE_CONFIG (`failed to compute blob by overlay differ (ok=false)`) · Issue #8717 · dagger/dagger](https://github.com/dagger/dagger/issues/8717)
* [(334) Discord | &quot;actions/cache&quot; | Dagger](https://discord.com/channels/707636530424053791/1165204052154535956)
* [Cache management | Docker Docs](https://docs.docker.com/build/ci/github-actions/cache/#github-cache)

## 为什么是 Dagger 而不是 Earthly

Earthly 我也用过，好处是和 Dockerfile 语法基本一致，基本上会写 Dockerfile 就会写 Earthfile。

具体来说，Earthly 使用下来没啥太致命的缺点，目前发现的一个问题是有些语法在 Dockerfile 中可以，但在 Earthfile 中就不行了，没有及时与 Dockerfile 上游对齐

另一方面是从 github 仓库来看，Earthly 不如 Dagger 活跃，毕竟 Dagger 是 Docker 创始人牵头，有一定的明星效应，能吸引更多的人来参与开源维护。

其实从语法来看，我觉得分不出太大优劣，使用 Dockerfile 的语法缺点是灵活性不如编程语言高，但优点是便于维护。

如果是之前使用 CUE 语言的 Dagger，那我觉得不如使用 Earthly 了，不需要多学一门语言，但现在 Dagger 改成了使用编程语言维护，使用 Dagger SDK 来构建，这样就比之前方便多了。

我目前发现了 Earthly 的两个 bug

* [Unexpected environment variable substitution · Issue #4305 · earthly/earthly](https://github.com/earthly/earthly/issues/4305)
* [`ENV` doesn&apos;t support setting multiple values · Issue #3959 · earthly/earthly](https://github.com/earthly/earthly/issues/3959)

官方也不是很积极。

就目前项目前景来看，可能 Dagger 更好一些
