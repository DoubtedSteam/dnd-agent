# 智能体平台

一个专为**跑团（TRPG）**设计的智能体对话平台，支持多智能体系统、剧本管理、角色对话和一致性检测。采用文件化存储（JSON/MD），便于版本控制和备份。

> 🎲 **主要用途**：本平台专为跑团游戏设计，支持玩家作为GM（游戏主持人）或玩家角色，与多个AI智能体角色互动，推进剧情发展。每个角色都是独立的智能体，会根据场景状态和玩家指令做出响应，营造沉浸式的跑团体验。

## ✨ 功能特性

### 🎭 人物卡管理
- **完整的CRUD操作**：创建、查看、更新、删除人物卡
- **灵活的属性系统**：支持自定义人物属性（年龄、性格、背景等）
- **详细的人设描述**：支持多段落、结构化的角色设定
- **文件化存储**：每个人物对应一个 JSON 配置文件，按主题分目录存放于 `characters/{theme}/`

### 💬 智能对话
- **多平台支持**：集成DeepSeek和OpenAI API
- **角色扮演**：基于人物设定生成符合角色的回复
- **可配置平台**：每次对话可指定使用的API平台
- **指令执行**：玩家的指令必须执行，但可能因环境因素失败
- **执行反馈**：详细描述执行过程和结果，包括失败原因

### 🔍 一致性检测
- **自动检测**：实时检测回复是否符合人物设定
- **评分系统**：提供0-1的一致性评分
- **详细反馈**：生成具体的改进建议
- **可配置开关**：支持启用/禁用检测功能

### 🤖 多智能体系统
- **独立智能体**：每个角色作为独立的智能体，拥有自己的设定和状态
- **并行处理**：所有智能体并行响应玩家指令，提高响应速度
- **环境交互**：智能体根据场景状态、角色状态和玩家指令生成响应
- **状态管理**：自动更新角色状态和场景状态，保留完整历史
- **表里分离**：区分玩家可见信息（表）和隐藏推演信息（里）
- **自动存档**：每次更新自动创建新存档步骤，支持回滚和查看历史
- **响应格式化**：将智能体的JSON响应转换为适合玩家角色的自然文本

### 📖 剧本系统
- **场景管理**：每个剧本包含场景设定文件（SCENE.md）
- **背景介绍**：启动剧本时自动显示背景介绍，增强代入感
- **剧本切换**：支持多个剧本，可随时切换
- **预设事件**：场景文件中可预设剧本事件，指导剧情发展

### ❓ 提问功能
- **信息查询**：回答玩家问题，不推进游戏步骤
- **上下文理解**：基于玩家角色、人物卡、环境信息回答
- **快速响应**：只调用一次LLM，快速获取答案
- **表里区分**：只回答玩家应该知道的信息（表信息）
- **一致性检查**：严格检查回答与历史信息的一致性
- **自动更新**：从回答中提取具体化信息，自动更新角色卡

### 💻 命令行界面（CLI）
- **交互式界面**：友好的命令行交互体验
- **进度显示**：实时显示执行进度和状态
- **彩色输出**：使用Rich库提供美观的彩色输出
- **主题切换**：轻松切换和管理不同剧本
- **存档管理**：查看、删除和管理存档步骤

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
> 💻 CLI使用指南，请查看 [CLI_README.md](CLI_README.md)

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

### 多智能体指令执行

```http
POST /api/themes/{theme}/execute
Content-Type: application/json
```

**请求体**：

```json
{
  "instruction": "我们出发去遗迹",
  "save_step": "0_step",
  "platform": "deepseek",
  "player_role": "冒险者小队队长"
}
```

**参数说明**：
- `instruction` (string, 必填): 玩家指令
- `save_step` (string, 可选): 存档步骤，默认使用当前步骤
- `platform` (string, 可选): API平台
- `player_role` (string, 可选): 玩家角色，会从场景文件中自动提取

**响应示例**：

```json
{
  "surface": {
    "responses": [
      {
        "character_name": "艾伦·勇者",
        "formatted_text": "好的，我们出发！"
      }
    ],
    "summary": "队伍开始向遗迹方向移动..."
  },
  "hidden": {
    "execution_results": [
      {
        "character_name": "艾伦·勇者",
        "execution_result": {
          "success": true,
          "actual_outcome": "成功移动到遗迹入口"
        }
      }
    ]
  },
  "new_step": "1_step"
}
```

### 提问功能

```http
POST /api/themes/{theme}/question
Content-Type: application/json
```

**请求体**：

```json
{
  "question": "队伍现在有多少人？",
  "save_step": "0_step",
  "platform": "deepseek"
}
```

**响应示例**：

```json
{
  "answer": "队伍目前有4人：勇者、魔法师、牧师和盗贼。",
  "consistency_check": {
    "score": 0.95,
    "feedback": "回答与历史信息一致"
  },
  "new_step": "1_step"
}
```

### 主题管理

```http
GET /api/themes
```

获取所有可用的主题（剧本）列表。

```http
GET /api/themes/{theme}/saves
```

获取指定主题的所有存档步骤。

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

### Token统计

```http
GET /api/token-stats
```

获取当前会话的token消耗统计。

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
| `SAVE_DIR` | 存档文件夹 | `save` | 否 |

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
├── cli.py                      # 命令行界面（CLI）
├── config.py                   # 配置管理模块
├── requirements.txt            # Python依赖包列表
├── README.md                   # 项目文档（本文件）
├── QUICKSTART.md               # 快速开始指南
├── CLI_README.md              # CLI使用指南
├── CHARACTER_ATTRIBUTES.md     # 角色属性说明
├── TOKEN_TRACKING.md           # Token追踪说明
├── example_usage.py            # 使用示例脚本
├── start_cli.bat/sh            # CLI启动脚本
├── .gitignore                  # Git忽略文件
├── .env                        # 环境变量文件（需自行创建）
├── characters/                 # 人物卡和剧本文件夹
│   ├── {theme}/                 # 每个主题（剧本）一个文件夹
│   │   ├── SCENE.md            # 场景设定（包含背景介绍）
│   │   ├── CHARACTER_ATTRIBUTES.md  # 主题特定的属性说明
│   │   └── {character_id}.json # 角色文件
├── save/                       # 存档文件夹
│   └── {theme}/                # 按主题分目录
│       └── {step}/              # 每个步骤一个文件夹
│           ├── SCENE.md        # 场景状态
│           ├── {character_id}.json  # 角色状态
│           └── HISTORY.json    # 历史记录
├── conversations/              # 对话记录（JSON文件）
└── services/                   # 服务模块
    ├── __init__.py
    ├── agent.py                # 智能体服务
    ├── chat_service.py         # 对话服务（支持多平台API）
    ├── consistency_checker.py  # 一致性检测服务
    ├── character_store.py      # 人物卡文件存储
    ├── multi_agent_coordinator.py  # 多智能体协调器
    ├── question_service.py     # 提问服务
    ├── environment_manager.py  # 环境管理器
    ├── save_manager.py         # 存档管理器
    ├── theme_manager.py        # 主题管理器
    └── token_tracker.py        # Token追踪器
```

## 🔧 开发指南

### 添加新的API平台

1. 在 `services/chat_service.py` 中添加新的API调用方法
2. 在 `config.py` 中添加对应的配置项
3. 在 `chat()` 方法中添加平台判断逻辑

### 自定义一致性检测

修改 `services/consistency_checker.py` 中的 `check_consistency()` 方法，调整检测提示词和评分逻辑。

### 数据存储

系统**不使用数据库**，所有数据以JSON/MD文件形式存储：

- **人物卡**：`characters/{theme}/{character_id}.json`
- **场景设定**：`characters/{theme}/SCENE.md`
- **存档**：`save/{theme}/{step}/`（包含角色状态、场景状态、历史记录）
- **对话记录**：`conversations/{character_id}.json`

所有文件都是可读的文本格式，便于：
- 版本控制（Git）
- 手动编辑
- 备份和恢复
- 跨平台迁移

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
- **人物卡**：`characters/{theme}/{character_id}.json`
- **存档**：`save/{theme}/{step}/`（包含角色状态、场景状态、历史记录）
- **对话记录**：`conversations/{character_id}.json`
- **场景设定**：`characters/{theme}/SCENE.md`（包含背景介绍、基础信息、剧本预设事件）

这样设计便于阅读、修改和版本控制。

### Q: 如何创建新剧本？

**A**: 
1. 在 `characters/` 目录下创建新文件夹（如 `my_story`）
2. 创建 `SCENE.md` 文件，包含背景介绍和场景设定
3. 创建角色JSON文件（如 `主角.json`）
4. 可选：创建 `CHARACTER_ATTRIBUTES.md` 说明角色属性字段
5. 使用 `theme my_story` 切换到新剧本

### Q: 指令执行失败怎么办？

**A**: 指令执行可能因环境因素失败（如墙壁太滑、体力不足等）。系统会：
1. 详细描述执行过程
2. 说明失败原因
3. 返回实际结果（可能部分成功）
4. 更新角色状态和环境状态

### Q: 如何查看token消耗？

**A**: 
- **CLI**：使用 `tokens` 命令
- **API**：调用 `GET /api/token-stats`
- 统计包括总调用次数、总token数、按平台和操作类型分类的统计

## 📝 更新日志

### v2.0.0 (最新)
- ✨ 多智能体系统：每个角色作为独立智能体并行响应
- ✨ 剧本系统：支持场景设定、背景介绍、预设事件
- ✨ CLI界面：交互式命令行界面，支持进度显示和彩色输出
- ✨ 提问功能：信息查询，不推进游戏步骤
- ✨ 响应格式化：将JSON响应转换为自然文本
- ✨ 玩家角色：支持定义玩家角色，智能体根据角色调整响应
- ✨ Token追踪：自动跟踪和统计token消耗
- ✨ 文件化存储：完全使用JSON/MD文件，不使用数据库
- ✅ 指令执行：指令必须执行，但可能因环境因素失败
- ✅ 自动存档：每次更新自动创建新存档步骤

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
- [Rich](https://rich.readthedocs.io/) - 终端美化库
- [DeepSeek](https://www.deepseek.com/) - AI API服务
- [OpenAI](https://openai.com/) - AI API服务

## 📮 联系方式

如有问题或建议，欢迎通过Issue反馈。

---

**享受创建和管理你的AI角色吧！** 🎉
