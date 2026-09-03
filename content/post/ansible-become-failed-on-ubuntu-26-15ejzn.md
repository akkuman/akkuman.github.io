---
title: Ubuntu 26.04 上 Ansible become 失败：sudo-rs 兼容问题及解决方案
slug: ansible-become-failed-on-ubuntu-26-15ejzn
date: '2026-09-03 14:05:49+08:00'
lastmod: '2026-09-03 14:17:49+08:00'
tags:
  - ansible
  - 运维
categories:
  - 技术分享
keywords: ansible,运维
description: >-
  在Ubuntu 26.04目标机器上运行Ansible时，使用`become`提权操作会报错`Timeout (12s) waiting for
  privilege escalation
  prompt`。根本原因是Ubuntu新版默认改用`sudo-rs`，与旧版Ansible不兼容。解决方案有三种：一是直接升级Ansible（新版已兼容）；二是临时设置环境变量`export
  ANSIBLE_BECOME_EXE=sudo.ws`；三是在ansible.cfg的`[privilege_escalation]`段中添加`become_exe
  = sudo.ws`。
toc: true
isCJKLanguage: true
---





## 背景

目标机器是 ubuntu 26.04，ansible 脚本使用了 `become` 来提权操作

但是总是报错 `Timeout (12s) waiting for privilege escalation prompt`

## 原因

ubuntu 新版换用了 `sudo-rs` 导致旧版 ansible 不兼容

可参见 [Ubuntu 26.04 默认 sudo-rs 的 sudoers 配置变更](https://www.ssdnodes.com/learn/lang/zh-hans/sudo-rs-on-ubuntu-what-changes)

## 解决方案

### 1. ~~升级 ansible~~

~~新版本 ansible 已经做了兼容~~

根据 [validate sudo become plugin against sudo-rs · Issue #85837 · ansible/ansible](https://github.com/ansible/ansible/issues/85837)

ansible-core 新版本已经修复了这个情况，并且最低反向移植到了 2.16

- 最新：似乎 [Revert "sudo become plugin: add sudo-rs prompt support (#86175) (#869… · ansible/ansible@ccaba46](https://github.com/ansible/ansible/commit/ccaba4618ec998c5e978344bec8444af7523f740) 回滚了

根据 [Releases and maintenance — Ansible Community Documentation](https://docs.ansible.com/projects/ansible/latest/reference_appendices/release_and_maintenance.html#ansible-community-changelogs) 中的映射

也就是最低 ansible 9 就可以，如果不行，请重新安装一次，确保使用了更新的 ansible-core

**最新**：ansible 官方已经回滚了所有相关的改动，将问题提交到了上游 [-p/--prompt behaviour breaks ansible · Issue #1461 · trifectatechfoundation/sudo-rs](https://github.com/trifectatechfoundation/sudo-rs/issues/1461)

看来他们认为是上游的问题，等待上游修复吧

### 2. 临时处理继续使用老旧 sudo

以下三种方案选一种

1. 环境变量 `export ANSIBLE_BECOME_EXE=sudo.ws`
2. 兼容处理

   ```yaml
       - name: Become to show id
         ansible.builtin.command:
           cmd: whoami
         become: true
         become_exe: "{{ 'sudo.ws' if ansible_facts.packages['sudo-rs'] is defined else 'sudo' }}"
         changed_when: false
         register: whoami_result
   ```

3. ansible.cfg 处理，在 ansible.cfg 中添加

   ```yaml
   [privilege_escalation]
   become_exe = sudo.ws
   ```

## Reference

- [Timeout (XXs) waiting for privilege escalation prompt -- Ubuntu 26.04 · Issue #86849 · ansible/ansible](https://github.com/ansible/ansible/issues/86849)
- [validate sudo become plugin against sudo-rs · Issue #85837 · ansible/ansible](https://github.com/ansible/ansible/issues/85837)
- [Ubuntu 26.04 默认 sudo-rs 的 sudoers 配置变更](https://www.ssdnodes.com/learn/lang/zh-hans/sudo-rs-on-ubuntu-what-changes)
