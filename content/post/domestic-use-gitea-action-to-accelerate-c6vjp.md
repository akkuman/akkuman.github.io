---
title: 国内使用 gitea action 加速
slug: domestic-use-gitea-action-to-accelerate-c6vjp
date: '2025-12-08 14:50:16+08:00'
lastmod: '2025-12-08 15:18:29+08:00'
description: |-
  本文介绍了在国内使用Gitea Actions时如何通过部署和配置act runner来加速工作流执行。主要内容包括：

  1. **部署步骤**：使用Docker Compose部署act runner，配置网络模式为host，并挂载必要的卷和配置文件。
  2. **配置优化**：
     - 替换默认的runner镜像源为国内镜像或自建registry，以解决拉取镜像慢的问题。
     - 配置GitHub镜像代理（如ghproxy），将工作流中的`actions/checkout`等操作重定向到国内镜像地址，加速代码仓库的克隆。

  通过这些调整，可以显著提升Gitea Actions在国内网络环境下的执行速度。
toc: true
isCJKLanguage: true
---





## 部署

1. 部署 gitea，打开管理界面 -> Actions -> Runners

2. 创建 runner，复制 token，假设为 nU6hLEMzujntxxxxCBz0JxmikkyIySTmoY
3. ```yaml
    services:
      act_runner:
        image: docker.1panel.live/gitea/act_runner:nightly
        container_name: act_runner
        environment:
          GITEA_INSTANCE_URL: https://git.example.com
          GITEA_RUNNER_REGISTRATION_TOKEN: nU6hLEMzujntxxxxCBz0JxmikkyIySTmoY
          GITEA_RUNNER_NAME: 运行器名称
        volumes:
          - /var/run/docker.sock:/var/run/docker.sock
          - ./data:/data
          - ./runner_cache:/root/.cache
        network_mode: host
    ```

4. 部署完成，执行命令 `sudo docker exec act_runner act_runner generate-config > config.yaml`​
5. 修改 docker-compose.yml 文件，添加 `- ./config.yaml:/config.yaml`​ 到 volumes，并添加环境变量 `CONFIG_FILE: /config.yaml`​，参见 [Act Runner | Gitea Documentation](https://docs.gitea.com/usage/actions/act-runner#start-the-runner-using-docker-compose)
6. 缓存配置：你可能会尝试按 [Act Runner | Gitea Documentation](https://docs.gitea.com/usage/actions/act-runner#configuring-cache-when-starting-a-runner-using-docker-image) 中提到的进行配置，但其实我们使用了 `network_mode: host`​，是不需要配置的

## 配置优化

最终你的 docker-compose.yml 文件应该类似于

```yaml
services:
  act_runner:
    image: docker.1panel.live/gitea/act_runner:nightly
    container_name: act_runner
    environment:
      GITEA_INSTANCE_URL: https://git.example.com
      GITEA_RUNNER_REGISTRATION_TOKEN: nU6hLEMzujntxxxxCBz0JxmikkyIySTmoY
      GITEA_RUNNER_NAME: 运行器名称
    volumes:
      - ./config.yaml:/config.yaml
      - /var/run/docker.sock:/var/run/docker.sock
      - ./data:/data
      - ./runner_cache:/root/.cache
    network_mode: host
```

### Runner 镜像替换

打开 config.yaml

默认的执行镜像为

```yaml
  labels:
    - "ubuntu-latest:docker://docker.gitea.com/runner-images:ubuntu-latest"
    - "ubuntu-24.04:docker://docker.gitea.com/runner-images:ubuntu-24.04"
    - "ubuntu-22.04:docker://docker.gitea.com/runner-images:ubuntu-22.04"

```

gitea 官方同时也在 DockerHub 推送了一份 https://hub.docker.com/r/gitea/runner-images

但可能国内网络条件不好，可以采用将镜像推送到内网自建的 docker registry 或使用 DockerHub 镜像

```yaml
  labels:
    - "ubuntu-latest:docker://docker.example.com/runner-images:ubuntu-latest"
    - "ubuntu-24.04:docker://docker.example.com/runner-images:ubuntu-24.04"
    - "ubuntu-22.04:docker://docker.example.com/runner-images:ubuntu-22.04"

```

### GHA 拉取地址替换

国内 git clone github 官方地址总是会有问题，在 [#716 - feat: support github mirror - act_runner - Gitea: Git with a cup of tea](https://gitea.com/gitea/act_runner/pulls/716) 中，提供了对于 github mirror 的支持

你可以找第三方的 github clone 镜像，也可以自己内网自建一个 github 镜像，比如我们自建一个 ghproxy.example.com

```plaintext
server {
    listen 80;
    server_name ghproxy.example.com;

    access_log          /var/log/nginx/ghproxy.example.com.access.log;
    error_log           /var/log/nginx/ghproxy.example.com.error.log warn;


    location / {
        proxy_pass https://github.com/;
        proxy_set_header Host github.com;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # 大文件传输支持
        client_max_body_size 0;
        proxy_request_buffering off;
    }
}
```

然后打开 config.yaml，添加如下内容

```yaml
runner:
  ...
  github_mirror: 'http://ghproxy.example.com'
```

如果你使用的是第三方比如 gitclone

那也可以

```yaml
runner:
  ...
  github_mirror: 'https://gitclone.com/github.com'
```

### action 中 docker 构建相关配置

如果你的 action runner 是固定的，那么最合适的方案应该是持久化一个 buildx 实例

```yaml
      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3
        with:
          image: docker.example.com/tonistiigi/binfmt:latest

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
        with:
          name: builder-act
          cleanup: false
          driver-opts: |
            image=docker.example.com/moby/buildkit:latest
```

可以看到，setup-qemu-action 和 setup-buildx-action 我们使用了自己的镜像来加速，避免网络问题

其中 buildx 我们固定了 name，并且指定了 cleanup: false，这样能保证我们多次构建使用的是同一个 buildx 实例，能够加速构建，也不需要 action 本身的缓存实现

如果你有很多个 runner，不使用 buildx 的 build cache，那么可以使用 gitea action runner 自带的缓存

### Golang 相关 action

我们知道 setup-go 和 goreleaser 这两个常用的 action 都是需要从 github 下载内容，网络不便，我 fork 了一份

用法参见如下

```yaml
      - name: Set up Go
        uses: akkuman/gitea-setup-go@gitea
        with:
          go-version-file: go.mod
          skip-download-from-github: true
          offical-download-mirror: 'https://mirrors.aliyun.com/golang'
          offical-download-metadata: 'https://hub.gitmirror.com/https://github.com/akkuman/golang-dl-metadata/raw/refs/heads/master/metadata.json'

      - name: Run GoReleaser
        uses: akkuman/gitea-goreleaser-action@gitea
        with:
          github-release-mirror: 'https://hub.gitmirror.com/https://github.com'
          distribution: goreleaser
          version: '~> v2'
          args: release --clean
        env:
          GITEA_TOKEN: ${{ secrets.PAT }}
          GITHUB_REPOSITORY_NAME: ${{ github.event.repository.name }}
```

‍
