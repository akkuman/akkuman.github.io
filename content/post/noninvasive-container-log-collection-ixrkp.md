---
title: 非侵入式容器日志收集
slug: noninvasive-container-log-collection-ixrkp
date: '2025-09-19 16:41:52+08:00'
lastmod: '2025-09-19 17:25:28+08:00'
tags:
  - Docker
  - SRE
keywords: Docker,SRE
description: >-
  本文介绍了使用Grafana、Loki和Alloy搭建非侵入式容器日志收集系统的方案。该系统通过监控Docker容器日志，自动推送至Loki存储，并利用Grafana进行可视化查询，无需修改应用程序代码。文章提供了Alloy配置文件示例，说明如何发现Docker容器、提取元数据（如容器名称），并添加标签区分不同主机日志。还提到可通过过滤器选择特定容器进行日志收集。最后给出了Loki的基础配置，包括保留策略和索引标签设置。该方案实现了轻量级、无代码侵入的容器日志集中管理。
toc: true
isCJKLanguage: true
---





## 前言

使用 grafana + loki + alloy 搭建日志收集系统，该系统监控机器上 docker 容器日志，然后推送至 loki，使用 grafana 进行可视化查询

相比于之前在代码中使用 promtail sdk 进行日志推送的方案，该方案无需懂代码

## config.alloy

```plaintext
// ###############################
// #### Logging Configuration ####
// ###############################

// Discover Docker containers and extract metadata.
discovery.docker "linux" {
  host = "unix:///var/run/docker.sock"
}

// Define a relabeling rule to create a service name from the container name.
discovery.relabel "logs_integrations_docker" {
      targets = []
  
      rule {
          source_labels = ["__meta_docker_container_name"]
          regex = "/(.*)"
          target_label = "container_name"
      }

     rule {
        target_label = "instance"
        replacement  = constants.hostname
    }

  }


// Configure a loki.source.docker component to collect logs from Docker containers.
loki.source.docker "default" {
  host       = "unix:///var/run/docker.sock"
  targets    = discovery.docker.linux.targets
  labels     = {"logging" = "alloy"}
  relabel_rules = discovery.relabel.logs_integrations_docker.rules
  forward_to = [loki.write.local.receiver]
}

loki.write "local" {
  endpoint {
    url = "http://loki:3100/loki/api/v1/push"
    // basic_auth {
    //   username = "<USERNAME>"
    //   password = "<PASSWORD>"
    // }
  }
}
```

​`labels = {"logging" = "alloy"}`​ 意味着给每一个日志条目添加 `logging="alloy"`​ 的 label，然后推送至 loki，可用于区分不同主机的日志

如果你希望对某些容器（而不是所有容器）进行日志收集，也可使用如下方式对容器进行过滤（详细解释请参见 [discovery.docker | Grafana Alloy documentation](https://grafana.com/docs/alloy/latest/reference/components/discovery/discovery.docker/#filter)）

```plaintext
discovery.docker "example" {
  host = "unix:///var/run/docker.sock"
  filter {
    name   = "label"
    values = ["com.example.monitoring=enabled"]
  }
  filter {
    name   = "status"
    values = ["running"]
  }
}
```

‍

## loki-config.yaml

```plaintext

# This is a complete configuration to deploy Loki backed by the filesystem.
# The index will be shipped to the storage via tsdb-shipper.

auth_enabled: false

limits_config:
  retention_period: 720h
  allow_structured_metadata: true
  volume_enabled: true
  reject_old_samples: false

distributor:
  otlp_config:
    # List of default otlp resource attributes to be picked as index labels
    # CLI flag: -distributor.otlp.default_resource_attributes_as_index_labels
      default_resource_attributes_as_index_labels: [service.name service.namespace service.instance.id deployment.environment deployment.environment.name cloud.region cloud.availability_zone k8s.cluster.name k8s.namespace.name k8s.container.name container.name k8s.replicaset.name k8s.deployment.name k8s.statefulset.name k8s.daemonset.name k8s.cronjob.name k8s.job.name]


server:
  http_listen_port: 3100

common:
  ring:
    instance_addr: 0.0.0.0
    kvstore:
      store: inmemory
  replication_factor: 1
  path_prefix: /loki

schema_config:
  configs:
  - from: 2020-05-15
    store: tsdb
    object_store: filesystem
    schema: v13
    index:
      prefix: index_
      period: 24h

compactor:
  retention_enabled: true
  delete_request_store: filesystem

storage_config:
  tsdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/index_cache
  filesystem:
    directory: /loki/chunks

pattern_ingester:
  enabled: true

```

​`retention_period: 720h`​ 意味着保留 720h 的日志供查询

​`reject_old_samples: false`​ 意味着接收比较老的日志，对于需要收集之前的日志的场景比较有用

## docker-compose.yml

```yaml
version: '3'
services:
  loki:
    image: swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/grafana/loki:3.5.5
    ports:
      - "3100:3100"
    volumes:
     - ./loki-config.yaml:/etc/loki/local-config.yaml
     - ./lokidata:/loki
    command: -config.file=/etc/loki/local-config.yaml

  grafana:
   image: swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/grafana/grafana:12.0.2
   environment:
     - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
     - GF_AUTH_ANONYMOUS_ENABLED=true
     - GF_AUTH_BASIC_ENABLED=false
   ports:
     - 3000:3000/tcp
   entrypoint:
      - sh
      - -euc
      - |
        mkdir -p /etc/grafana/provisioning/datasources
        cat <<EOF > /etc/grafana/provisioning/datasources/ds.yaml
        apiVersion: 1
        datasources:
        - name: Loki
          type: loki
          access: proxy
          orgId: 1
          url: http://loki:3100
          basicAuth: false
          isDefault: false
          version: 1
          editable: false
        EOF
        /run.sh

  alloy:
   image: swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/grafana/alloy:v1.10.2
   privileged: true
   ports:
     - 12345:12345
     - 4317:4317
     - 4318:4318
   volumes:
     - ./config.alloy:/etc/alloy/config.alloy
     - /var/run/docker.sock:/var/run/docker.sock
     - /:/rootfs:ro
     - /var/run:/var/run:rw
     - /sys:/sys:ro
     - /var/lib/docker/:/var/lib/docker:ro
     - /dev/disk/:/dev/disk:ro
   command: run --server.http.listen-addr=0.0.0.0:12345 --storage.path=/var/lib/alloy/data /etc/alloy/config.alloy

```

## 运行

```shell
mkdir -p lokidata
chmod 777 lokidata
docker compose up -d
```

## 效果

alloy 将持续拉取 docker 容器（含有特定 label）的日志，推送到 loki 供查询，grafana 可以用来可视化查询

## Reference

- [使用 Grafana Alloy 监控 Docker 容器 | Grafana Alloy 文档 --- Monitor Docker containers with Grafana Alloy | Grafana Alloy documentation](https://grafana.com/docs/alloy/latest/monitor/monitor-docker-containers/#clone-and-deploy-the-example)
