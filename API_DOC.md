# FastGPT RAG2API 接口文档

## 概述

本服务是 FastGPT 知识库 OpenAPI 的封装层。通过 AES token 中的设备名称（`device_name`）从 MySQL 数据库中查询对应的 FastGPT `dataset_id`，然后将所有操作转发给 FastGPT。

调用方**无需知道 `dataset_id`**，服务端会自动解析。

## 鉴权

除 `/health` 外，所有接口都需要一个请求头：

| 请求头 | 必填 | 说明 |
|---|---|---|
| `Authorization` | 是 | `Bearer <AES_TOKEN>`，AES-256-CBC 加密的 token，内含 `device_name` + `timestamp` |

Token 明文为 `{"device_name": "...", "timestamp": ...}`，加密格式为 `base64url(IV[16字节] + 密文)`。服务端用 `.env` 中的 `AES_SECRET_KEY` 解密，并校验 `timestamp` 与当前时间的偏差不超过 `AES_TOKEN_TTL`（默认 300 秒）。

使用自带脚本生成 token：

```bash
python scripts/generate_token.py <device_name>
```

缺少或错误的 `Authorization` 返回 `401`，token 过期也返回 `401`。设备名无法解析返回 `404`。

## 响应格式

FastGPT 的响应原样转发，标准格式：

```json
{
  "code": 200,
  "statusText": "",
  "message": "",
  "data": { ... }
}
```

错误响应使用标准 HTTP 状态码：
- `401` - 鉴权失败
- `404` - 设备不存在或未绑定知识库
- `500` - 服务端或 FastGPT 错误

---

## 健康检查

### GET /health

返回服务状态，无需鉴权。

**响应：**
```json
{
  "status": "ok"
}
```

---

## 知识库

### GET /datasets

获取当前设备绑定的知识库详情。

**请求头：** `Authorization`

**示例：**
```bash
curl -X GET http://localhost:8000/datasets \
  -H "Authorization: Bearer YOUR_AES_TOKEN"
```

**响应示例：**
```json
{
  "code": 200,
  "data": {
    "_id": "6a549d95d25ddc8d526c7c34",
    "name": "robot_knowledge_base_100008_22",
    "type": "dataset",
    "intro": "...",
    "status": "active"
  }
}
```

## 集合（Collections）

集合的创建和删除由其他系统管理，本服务仅提供查询和更新。

### POST /collections/list

列出知识库中的集合。

**请求头：** `Authorization`

**请求体：**
```json
{
  "offset": 0,
  "pageSize": 10,
  "parentId": null,
  "searchText": ""
}
```

**响应示例：**
```json
{
  "code": 200,
  "data": {
    "total": 1,
    "list": [
      {
        "_id": "6a549d96d25ddc8d526c7c4e",
        "name": "document.docx",
        "type": "file",
        "dataAmount": 11
      }
    ]
  }
}
```

### GET /collections/{collection_id}

获取指定集合的详情。

| 参数 | 说明 |
|---|---|
| `collection_id` | 集合 ID |

### POST /collections/update

更新集合信息。

**请求体：**
```json
{
  "id": "collection_id",
  "name": "新名称",
  "tags": ["tag1"],
  "forbid": false
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 集合 ID（或使用 `externalFileId`） |
| `externalFileId` | string | 外部文件 ID（替代 `id`） |
| `parentId` | string | 移动到其他文件夹 |
| `name` | string | 新名称 |
| `tags` | string[] | 新标签 |
| `forbid` | bool | 禁用此集合 |
| `createTime` | string | 自定义创建时间 |

---

## 数据（Data）

对集合中的单条数据进行操作。

### POST /collections/{collection_id}/data/push

向集合推送数据（问答对或文本分段）。

| 参数 | 说明 |
|---|---|
| `collection_id` | 集合 ID |

**请求体：**
```json
{
  "collectionId": "自动填充",
  "trainingType": "chunk",
  "prompt": "",
  "data": [
    {
      "q": "什么是 FastGPT？",
      "a": "FastGPT 是一个知识库问答系统。",
      "indexes": []
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `collectionId` | string | 自动从 URL 路径填充 |
| `trainingType` | string | `chunk` 或 `qa` |
| `prompt` | string | QA 模式提示词 |
| `data` | PushDataItem[] | 数据数组 |
| `data[].q` | string | 问题 / 主要文本 |
| `data[].a` | string | 答案 / 补充文本 |
| `data[].indexes` | IndexItem[] | 自定义索引 |

### POST /collections/{collection_id}/data/list

列出集合中的数据。

**请求体：**
```json
{
  "offset": 0,
  "pageSize": 10,
  "searchText": ""
}
```

**响应示例：**
```json
{
  "code": 200,
  "data": {
    "total": 11,
    "list": [
      {
        "_id": "6a549d98d25ddc8d526c7cd7",
        "chunkIndex": 0,
        "q": "文本内容...",
        "a": ""
      }
    ]
  }
}
```

### GET /collections/{collection_id}/data/{data_id}

获取指定数据的详情。

### PUT /collections/{collection_id}/data/update

更新数据。

**请求体：**
```json
{
  "dataId": "6a549d98d25ddc8d526c7cd7",
  "q": "更新后的问题",
  "a": "更新后的答案",
  "indexes": []
}
```

### DELETE /collections/{collection_id}/data/{data_id}

删除指定数据。

---

## 搜索

### POST /search

在 token 中 `device_name` 解析出的知识库中搜索。

**请求体：**
```json
{
  "text": "搜索内容",
  "limit": 5000,
  "similarity": 0,
  "searchMode": "embedding",
  "usingReRank": false,
  "datasetSearchUsingExtensionQuery": false,
  "datasetSearchExtensionModel": "gpt-4o-mini",
  "datasetSearchExtensionBg": ""
}
```

**参数说明：**

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `text` | string | （必填） | 搜索文本 |
| `limit` | int | `5000` | 最大返回条数 |
| `similarity` | float | `0` | 最小相似度（0-1） |
| `searchMode` | string | `"embedding"` | 搜索模式：`embedding` / `fullTextRecall` / `mixedRecall` |
| `usingReRank` | bool | `false` | 是否使用重排序模型 |
| `datasetSearchUsingExtensionQuery` | bool | `false` | 是否使用查询扩展 |
| `datasetSearchExtensionModel` | string | `"gpt-4o-mini"` | 扩展模型 |
| `datasetSearchExtensionBg` | string | `""` | 扩展背景 |

**搜索模式对比：**

| 模式 | 速度 | 召回率 | 说明 |
|---|---|---|---|
| `embedding` | ~230ms | 高 | 向量相似度搜索，语义匹配效果最好 |
| `fullTextRecall` | ~100ms | 低 | 全文检索，速度快但依赖分词 |
| `mixedRecall` | ~180ms | 中 | 向量 + 全文混合检索 |

**示例：**
```bash
curl -X POST http://localhost:8000/search \
  -H "Authorization: Bearer YOUR_AES_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "编程课多少钱", "searchMode": "embedding"}'
```

**响应示例：**
```json
{
  "code": 200,
  "data": {
    "list": [
      {
        "id": "6a549d98d25ddc8d526c7cba",
        "q": "匹配到的文本内容...",
        "chunkIndex": 9,
        "datasetId": "6a549d95d25ddc8d526c7c34",
        "collectionId": "6a549d96d25ddc8d526c7c4e",
        "score": [
          {
            "type": "embedding",
            "value": 0.7857,
            "index": 0
          }
        ],
        "tokens": 1155
      }
    ],
    "duration": "0.221s",
    "searchMode": "embedding"
  }
}
```

---

## 接口总表

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /health | 健康检查（无需鉴权） |
| GET | /datasets | 获取知识库详情 |
| POST | /collections/list | 列出集合 |
| GET | /collections/{collection_id} | 获取集合详情 |
| POST | /collections/update | 更新集合 |
| POST | /collections/{collection_id}/data/push | 推送数据 |
| POST | /collections/{collection_id}/data/list | 列出数据 |
| GET | /collections/{collection_id}/data/{data_id} | 获取数据详情 |
| PUT | /collections/{collection_id}/data/update | 更新数据 |
| DELETE | /collections/{collection_id}/data/{data_id} | 删除数据 |
| POST | /search | 搜索知识库 |
