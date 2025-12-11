# 智能体平台

一个功能完整的智能体对话平台，支持人物卡管理、角色对话和一致性检测。人物卡采用“一个角色一个配置文件”的方式存储在统一文件夹，便于版本化和备份。

## ✨ 功能特性

### 🎭 人物卡管理
- **完整的CRUD操作**：创建、查看、更新、删除人物卡
- **灵活的属性系统**：支持自定义人物属性（年龄、性格、背景等）
- **详细的人设描述**：支持多段落、结构化的角色设定
- **文件化存储**：每个人物对应一个 JSON 配置文件，按主题分目录存放于 `characters/{theme}/`

### 💬 智能对话
- **多平台支持**：集成DeepSeek和OpenAI API
- **上下文记忆**：自动维护对话历史，保持连贯性
- **角色扮演**：基于人物设定生成符合角色的回复
- **可配置平台**：每次对话可指定使用的API平台

### 🔍 一致性检测
- **自动检测**：实时检测回复是否符合人物设定
- **评分系统**：提供0-1的一致性评分
- **详细反馈**：生成具体的改进建议
- **可配置开关**：支持启用/禁用检测功能

### 🤖 多智能体系统
- **独立智能体**：每个角色作为独立的智能体
- **并行处理**：所有智能体并行响应玩家指令
- **环境交互**：智能体根据场景状态和指令生成响应
- **状态管理**：自动更新角色状态和场景状态
- **表里分离**：区分玩家可见信息和隐藏推演信息
- **自动存档**：每次更新自动创建新存档步骤

### ❓ 提问功能
- **信息查询**：回答玩家问题，不推进游戏步骤
- **上下文理解**：基于玩家角色、人物卡、环境信息回答
- **快速响应**：只调用一次LLM，快速获取答案
- **表里区分**：只回答玩家应该知道的信息

## 🚀 快速开始

### 前置要求

- Python 3.8+
- DeepSeek 或 OpenAI API 密钥

### 安装步骤

1. **克隆或下载项目**

```bash
cd MyAgent
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **配置环境变量**

创建 `.env` 文件：

```env
# DeepSeek API（推荐）
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
DEEPSEEK_API_BASE=https://api.deepseek.com/v1

# OpenAI API（可选）
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_API_BASE=https://api.openai.com/v1

# 默认API平台
DEFAULT_API_PLATFORM=deepseek

# 一致性检测配置
CONSISTENCY_CHECK_ENABLED=true
CONSISTENCY_CHECK_API=deepseek

# 人物卡存放目录
CHARACTER_CONFIG_DIR=characters
```

## 📂 人物卡存储规范

- 目录结构：`{CHARACTER_CONFIG_DIR}/{theme}/{character_id}.json`
- 每个文件对应一个角色，包含 `id`、`name`、`description`、`attributes`、`theme`、时间戳
- 通过API创建/更新/删除会自动维护对应的JSON文件
- 推荐的属性结构示例：
  - `gender`: 性别
  - `vitals`: `{ hp, mp, stamina }`
  - `weapon`: `{ main_hand, off_hand, backup, ranged }`
  - `equipment`: `{ armor/robe, helmet/hat, boots, accessory: [] }`
  - `skills`: 技能数组
- 详细字段含义见 `CHARACTER_ATTRIBUTES.md`，系统提示会将该结构化信息一并传给LLM。

示例（冒险者小队）：

```
characters/
└── adventure_party/
    ├── 勇者.json
    ├── 魔法师.json
    ├── 牧师.json
    └── 盗贼.json
```

4. **启动服务**

```bash
python app.py
```

服务将在 `http://localhost:5000` 启动。

5. **测试运行**

```bash
python example_usage.py
```

> 📖 更详细的快速开始指南，请查看 [QUICKSTART.md](QUICKSTART.md)

## 📚 API 接口文档

### 基础信息

- **Base URL**: `http://localhost:5000`
- **Content-Type**: `application/json`
- **CORS**: 已启用，支持跨域请求
- **人物卡存储**: 每个人物对应一个 JSON 文件，默认位于 `characters/`

### 人物卡管理

#### 获取所有人物卡

```http
GET /api/characters
```

**响应示例**：

```json
[
  {
    "id": "8b3c0a0e6c9540eab08a4b1c1b4c0a12",
    "name": "小助手",
    "description": "一个友好的AI助手...",
    "attributes": {
      "personality": "友好、耐心",
      "style": "温和"
    },
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

#### 创建人物卡

```http
POST /api/characters
Content-Type: application/json
```

**请求体**：

```json
{
  "name": "角色名称",
  "description": "角色详细描述/人设\n可以多行\n支持Markdown格式",
  "attributes": {
    "age": 25,
    "personality": "开朗活泼",
    "background": "来自未来的AI助手",
    "speaking_style": "使用礼貌用语，语气温和"
  }
}
```

**响应**：返回创建的人物卡对象（包含 `id`）

**错误响应**：

```json
{
  "error": "姓名和描述是必填项"
}
```

#### 获取指定人物卡

```http
GET /api/characters/{character_id}
```

**路径参数**：
- `character_id` (integer): 人物卡ID

#### 更新人物卡

```http
PUT /api/characters/{character_id}
Content-Type: application/json
```

**请求体**（所有字段可选）：

```json
{
  "name": "新名称",
  "description": "新描述",
  "attributes": {
    "age": 26
  }
}
```

#### 删除人物卡

```http
DELETE /api/characters/{character_id}
```

**响应**：

```json
{
  "message": "人物卡已删除"
}
```

### 对话功能

#### 与角色对话

```http
POST /api/characters/{character_id}/chat
Content-Type: application/json
```

**请求体**：

```json
{
  "message": "你好，请介绍一下自己",
  "platform": "deepseek"
}
```

**参数说明**：
- `message` (string, 必填): 用户消息
- `platform` (string, 可选): API平台 (`deepseek` 或 `openai`)，默认使用配置的平台

**响应示例**：

```json
{
  "response": "你好！我是小助手，很高兴认识你...",
  "consistency_score": 0.95,
  "consistency_feedback": "回复符合角色设定，保持了友好的语气和专业的风格...",
  "conversation_id": 1
}
```

**字段说明**：
- `response`: 角色的回复内容
- `consistency_score`: 一致性评分（0-1），如果禁用检测则为 `null`
- `consistency_feedback`: 一致性检测反馈，如果禁用检测则为 `null`
- `conversation_id`: 对话记录ID

#### 获取对话历史

```http
GET /api/characters/{character_id}/conversations
```

**响应示例**：

```json
[
  {
    "id": 1,
    "character_id": "8b3c0a0e6c9540eab08a4b1c1b4c0a12",
    "user_message": "你好",
    "character_response": "你好！很高兴认识你...",
    "consistency_score": 0.95,
    "consistency_feedback": "回复符合设定...",
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### 健康检查

```http
GET /api/health
```

**响应**：

```json
{
  "status": "ok"
}
```

## 💻 使用示例

### Python 示例

```python
import requests

BASE_URL = "http://localhost:5000"

# 1. 创建人物卡
character_data = {
    "name": "小助手",
    "description": """你是一个友好、乐于助人的AI助手。
性格特点：温和、耐心、专业
说话风格：使用礼貌用语，语气友好
背景：拥有丰富的知识，喜欢解答各种问题""",
    "attributes": {
        "personality": "友好、耐心、专业",
        "style": "温和礼貌",
        "role": "AI助手"
    }
}

response = requests.post(f"{BASE_URL}/api/characters", json=character_data)
character = response.json()
character_id = character['id']
print(f"创建成功！人物卡ID: {character_id}")

# 2. 开始对话
chat_data = {
    "message": "你好，请介绍一下自己",
    "platform": "deepseek"  # 可选
}

response = requests.post(
    f"{BASE_URL}/api/characters/{character_id}/chat",
    json=chat_data
)
result = response.json()

print(f"角色回复: {result['response']}")
print(f"一致性评分: {result.get('consistency_score', 'N/A')}")
if result.get('consistency_feedback'):
    print(f"检测反馈: {result['consistency_feedback']}")

# 3. 获取对话历史
response = requests.get(f"{BASE_URL}/api/characters/{character_id}/conversations")
conversations = response.json()
print(f"\n共有 {len(conversations)} 条对话记录")
```

### cURL 示例

```bash
# 创建人物卡
curl -X POST http://localhost:5000/api/characters \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试角色",
    "description": "一个友好的AI助手",
    "attributes": {"personality": "友好"}
  }'

# 与角色对话（将 {character_id} 替换为创建返回的 id）
curl -X POST http://localhost:5000/api/characters/{character_id}/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好"
  }'

# 获取对话历史
curl http://localhost:5000/api/characters/{character_id}/conversations
```

### JavaScript 示例

```javascript
const BASE_URL = 'http://localhost:5000';

// 创建人物卡
async function createCharacter() {
  const response = await fetch(`${BASE_URL}/api/characters`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: '小助手',
      description: '一个友好的AI助手',
      attributes: { personality: '友好' }
    })
  });
  return await response.json();
}

// 与角色对话
async function chat(characterId, message) {
  const response = await fetch(`${BASE_URL}/api/characters/${characterId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, platform: 'deepseek' })
  });
  return await response.json();
}
```

## ⚙️ 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API密钥 | - | 是* |
| `DEEPSEEK_API_BASE` | DeepSeek API地址 | `https://api.deepseek.com/v1` | 否 |
| `OPENAI_API_KEY` | OpenAI API密钥 | - | 否 |
| `OPENAI_API_BASE` | OpenAI API地址 | `https://api.openai.com/v1` | 否 |
| `DEFAULT_API_PLATFORM` | 默认API平台 | `deepseek` | 否 |
| `CONSISTENCY_CHECK_ENABLED` | 启用一致性检测 | `true` | 否 |
| `CONSISTENCY_CHECK_API` | 检测使用的API平台 | `deepseek` | 否 |
| `CHARACTER_CONFIG_DIR` | 人物卡文件夹 | `characters` | 否 |
| `DATABASE_URL` | 数据库URL | `sqlite:///agent_platform.db` | 否 |

*至少需要配置一个API密钥（DeepSeek或OpenAI）

### 一致性检测

一致性检测功能会分析角色回复是否符合人物设定，包括：

- **性格一致性**：回复是否符合角色的性格特点
- **历史一致性**：是否与之前的对话保持一致
- **设定一致性**：是否有违和感或矛盾之处

检测结果包含：
- **评分**：0-1之间的数值，越高表示越符合设定
- **反馈**：详细的文字说明和改进建议

> ⚠️ **注意**：启用一致性检测会增加API调用次数，可能产生额外费用。可以通过 `CONSISTENCY_CHECK_ENABLED=false` 禁用。

## 📁 项目结构

```
MyAgent/
├── app.py                      # Flask主应用，包含所有API路由
├── config.py                   # 配置管理模块
├── models.py                   # 数据模型（Conversation）
├── requirements.txt            # Python依赖包列表
├── README.md                   # 项目文档（本文件）
├── QUICKSTART.md               # 快速开始指南
├── example_usage.py            # 使用示例脚本
├── .gitignore                  # Git忽略文件
├── .env                        # 环境变量文件（需自行创建）
├── characters/                 # 人物卡配置文件夹（每个角色一个JSON）
└── services/
    ├── __init__.py
    ├── chat_service.py         # 对话服务（支持多平台API）
    ├── consistency_checker.py  # 一致性检测服务
    └── character_store.py      # 人物卡文件存储
```

## 🔧 开发指南

### 添加新的API平台

1. 在 `services/chat_service.py` 中添加新的API调用方法
2. 在 `config.py` 中添加对应的配置项
3. 在 `chat()` 方法中添加平台判断逻辑

### 自定义一致性检测

修改 `services/consistency_checker.py` 中的 `check_consistency()` 方法，调整检测提示词和评分逻辑。

### 数据库迁移

项目使用SQLAlchemy ORM，数据库结构变更时：

```python
# 删除旧数据库
import os
os.remove('agent_platform.db')

# 重新创建（会自动执行）
python app.py
```

## 🐛 常见问题

### Q: API调用失败，提示401错误？

**A**: 检查API密钥是否正确配置，确保 `.env` 文件中的密钥有效。

### Q: 一致性检测返回null？

**A**: 检查 `CONSISTENCY_CHECK_ENABLED` 是否设置为 `true`，以及检测API的密钥是否配置。

### Q: 对话回复不符合角色设定？

**A**: 
1. 检查人物描述是否详细清晰
2. 查看一致性检测反馈，根据建议调整人物设定
3. 尝试使用不同的API平台（某些平台对角色扮演支持更好）

### Q: 如何备份数据？

**A**: 直接复制以下目录即可：
- `characters/` - 人物卡
- `save/` - 存档
- `conversations/` - 对话记录（JSON文件）

所有数据都是JSON/MD文件，易于版本控制和备份。

### Q: 系统使用数据库吗？

**A**: 不使用。所有数据都存储在JSON/MD文件中：
- 人物卡：`characters/{theme}/{character_id}.json`
- 存档：`save/{theme}/{step}/`
- 对话记录：`conversations/{character_id}.json`
- 场景设定：`SCENE.md` 文件

这样设计便于阅读、修改和版本控制。

## 📝 更新日志

### v1.0.0 (2024-01-01)
- ✨ 初始版本发布
- ✅ 人物卡管理功能
- ✅ 多平台对话支持（DeepSeek/OpenAI）
- ✅ 一致性检测功能

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/) - Web框架
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM框架
- [DeepSeek](https://www.deepseek.com/) - AI API服务
- [OpenAI](https://openai.com/) - AI API服务

## 📮 联系方式

如有问题或建议，欢迎通过Issue反馈。

---

**享受创建和管理你的AI角色吧！** 🎉
