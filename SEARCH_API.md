# POST /search — 知识库搜索

## 概述

在 `X-Device-Name` 解析出的 FastGPT 知识库中执行语义/全文/混合检索。调用方无需关心 `datasetId`，服务端自动根据设备名查库并注入。

---

## 请求

### 方法 & 路径

```
POST /search
```

### 请求头

| 请求头 | 必填 | 说明 |
|---|---|---|
| `Authorization` | 是 | `Bearer <API_KEY>`，与 `.env` 中 `API_KEY` 比对 |
| `X-Device-Name` | 是 | 设备名称，用于在 MySQL 中查 `ya_setting_robot.device_name` → `ya_member_robot_attributes.dataset_id` |
| `Content-Type` | 否 | `application/json`（默认） |

### 请求体（JSON）

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

#### 参数详解

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `text` | string | **是** | — | 搜索文本。FastGPT 会将其向量化后检索 |
| `limit` | int | 否 | `5000` | 最大返回条数。FastGPT 内部有上限 |
| `similarity` | float | 否 | `0` | 最小相似度阈值（0–1）。`0` 表示不过滤，`0.8` 表示只返回得分 ≥ 0.8 的结果。实际生效取决于 FastGPT 是否开启 `usingSimilarityFilter` |
| `searchMode` | string | 否 | `"embedding"` | 搜索模式，见下表 |
| `usingReRank` | bool | 否 | `false` | 是否启用重排序（Reranker）。开启后 FastGPT 会用重排序模型对召回结果二次打分，精度更高但延迟增加 |
| `datasetSearchUsingExtensionQuery` | bool | 否 | `false` | 是否使用 LLM 查询扩展。开启后 FastGPT 会用下方指定的模型改写/扩展用户的搜索词，提升召回率 |
| `datasetSearchExtensionModel` | string | 否 | `"gpt-4o-mini"` | 查询扩展使用的 LLM 模型 ID。仅在 `datasetSearchUsingExtensionQuery: true` 时生效 |
| `datasetSearchExtensionBg` | string | 否 | `""` | 查询扩展时的背景信息/提示词，可指导 LLM 生成更精准的扩展查询 |

#### 搜索模式

| 模式 | 说明 | 典型延迟 | 适用场景 |
|---|---|---|---|
| `embedding` | 向量语义检索。文本 → embedding → 向量相似度匹配 | ~230ms | 语义理解需求，如自然语言问答 |
| `fullTextRecall` | 全文关键词检索。依赖 Elasticsearch/MySQL 分词索引 | ~100ms | 精确关键词匹配，如文档标题搜索 |
| `mixedRecall` | 向量 + 全文混合检索。同时召回两路结果并融合排序 | ~180ms | 兼顾语义和关键词，综合效果最佳 |

---

## 服务端处理流程

```
Client
  │  POST /search
  │  Headers: Authorization + X-Device-Name
  │  Body: { text, searchMode, limit, ... }
  ▼
┌─────────────────────────────┐
│ 1. request_id_middleware    │  附加 X-Request-ID，记录起始时间
└─────────────────────────────┘
  ▼
┌─────────────────────────────┐
│ 2. verify_api_key           │  secrets.compare_digest 比对 Authorization
│    失败 → 401               │  与 .env 中 API_KEY 比对
└─────────────────────────────┘
  ▼
┌─────────────────────────────┐
│ 3. get_device_dataset_id    │  查 MySQL:
│    - 查内存缓存 (TTL 5min)   │    ya_setting_robot.device_name = X-Device-Name
│    - 缓存未命中 → 查 DB      │    JOIN ya_member_robot_attributes ON robot_id
│    - 取最新记录 (id DESC)    │    WHERE is_delete = 0
│    失败 → 404               │  → 返回 dataset_id
└─────────────────────────────┘
  ▼
┌─────────────────────────────┐
│ 4. 组装 payload              │  body.model_dump() + datasetId
│    POST /api/core/dataset/   │  → FastGPT OpenAPI
│    searchTest                │
└─────────────────────────────┘
  ▼
┌─────────────────────────────┐
│ 5. FastGPT 返回 → 原样透传   │  非 2xx → HTTPException(同状态码)
└─────────────────────────────┘
  ▼
Client  ←  X-Request-ID + 响应体 + 耗时日志
```

---

## 响应

### 成功响应 (200)

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

#### 响应字段

**顶层**

| 字段 | 类型 | 说明 |
|---|---|---|
| `code` | int | 状态码，FastGPT 约定 `200` 为成功 |
| `statusText` | string | 状态文本 |
| `message` | string | 错误消息（成功时为空） |
| `data` | object | 搜索结果 |

**data 层**

| 字段 | 类型 | 说明 |
|---|---|---|
| `list` | array | 匹配结果列表，按相似度降序 |
| `duration` | string | FastGPT 内部处理耗时（不含网络传输） |
| `searchMode` | string | 实际使用的搜索模式 |
| `limit` | int | 请求的最大返回条数 |
| `similarity` | float | 请求的相似度阈值 |
| `usingReRank` | bool | 是否启用重排序 |
| `usingSimilarityFilter` | bool | FastGPT 是否实际应用了相似度过滤 |

**list[] 单条结果**

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 数据分片 ID（MongoDB ObjectId） |
| `q` | string | 匹配到的文本内容（问答模式为问题+答案） |
| `chunkIndex` | int | 分段序号（原始文档中的第几段） |
| `datasetId` | string | 所属知识库 ID |
| `collectionId` | string | 所属集合 ID |
| `sourceId` | string | 源文件路径 |
| `sourceName` | string | 源文件名 |
| `score[]` | array | 相似度得分数组 |
| `score[].type` | string | 得分类型：`embedding` / `fullText` / `reRank` |
| `score[].value` | float | 得分值（0–1），越高越相关 |
| `score[].index` | int | 得分序号（多路召回时标识来源） |
| `tokens` | int | 该分片的 token 数 |

### 错误响应

| HTTP 状态码 | 场景 | 响应体示例 |
|---|---|---|
| `401` | 缺少 Authorization 头 | `{"detail": "Missing Authorization header"}` |
| `401` | API Key 不匹配 | `{"detail": "Invalid API key"}` |
| `404` | 设备名在数据库中不存在 | `{"detail": "No active dataset found for this device name"}` |
| `404` | 设备存在但未绑定 dataset_id | `{"detail": "Device has no dataset_id bound"}` |
| `500` | 服务端 API_KEY 未配置 | `{"detail": "API_KEY not configured on server"}` |
| `4xx/5xx` | FastGPT 上游返回错误 | 透传 FastGPT 的状态码和响应体，如 `{"detail": {...}}` |

---

## curl 示例

### 基础语义搜索

```bash
curl -X POST http://localhost:8000/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "X-Device-Name: test_07" \
  -H "Content-Type: application/json" \
  -d '{"text": "编程课多少钱", "searchMode": "embedding"}'
```

### 全文检索 + 重排序

```bash
curl -X POST http://localhost:8000/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "X-Device-Name: test_07" \
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
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "X-Device-Name: test_07" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "科技特长生",
    "searchMode": "embedding",
    "datasetSearchUsingExtensionQuery": true,
    "datasetSearchExtensionModel": "gpt-4o-mini",
    "datasetSearchExtensionBg": "你是一个教育咨询助手，帮助家长了解编程课程"
  }'
```

### 带 Request ID 的调试请求

```bash
curl -X POST http://localhost:8000/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "X-Device-Name: test_07" \
  -H "X-Request-ID: my-trace-001" \
  -H "Content-Type: application/json" \
  -d '{"text": "测试", "limit": 3}'
```

服务端日志输出示例：

```
2026-07-14 14:00:27 | INFO    | fastgptrag2api.access | my-trace-001 | POST /search | 200 | 234ms | device=test_07
```

---

## 性能与缓存

- **设备 → dataset_id 映射缓存**：进程内内存，TTL 5 分钟。同一个设备首次请求查 DB（~5-20ms），后续命中缓存（<1ms）
- **FastGPT 转发超时**：120 秒（硬编码在 `fastgpt_client.py`）
- **searchMode 延迟参考**：`embedding` ~230ms / `mixedRecall` ~180ms / `fullTextRecall` ~100ms（不含网络 RTT）
- **并发**：数据库连接池 `pool_size=20, max_overflow=10`，httpx 客户端单例共享
