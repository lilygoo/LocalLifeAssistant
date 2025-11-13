# Public Chat API Documentation

## 概述

Public Chat API 是一个RESTful API，提供智能本地生活助手服务。该API使用Firebase认证和速率限制来保护服务。

### 环境URL

- **开发环境**: `http://localhost:8000`
- **生产环境**: `https://your-domain.com` (请替换为实际域名)
- **API Prefix**: `/api/public`

**完整API端点**:
- 开发: `http://localhost:8000/api/public/chat`
- 生产: `https://your-domain.com/api/public/chat`

> **注意**: 生产环境URL需要通过环境变量 `DOMAIN_NAME` 配置。请将文档中的 `your-domain.com` 替换为您的实际域名。

## 认证

所有API请求都需要Firebase认证令牌。

### 获取Firebase Token

1. 在客户端使用Firebase Auth SDK登录
2. 获取ID Token: `await user.getIdToken()`
3. 在请求头中包含token: `Authorization: Bearer <token>`

### 请求头格式

```
Authorization: Bearer <firebase_token>
Content-Type: application/json
```

## 速率限制

API实施固定窗口计数器速率限制：

- **限制**: 10 请求/60秒 (默认，可通过环境变量配置)
- **配置变量**: 
  - `API_RATE_LIMIT_MAX`: 最大请求数 (默认: 10)
  - `API_RATE_LIMIT_WINDOW`: 时间窗口秒数 (默认: 60)

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

## API端点

### POST /api/public/chat

发送聊天消息并获取事件推荐。

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

**响应字段说明:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `message` | string | AI助手的回复消息 |
| `recommendations` | array | 事件推荐列表 |
| `llm_provider_used` | string | 使用的LLM提供商 |
| `cache_used` | boolean | 是否使用了缓存 |
| `cache_age_hours` | number\|null | 缓存年龄（小时） |
| `extracted_preferences` | object\|null | 提取的用户偏好 |
| `extraction_summary` | string\|null | 偏好摘要（格式化） |
| `usage_stats` | object\|null | 使用统计（匿名用户） |
| `trial_exceeded` | boolean | 是否超过试用限制 |
| `conversation_id` | string | 对话ID（用于继续对话） |

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
# Production: https://your-domain.com (replace with your actual domain)
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
// Production: https://your-domain.com (replace with your actual domain)
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

**生产环境** (替换为您的实际域名):
```bash
curl -X POST https://your-domain.com/api/public/chat \
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

## 支持

如有问题或需要帮助，请参考：
- 示例代码: [`../examples/`](../examples/)
- 项目文档: 项目根目录的README.md

## 公网访问配置

### 部署到生产环境

API已配置为支持公网访问。部署时需要：

1. **设置域名环境变量**:
   ```bash
   export DOMAIN_NAME=your-domain.com
   ```

2. **配置CORS**: API会自动根据 `DOMAIN_NAME` 配置CORS，允许来自该域名的请求

3. **使用HTTPS**: 生产环境建议使用HTTPS，通过Nginx反向代理配置SSL证书

4. **防火墙配置**: 确保服务器开放必要端口（80, 443, 8000）

### 访问示例

**生产环境调用**:
```bash
# 替换为您的实际域名
curl -X POST https://your-domain.com/api/public/chat \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Find events in New York"}'
```

### 环境变量

服务器端可通过以下环境变量配置：

| 变量 | 说明 | 默认值 | 必需 |
|------|------|--------|------|
| `DOMAIN_NAME` | 生产域名 | - | 是（生产环境） |
| `API_RATE_LIMIT_MAX` | 速率限制最大请求数 | 10 | 否 |
| `API_RATE_LIMIT_WINDOW` | 速率限制时间窗口（秒） | 60 | 否 |

## 版本信息

- API版本: 1.0.0
- 最后更新: 2024-01-15
- 公网访问: ✅ 已支持

