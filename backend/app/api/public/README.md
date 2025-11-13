# Public Chat API Documentation

> **For External Developers**: This API allows you to integrate intelligent local event discovery into your applications. The API provides conversational event recommendations powered by AI.

## 📑 Table of Contents

- [Quick Start](#-quick-start)
- [Overview](#-概述--overview)
- [Authentication](#-认证--authentication)
- [Rate Limiting](#-速率限制--rate-limiting)
- [API Endpoints](#-api端点--api-endpoints)
- [Code Examples](#代码示例)
- [Best Practices](#最佳实践)
- [Configuration](#环境变量配置)
- [Additional Resources](#-更多资源--additional-resources)
- [Production Deployment](#公网访问配置)

## 🚀 Quick Start

**Get started in 3 steps:**

1. **Get a Firebase Token** - Authenticate with Firebase Auth
2. **Make your first request** - Send a POST request to `/api/public/chat`
3. **Handle the response** - Receive AI-powered event recommendations

**Example (cURL):**
```bash
curl -X POST https://lily.locomoco.top/api/public/chat \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Find music concerts in New York this weekend"}'
```

> 📝 **Note**: Production domain: `https://lily.locomoco.top`. For development, use `http://localhost:8000`.

### ✨ What You Get

This API provides:
- **🤖 AI-Powered Search**: Natural language understanding for event queries
- **📍 Location Intelligence**: Automatic location extraction and event matching
- **💬 Conversational Context**: Maintains conversation history for follow-up queries
- **🎯 Smart Recommendations**: Relevance-scored event recommendations
- **⚡ Cached Results**: Fast responses with intelligent caching
- **🔒 Secure**: Firebase authentication and rate limiting

## 概述 / Overview

Public Chat API 是一个RESTful API，提供智能本地生活助手服务。该API使用Firebase认证和速率限制来保护服务。

**English**: Public Chat API is a RESTful API that provides intelligent local life assistant services. The API uses Firebase authentication and rate limiting to protect the service.

### 环境URL / Environment URLs

- **开发环境 / Development**: `http://localhost:8000`
- **生产环境 / Production**: `https://lily.locomoco.top`
- **API Prefix**: `/api/public`

**完整API端点 / Full API Endpoints**:
- 开发 / Development: `http://localhost:8000/api/public/chat`
- 生产 / Production: `https://lily.locomoco.top/api/public/chat`

> ✅ **生产环境已配置 / Production Configured**: 生产环境URL为 `https://lily.locomoco.top`
> 
> **English**: Production URL is configured as `https://lily.locomoco.top`

## 🔑 认证 / Authentication

所有API请求都需要Firebase认证令牌。  
**English**: All API requests require Firebase authentication tokens.

### 获取Firebase Token / Getting Firebase Token

1. 在客户端使用Firebase Auth SDK登录 / Use Firebase Auth SDK in your client to sign in
2. 获取ID Token: `await user.getIdToken()` / Get ID Token: `await user.getIdToken()`
3. 在请求头中包含token: `Authorization: Bearer <token>` / Include token in request header: `Authorization: Bearer <token>`

**JavaScript Example:**
```javascript
import { getAuth, signInAnonymously } from 'firebase/auth';

const auth = getAuth();
const userCredential = await signInAnonymously(auth);
const token = await userCredential.user.getIdToken();
```

### 请求头格式 / Request Headers

```
Authorization: Bearer <firebase_token>
Content-Type: application/json
```

> 💡 **Tip**: Firebase tokens typically expire after 1 hour. Implement token refresh logic in your application.

## ⚡ 速率限制 / Rate Limiting

API实施固定窗口计数器速率限制。  
**English**: The API implements fixed window counter rate limiting.

- **限制 / Limit**: 10 请求/60秒 (默认，可通过环境变量配置) / 10 requests per 60 seconds (default, configurable via environment variables)
- **配置变量 / Configuration Variables**: 
  - `API_RATE_LIMIT_MAX`: 最大请求数 (默认: 10) / Maximum requests (default: 10)
  - `API_RATE_LIMIT_WINDOW`: 时间窗口秒数 (默认: 60) / Time window in seconds (default: 60)

### 速率限制响应头

每个响应都包含以下头部：

- `X-RateLimit-Limit`: 允许的最大请求数
- `X-RateLimit-Remaining`: 当前窗口剩余请求数
- `X-RateLimit-Reset`: 窗口重置时间戳（Unix时间戳）

### 速率限制错误

当超过速率限制时，API返回：

- **状态码**: `429 Too Many Requests`
- **响应体**:
```json
{
  "detail": "Rate limit exceeded. Maximum 10 requests per 60 seconds. Try again after 1234567890."
}
```

## 📡 API端点 / API Endpoints

### POST /api/public/chat

发送聊天消息并获取事件推荐。  
**English**: Send a chat message and receive event recommendations.

**What this endpoint does:**
- Accepts natural language queries (e.g., "Find jazz concerts this weekend")
- Extracts user preferences (location, date, event type)
- Searches for matching events using AI-powered semantic search
- Returns formatted recommendations with event details
- Maintains conversation context for follow-up queries

#### 请求

**Headers:**
```
Authorization: Bearer <firebase_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "Find music concerts in New York this weekend",
  "conversation_history": [],
  "llm_provider": "openai",
  "is_initial_response": false,
  "conversation_id": null
}
```

**参数说明:**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `message` | string | 是 | 用户的消息/查询 |
| `conversation_history` | array | 否 | 之前的对话历史（默认: []） |
| `llm_provider` | string | 否 | LLM提供商（默认: "openai"） |
| `is_initial_response` | boolean | 否 | 是否为首次消息（默认: false） |
| `conversation_id` | string\|null | 否 | 继续现有对话的ID（默认: null） |

**注意**: `user_id` 不需要在请求中提供，它从Firebase token中自动提取。

#### 响应

**成功响应 (200 OK):**

```json
{
  "message": "🎉 Found 5 events in New York that match your search! Check out the recommendations below ↓",
  "recommendations": [
    {
      "type": "event",
      "data": {
        "title": "Jazz Night at Blue Note",
        "venue_name": "Blue Note Jazz Club",
        "venue_city": "New York",
        "start_datetime": "2024-01-15T20:00:00",
        "end_datetime": "2024-01-15T23:00:00",
        "is_free": false,
        "ticket_min_price": "$25",
        "ticket_max_price": "$50",
        "image_url": "https://...",
        "event_url": "https://...",
        "categories": ["Music", "Jazz"],
        "source": "cached"
      },
      "relevance_score": 0.95,
      "explanation": "Event in New York: Jazz Night at Blue Note"
    }
  ],
  "llm_provider_used": "openai",
  "cache_used": true,
  "cache_age_hours": 2.5,
  "extracted_preferences": {
    "location": "new york",
    "date": "this weekend",
    "time": "none",
    "event_type": "music"
  },
  "extraction_summary": "📍 new york • 📅 this weekend • 🎭 music",
  "usage_stats": null,
  "trial_exceeded": false,
  "conversation_id": "abc-123-def-456"
}
```

**响应字段说明 / Response Fields:**

| 字段 / Field | 类型 / Type | 说明 / Description |
|------|------|------|
| `message` | string | AI助手的回复消息 / AI assistant's response message |
| `recommendations` | array | 事件推荐列表 / List of event recommendations |
| `llm_provider_used` | string | 使用的LLM提供商 / LLM provider used (e.g., "openai", "anthropic") |
| `cache_used` | boolean | 是否使用了缓存 / Whether cache was used |
| `cache_age_hours` | number\|null | 缓存年龄（小时） / Cache age in hours |
| `extracted_preferences` | object\|null | 提取的用户偏好 / Extracted user preferences (see below) |
| `extraction_summary` | string\|null | 偏好摘要（格式化） / Formatted preference summary |
| `usage_stats` | object\|null | 使用统计（匿名用户） / Usage statistics (for anonymous users) |
| `trial_exceeded` | boolean | 是否超过试用限制 / Whether trial limit was exceeded |
| `conversation_id` | string | 对话ID（用于继续对话） / Conversation ID (for continuing conversations) |

#### 推荐项结构 / Recommendation Item Structure

每个推荐项包含以下字段 / Each recommendation item contains:

| 字段 / Field | 类型 / Type | 说明 / Description |
|------|------|------|
| `type` | string | 推荐类型，当前为 "event" / Recommendation type, currently "event" |
| `data` | object | 事件数据对象 / Event data object (see below) |
| `relevance_score` | number | 相关性分数 (0.0-1.0) / Relevance score (0.0-1.0) |
| `explanation` | string | 推荐原因说明 / Explanation for the recommendation |

#### 事件数据对象 / Event Data Object

`recommendations[].data` 对象包含以下字段 / The `data` object contains:

| 字段 / Field | 类型 / Type | 必需 / Required | 说明 / Description |
|------|------|------|------|
| `event_id` | string | 否 | 事件唯一标识符 / Unique event identifier |
| `title` | string | 是 | 事件标题 / Event title |
| `description` | string | 是 | 事件描述 / Event description |
| `venue_name` | string | 是 | 场馆名称 / Venue name |
| `venue_city` | string | 是 | 场馆所在城市 / Venue city |
| `venue_country` | string | 否 | 场馆所在国家 / Venue country |
| `start_datetime` | string | 是 | 开始时间 (ISO 8601格式) / Start datetime (ISO 8601 format) |
| `end_datetime` | string | 否 | 结束时间 (ISO 8601格式) / End datetime (ISO 8601 format) |
| `timezone` | string | 否 | 时区 / Timezone |
| `organizer_name` | string | 否 | 组织者名称 / Organizer name |
| `organizer_id` | string | 否 | 组织者ID / Organizer ID |
| `is_free` | boolean | 是 | 是否免费 / Whether event is free |
| `ticket_min_price` | string | 否 | 最低票价 / Minimum ticket price |
| `ticket_max_price` | string | 否 | 最高票价 / Maximum ticket price |
| `categories` | array | 否 | 事件分类数组 / Array of event categories |
| `image_url` | string | 否 | 事件图片URL / Event image URL |
| `event_url` | string | 否 | 事件详情页URL / Event detail page URL |
| `source` | string | 是 | 数据来源 ("cached" 或 "realtime") / Data source ("cached" or "realtime") |
| `latitude` | number | 否 | 场馆纬度 / Venue latitude |
| `longitude` | number | 否 | 场馆经度 / Venue longitude |
| `attendee_count` | number | 否 | 参加人数 / Number of attendees |
| `rating` | number | 否 | 评分 / Rating |

#### 用户偏好对象 / User Preferences Object

`extracted_preferences` 对象包含以下字段 / The `extracted_preferences` object contains:

| 字段 / Field | 类型 / Type | 说明 / Description |
|------|------|------|
| `location` | string\|null | 提取的位置信息 / Extracted location (e.g., "new york", "none") |
| `date` | string\|null | 提取的日期信息 / Extracted date (e.g., "this weekend", "none") |
| `time` | string\|null | 提取的时间信息 / Extracted time (e.g., "evening", "none") |
| `event_type` | string\|null | 提取的事件类型 / Extracted event type (e.g., "music", "none") |

**注意 / Note**: 如果某个字段未提取到，值为 `"none"` 或 `null` / If a field is not extracted, the value is `"none"` or `null`.

#### 使用统计对象 / Usage Statistics Object

`usage_stats` 对象（仅匿名用户）包含以下字段 / The `usage_stats` object (anonymous users only) contains:

| 字段 / Field | 类型 / Type | 说明 / Description |
|------|------|------|
| `total_interactions` | number | 总交互次数 / Total number of interactions |
| `remaining_interactions` | number | 剩余交互次数 / Remaining interactions |
| `trial_limit` | number | 试用限制次数 / Trial limit count |

#### 错误响应

**401 Unauthorized** - 无效或缺失的认证token:
```json
{
  "detail": "Authorization header required"
}
```

**403 Forbidden** - 无权访问该对话:
```json
{
  "detail": "You do not have permission to access this conversation"
}
```

**404 Not Found** - 对话不存在:
```json
{
  "detail": "Conversation not found"
}
```

**429 Too Many Requests** - 超过速率限制:
```json
{
  "detail": "Rate limit exceeded. Maximum 10 requests per 60 seconds. Try again after 1234567890."
}
```

**500 Internal Server Error** - 服务器错误:
```json
{
  "detail": "Error processing chat request: <error message>"
}
```

## 代码示例

### Python

```python
import requests
import os

# Configure API base URL
# Development: http://localhost:8000
# Production: https://lily.locomoco.top
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
FIREBASE_TOKEN = "your_firebase_token_here"

headers = {
    "Authorization": f"Bearer {FIREBASE_TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "message": "Find music concerts in New York this weekend",
    "conversation_history": [],
    "llm_provider": "openai",
    "is_initial_response": True,
    "conversation_id": None
}

response = requests.post(
    f"{API_BASE_URL}/api/public/chat",
    json=payload,
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    print(f"Response: {data['message']}")
    print(f"Found {len(data['recommendations'])} recommendations")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

完整示例请参考: [`../examples/python_example.py`](../examples/python_example.py)

### JavaScript/Node.js

```javascript
const axios = require('axios');

// Configure API base URL
// Development: http://localhost:8000
// Production: https://lily.locomoco.top
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';
const FIREBASE_TOKEN = 'your_firebase_token_here';

const headers = {
  'Authorization': `Bearer ${FIREBASE_TOKEN}`,
  'Content-Type': 'application/json'
};

const payload = {
  message: 'Find music concerts in New York this weekend',
  conversation_history: [],
  llm_provider: 'openai',
  is_initial_response: true,
  conversation_id: null
};

axios.post(`${API_BASE_URL}/api/public/chat`, payload, { headers })
  .then(response => {
    console.log(`Response: ${response.data.message}`);
    console.log(`Found ${response.data.recommendations.length} recommendations`);
  })
  .catch(error => {
    console.error(`Error: ${error.response?.status} - ${error.response?.data?.detail}`);
  });
```

完整示例请参考: [`../examples/javascript_example.js`](../examples/javascript_example.js)

### cURL

**开发环境**:
```bash
curl -X POST http://localhost:8000/api/public/chat \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Find music concerts in New York this weekend",
    "conversation_history": [],
    "llm_provider": "openai",
    "is_initial_response": true,
    "conversation_id": null
  }'
```

**生产环境 / Production**:
```bash
curl -X POST https://lily.locomoco.top/api/public/chat \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Find music concerts in New York this weekend",
    "conversation_history": [],
    "llm_provider": "openai",
    "is_initial_response": true,
    "conversation_id": null
  }'
```

完整示例请参考: [`../examples/curl_examples.sh`](../examples/curl_examples.sh)

## 最佳实践

### 1. 错误处理

始终检查HTTP状态码并处理错误：

```python
try:
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        # 重新获取token
        pass
    elif e.response.status_code == 429:
        # 等待后重试
        reset_time = int(e.response.headers.get('X-RateLimit-Reset', 0))
        wait_seconds = reset_time - int(time.time())
        time.sleep(wait_seconds)
        # 重试请求
    else:
        # 其他错误
        pass
```

### 2. 速率限制处理

- 监控 `X-RateLimit-Remaining` 头部
- 当接近限制时，减少请求频率
- 收到429错误时，等待到 `X-RateLimit-Reset` 时间后再重试

### 3. 对话管理

- 保存 `conversation_id` 以继续对话
- 在后续请求中使用相同的 `conversation_id`
- 不要跨用户共享 `conversation_id`

### 4. Token管理

- Firebase token通常1小时过期
- 实现token刷新机制
- 不要在客户端代码中硬编码token

### 5. 重试策略

对于临时错误（429, 500），实施指数退避重试：

```python
import time
import random

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [429, 500, 502, 503]:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
                continue
            raise
    raise Exception("Max retries exceeded")
```

## 环境变量配置

服务器端可以通过以下环境变量配置API：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `API_RATE_LIMIT_MAX` | 速率限制最大请求数 | 10 |
| `API_RATE_LIMIT_WINDOW` | 速率限制时间窗口（秒） | 60 |

## 📚 更多资源 / Additional Resources

**示例代码 / Example Code**: 
- Python: [`../examples/python_example.py`](../examples/python_example.py)
- JavaScript: [`../examples/javascript_example.js`](../examples/javascript_example.js)
- cURL: [`../examples/curl_examples.sh`](../examples/curl_examples.sh)

**项目文档 / Project Documentation**: 项目根目录的README.md / README.md in project root

## 💬 支持 / Support

如有问题或需要帮助，请参考上述资源。  
**English**: For questions or help, please refer to the resources above.

## 🌐 公网访问配置 / Production Deployment

### 部署到生产环境 / Deploying to Production

API已配置为支持公网访问。部署时需要：  
**English**: The API is configured for public access. When deploying:

1. **设置域名环境变量 / Set Domain Environment Variable**:
   ```bash
   export DOMAIN_NAME=lily.locomoco.top
   ```
   > ✅ Production domain: `lily.locomoco.top`

2. **配置CORS / Configure CORS**: API会自动根据 `DOMAIN_NAME` 配置CORS，允许来自该域名的请求  
   **English**: API automatically configures CORS based on `DOMAIN_NAME` to allow requests from that domain

3. **使用HTTPS / Use HTTPS**: 生产环境建议使用HTTPS，通过Nginx反向代理配置SSL证书  
   **English**: Production should use HTTPS via Nginx reverse proxy with SSL certificate

4. **防火墙配置 / Firewall Configuration**: 确保服务器开放必要端口（80, 443, 8000）  
   **English**: Ensure server opens necessary ports (80, 443, 8000)

### 访问示例 / Access Example

**生产环境调用 / Production Call**:
```bash
curl -X POST https://lily.locomoco.top/api/public/chat \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Find events in New York"}'
```

### 环境变量 / Environment Variables

服务器端可通过以下环境变量配置：  
**English**: Server-side configuration via environment variables:

| 变量 / Variable | 说明 / Description | 默认值 / Default | 必需 / Required |
|------|------|--------|------|
| `DOMAIN_NAME` | 生产域名 / Production domain | `lily.locomoco.top` | 是（生产环境）/ Yes (production) |
| `API_RATE_LIMIT_MAX` | 速率限制最大请求数 / Max requests per window | 10 | 否 / No |
| `API_RATE_LIMIT_WINDOW` | 速率限制时间窗口（秒）/ Time window (seconds) | 60 | 否 / No |

## 📋 版本信息 / Version Information

- **API版本 / API Version**: 1.0.0
- **最后更新 / Last Updated**: 2024-01-15
- **公网访问 / Public Access**: ✅ 已支持 / Supported
- **认证方式 / Authentication**: Firebase Auth
- **速率限制 / Rate Limiting**: ✅ 已实施 / Implemented

---

> 💡 **For API Consumers**: This documentation is designed for external developers integrating the Local Life Assistant API into their applications. Production API is available at `https://lily.locomoco.top`.

