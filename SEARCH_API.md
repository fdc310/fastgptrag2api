# POST /search — 知识库搜索

## 概述

调用方传入搜索文本和搜索参数，服务端自动根据 token 中的设备名解析 `datasetId`，转发给 FastGPT 并返回结果。调用方无需关心 `datasetId`。

---

## 认证

使用 **AES-256-CBC token** 认证。token 内含 `device_name` + `timestamp`，有效期 5 分钟。

### 生成 Token

用项目自带脚本：

```bash
python scripts/generate_token.py <device_name>
```

输出示例：

```
Device:   test_07
TTL:      300s
Token:    0krw17tMaEYcfHd7wdxhaVAJKHABxoviX63UC4fDgWT9sF02itSEGkRyYGDopQDa...

curl example:
  curl -H "Authorization: Bearer 0krw17tMa..." http://localhost:8000/health
```

---

## 请求

### 方法 & 路径

```
POST /search
```

### 请求头

| 请求头 | 必填 | 说明 |
|---|---|---|
| `Authorization` | 是 | `Bearer <AES_TOKEN>` |
| `Content-Type` | 否 | `application/json`（默认） |

### 请求体

```json
{
  "text": "搜索关键词或问题",
  "limit": 5000,
  "similarity": 0,
  "searchMode": "embedding",
  "usingReRank": false,
  "datasetSearchUsingExtensionQuery": false,
  "datasetSearchExtensionModel": "gpt-4o-mini",
  "datasetSearchExtensionBg": ""
}
```

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `text` | string | **是** | — | 搜索文本 |
| `limit` | int | 否 | `5000` | 最大返回条数 |
| `similarity` | float | 否 | `0` | 最小相似度阈值（0–1）。`0` 表示不过滤 |
| `searchMode` | string | 否 | `"embedding"` | 搜索模式，见下表 |
| `usingReRank` | bool | 否 | `false` | 是否启用重排序，精度更高但延迟增加 |
| `datasetSearchUsingExtensionQuery` | bool | 否 | `false` | 是否用 LLM 扩展查询词 |
| `datasetSearchExtensionModel` | string | 否 | `"gpt-4o-mini"` | 查询扩展使用的模型 |
| `datasetSearchExtensionBg` | string | 否 | `""` | 查询扩展的背景提示词 |

### 搜索模式

| 模式 | 说明 | 典型延迟 |
|---|---|---|
| `embedding` | 向量语义检索 | ~230ms |
| `fullTextRecall` | 全文关键词检索 | ~100ms |
| `mixedRecall` | 向量 + 全文混合检索 | ~180ms |

---

## 响应

### 成功 (200)

```json
{
  "code": 200,
  "statusText": "",
  "message": "",
  "data": {
    "list": [
      {
        "id": "6a549d98d25ddc8d526c7cba",
        "q": "匹配到的文本内容...",
        "chunkIndex": 9,
        "datasetId": "6a549d95d25ddc8d526c7c34",
        "collectionId": "6a549d96d25ddc8d526c7c4e",
        "sourceId": "dataset/.../document.docx",
        "sourceName": "document.docx",
        "score": [
          {
            "type": "embedding",
            "value": 0.7823,
            "index": 0
          }
        ],
        "tokens": 1155
      }
    ],
    "duration": "0.230s",
    "searchMode": "embedding",
    "limit": 3,
    "similarity": 0,
    "usingReRank": false,
    "usingSimilarityFilter": true
  }
}
```

**data 层关键字段：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `list` | array | 匹配结果，按相似度降序 |
| `duration` | string | FastGPT 处理耗时 |
| `searchMode` | string | 实际搜索模式 |

**list[] 中关键字段：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 分片 ID |
| `q` | string | 匹配到的文本内容 |
| `sourceName` | string | 来源文件名 |
| `score` | array | 相似度得分，`type` 为 `embedding`/`fullText`/`reRank`，`value` 0–1 |

### 错误响应

| HTTP 状态码 | 场景 |
|---|---|
| `401` | 缺少 Authorization、token 格式错误、解密失败、或 token 过期 |
| `404` | 设备名不存在或未绑定知识库 |
| `500` | 服务端配置错误 |
| `4xx/5xx` | FastGPT 上游错误，透传原始状态码和响应体 |

---

## 示例

> 先用 `python scripts/generate_token.py test_07` 生成 token，替换下面的 `YOUR_AES_TOKEN`。

### 语义搜索

```bash
curl -X POST http://localhost:8000/search \
  -H "Authorization: Bearer YOUR_AES_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "编程课多少钱", "searchMode": "embedding"}'
```

### 混合检索 + 重排序

```bash
curl -X POST http://localhost:8000/search \
  -H "Authorization: Bearer YOUR_AES_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "蓝桥杯",
    "searchMode": "mixedRecall",
    "usingReRank": true,
    "limit": 10,
    "similarity": 0.5
  }'
```

### 带查询扩展

```bash
curl -X POST http://localhost:8000/search \
  -H "Authorization: Bearer YOUR_AES_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "科技特长生",
    "searchMode": "embedding",
    "datasetSearchUsingExtensionQuery": true,
    "datasetSearchExtensionModel": "gpt-4o-mini",
    "datasetSearchExtensionBg": "你是一个教育咨询助手"
  }'
```
