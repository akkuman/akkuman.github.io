---
title: huma 中如何和 int64 搭配使用
slug: how-to-use-inhuma-with-int64-2ojqvm
date: '2025-09-16 10:41:59+08:00'
lastmod: '2025-09-19 17:27:25+08:00'
tags:
  - Golang
keywords: Golang
description: >-
  在 Golang 中使用 Huma 框架时，处理 int64 类型（如雪花 ID）在前端 JSON 序列化中可能遇到精度问题。本文提供了解决方案：通过自定义
  BigInt 类型实现 JSON 序列化接口、Huma 的 SchemaProvider 接口生成 OpenAPI 文档，以及 ParamWrapper
  接口处理查询和路径参数，确保 int64 在前端以字符串形式安全传输。
toc: true
isCJKLanguage: true
---





golang + huma 开发过程中，如果你有过前端开发的经验，可能知道最好将 bigint（int64）（比如雪花 id）序列化成字符串（因为 js 处理 bigint 需要额外的手段）

但是这个需求在 huma 中有点麻烦

## TLDR

[huma/issues/698#issuecomment-3294634741](https://github.com/danielgtaylor/huma/issues/698#issuecomment-3294634741)

## 详解

```go
type BigInt int64

func (b *BigInt) UnmarshalJSON(data []byte) error {
	s := strings.Trim(string(data), `"`)
	if s == "" {
		*b = 0
		return nil
	}
	n, err := strconv.ParseInt(s, 10, 64)
	if err != nil {
		return err
	}
	*b = BigInt(n)
	return nil
}

func (b BigInt) MarshalJSON() ([]byte, error) {
	return fmt.Appendf(nil, `"%d"`, b), nil
}

// Define schema to use wrapped type
func (o BigInt) Schema(r huma.Registry) *huma.Schema {
	return huma.SchemaFromType(r, reflect.TypeOf(""))
}

type wrapperBigInt struct {
	b *BigInt
}

// implement encoding.TextUnmarshaler interface
func (w *wrapperBigInt) UnmarshalText(text []byte) error {
	s := strings.Trim(string(text), `"`)
	if s == "" {
		*w.b = 0
		return nil
	}
	n, err := strconv.ParseInt(s, 10, 64)
	if err != nil {
		return err
	}
	*w.b = BigInt(n)
	return nil
}

func (o *BigInt) Receiver() reflect.Value {
	a := new(wrapperBigInt)
	a.b = o
	return reflect.ValueOf(a).Elem()
}
```

1. 实现 json 序列化接口，使之在 json 序列化和反序列化中能正确表现为字符串
2. 实现 huma 的 `SchemaProvider`​ 接口 `Schema(r huma.Registry) *huma.Schema`​，使该类型生成 openapi 文档时表现为 string
3. 上面两步做完，就能正常序列化和反序列化出 json body 的参数，但是对于 query 和 path 参数不行，还需要继续
4. 实现 huma 的 `ParamWrapper`​ 接口 `Receiver() reflect.Value`​ 使该类型在接收值时表现为一个 struct，来使该类型的解析走 encoding.TextUnmarshaler [huma.go#L1560-L1565](https://github.com/danielgtaylor/huma/blob/689a87da011dd155d23b8324968f9f786fef5796/huma.go#L1560-L1565)
5. 配置 struct 同时将原始值的指针设置到一个字段上，实现 encoding.TextUnmarshaler 时将数字反序列化回原始值
