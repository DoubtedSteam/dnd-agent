# 快速开始指南

5分钟快速上手智能体平台。

## 前置要求

- Python 3.8 或更高版本
- DeepSeek 或 OpenAI API 密钥（至少需要一个）

## 步骤 1：安装依赖

```bash
pip install -r requirements.txt
```

## 步骤 2：配置 API 密钥

创建 `.env` 文件（在项目根目录）：

```bash
# Windows PowerShell
New-Item -Path .env -ItemType File

# Linux/Mac
touch .env
```

编辑 `.env` 文件，填入你的 API 密钥：

```env
# DeepSeek API（推荐，性价比高）
DEEPSEEK_API_KEY=sk-your-deepseek-key-here

# OpenAI API（可选）
OPENAI_API_KEY=sk-your-openai-key-here

# 默认使用的平台
DEFAULT_API_PLATFORM=deepseek

# 启用一致性检测
CONSISTENCY_CHECK_ENABLED=true
```

> 💡 **获取 API 密钥**
> - DeepSeek: https://platform.deepseek.com/
> - OpenAI: https://platform.openai.com/

## 人物卡文件存放方式

- 每个人物对应一个配置文件，按主题存放在 `characters/{theme}/` 目录
- 文件格式为 JSON，文件名为人物的 `id`（示例：`characters/adventure_party/hero.json`）
- 通过 API 创建/更新/删除人物卡会自动同步到对应文件

推荐属性字段：
- `gender`: 性别
- `vitals`: `{ hp, mp, stamina }`
- `weapon`: `{ main_hand, off_hand, backup, ranged }`
- `equipment`: `{ armor/robe, helmet/hat, boots, accessory: [] }`
- `skills`: 技能数组
- 详细字段含义见 `CHARACTER_ATTRIBUTES.md`；这些结构化属性会随人物描述一起传给LLM。

## 步骤 3：启动服务

```bash
python app.py
```

看到以下输出表示启动成功：

```
 * Running on http://0.0.0.0:5000
```

## 步骤 4：测试运行

打开新的终端窗口，运行示例脚本：

```bash
python example_usage.py
```

或者使用 curl 测试：

```bash
# 创建人物卡
curl -X POST http://localhost:5000/api/characters \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试角色",
    "description": "一个友好的AI助手",
    "attributes": {"personality": "友好"}
  }'

# 获取返回的 character_id，然后进行对话
curl -X POST http://localhost:5000/api/characters/1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好"
  }'
```

## 下一步

- 📖 查看 [README.md](README.md) 了解详细功能
- 🔧 查看 API 接口文档
- 💻 运行 `example_usage.py` 查看更多示例

## 常见问题

**Q: 提示 API 密钥错误？**  
A: 检查 `.env` 文件中的密钥是否正确，确保没有多余的空格。

**Q: 端口 5000 被占用？**  
A: 修改 `app.py` 最后一行的端口号，例如改为 `port=5001`。

**Q: 数据库文件在哪里？**  
A: 数据库文件 `agent_platform.db` 会自动创建在项目根目录。

**Q: 如何禁用一致性检测？**  
A: 在 `.env` 文件中设置 `CONSISTENCY_CHECK_ENABLED=false`。

## 需要帮助？

查看完整的 [README.md](README.md) 文档获取更多信息。

