---
title: elementui 表格中带有按钮的loading解决方案
date: 2020-07-17 13:28:00
tags:
- 前端
- Tips
categories:
- 前端
---

需求：表格每一列有一个按钮字段，点击后需要loading

<!--more-->

按照普通的在 Array 对象上加属性，监听不到变化，需要使用 this.$set

比如这个样子设置

```js
getCoreLoots().then(response => {
  this.transitFileList = response.data.data
  this.transitFileList = this.transitFileList.map(item => {
    // 添加上传按钮loading
    item.uploadLoading = false
    return item
  })
  console.log(this.transitFileList)
  this.transitListLoading = false
})
```

这样子出来的结果是这样

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/1c5c9a99037fc94d82ac4aa9da40aa7b..png)

属性设置到了 `__ob__` 外面，vue监听不到变化，也就是说我们进行改变后dom不会更新

**主要的原因是**：当你把一个普通的 JavaScript 对象传入 Vue 实例作为 data 选项，Vue 将遍历此对象所有的 property，并使用 Object.defineProperty 把这些 property 全部转为 getter/setter。这些 getter/setter 对用户来说是不可见的，但是在内部它们让 Vue 能够追踪依赖，在 property 被访问和修改时通知变更。Vue 无法检测 property 的添加或移除。由于 Vue 会在初始化实例时对 property 执行 getter/setter 转化，所以 property 必须在 data 对象上存在才能让 Vue 将它转换为响应式的。

知道了原因之后我们可以做一下略微的改造

```js
getCoreLoots().then(response => {
  this.transitFileList = response.data.data
  this.transitFileList = response.data.data.map(item => {
    // 添加上传按钮loading
    item.uploadLoading = false
    return item
  })
  console.log(this.transitFileList)
  this.transitListLoading = false
})
```

![enter description here](https://raw.githubusercontent.com/akkuman/pic/master/pic/2021/8/0a54f1055f3edd195d1d96c3faabafac..png)

现在可以看到在 `__ob__` 里面了。

同样，如果你有更多的需求可以按照官方文档中的使用 set 来进行设置

例如

```js
<el-table-columnlabel="操作" width="145">
  <template slot-scope="scope">
    <el-button type="text" :loading="scope.row.uploadLoading" size="mini" @click="handleClickUploadTransitFileToTarget(scope)">上传到目标</el-button>
  </template>
</el-table-column>

...

getTransitFileList() {
  getCoreLoots().then(response => {
    this.transitFileList = response.data.data
    this.transitFileList = this.transitFileList.map(item => {
      // 添加上传按钮loading
      this.$set(item, 'uploadLoading', false)
      return item
    })
  })
},


handleClickUploadTransitFileToTarget(scope) {
  this.$set(scope.row, 'uploadLoading', true)
  uploadFileToTarget().then(response => {
    showMsg(this, `${scope.row.name} 上传成功`)
    this.$set(scope.row, 'uploadLoading', false)
  })
}

```