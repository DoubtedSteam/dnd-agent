# 数据库使用说明

## 数据库使用情况

### 之前使用数据库的地方

在原始实现中，数据库（SQLite）仅用于存储**对话历史记录**：

1. **`/api/characters/<character_id>/chat`** 接口
   - 保存单次对话记录到数据库
   - 存储：用户消息、角色回复、一致性评分、反馈

2. **`/api/characters/<character_id>/conversations`** 接口
   - 从数据库读取对话历史
   - 按时间倒序返回

### 为什么不再需要数据库？

根据系统设计，我们已经：

1. **移除了对话历史的使用**：系统不再使用对话历史来生成回复，而是仅根据场景状态和人物设定
2. **采用文件化存储**：所有数据（人物卡、场景、存档）都使用JSON/MD文件存储
3. **简化架构**：移除数据库依赖，使系统更轻量、更易维护

### 新的存储方式

现在所有记录都使用**JSON文件**存储：

- **对话记录**：`conversations/{character_id}.json`
  - 格式：JSON数组，每个元素是一条对话记录
  - 包含：用户消息、角色回复、一致性评分、时间戳

- **人物卡**：`characters/{theme}/{character_id}.json`
- **存档人物卡**：`save/{theme}/{step}/{character_id}.json`
- **场景设定**：`characters/{theme}/SCENE.md` 或 `save/{theme}/{step}/SCENE.md`

## 数据存储结构

### 对话记录文件示例

`conversations/hero.json`:
```json
[
  {
    "id": 1,
    "character_id": "hero",
    "user_message": "你好",
    "character_response": "你好！我是勇者...",
    "consistency_score": 0.95,
    "consistency_feedback": "回复符合角色设定...",
    "created_at": "2024-01-01T00:00:00"
  },
  {
    "id": 2,
    "character_id": "hero",
    "user_message": "我们出发吧",
    "character_response": "好的，我准备好了！",
    "consistency_score": null,
    "consistency_feedback": null,
    "created_at": "2024-01-01T00:05:00"
  }
]
```

## 优势

1. **易于阅读和修改**：直接编辑JSON文件即可
2. **版本控制友好**：可以使用Git管理对话历史
3. **无需数据库**：减少依赖，简化部署
4. **备份简单**：直接复制文件即可
5. **跨平台**：不依赖特定数据库系统

## 迁移说明

如果之前使用数据库存储对话记录，可以：

1. 导出数据库中的对话记录
2. 转换为JSON格式
3. 保存到 `conversations/{character_id}.json` 文件

## 注意事项

- 对话记录文件会随着时间增长，建议定期归档
- 可以按日期或主题分割对话记录文件
- 如果不需要对话历史功能，可以完全移除相关代码

