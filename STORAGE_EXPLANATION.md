# 数据存储说明

## 存储方式

系统**不使用数据库**，所有数据都以**JSON或Markdown文件**的形式存储，便于阅读和修改。

## 存储结构

### 1. 人物卡

**位置**：`characters/{theme}/{character_id}.json`

**示例**：`characters/adventure_party/勇者.json`

```json
{
  "id": "hero",
  "name": "艾伦·勇者",
  "description": "勇者，擅长近战...",
  "attributes": {
    "class": "勇者",
    "state": {
      "surface": {...},
      "hidden": {...}
    }
  },
  "theme": "adventure_party"
}
```

### 2. 存档人物卡

**位置**：`save/{theme}/{step}/{character_id}.json`

**示例**：`save/adventure_party/0_step/勇者.json`

存档中的人物卡包含当前游戏状态，会随着游戏进展更新。

### 3. 场景设定

**位置**：
- 初始场景：`characters/{theme}/SCENE.md`
- 存档场景：`save/{theme}/{step}/SCENE.md`

**格式**：Markdown文件，包含：
- 基础信息（时间、地点、背景）
- 表（玩家可见）
- 重大事件
- 里（LLM推演用，隐藏）

### 4. 对话记录

**位置**：`conversations/{character_id}.json`

**格式**：JSON数组

```json
[
  {
    "id": 1,
    "character_id": "hero",
    "user_message": "你好",
    "character_response": "你好！我是...",
    "consistency_score": 0.95,
    "consistency_feedback": "回复符合设定",
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### 5. 属性说明

**位置**：
- 全局：`CHARACTER_ATTRIBUTES.md`
- 主题特定：`characters/{theme}/CHARACTER_ATTRIBUTES.md`

**格式**：Markdown文件，说明属性字段的含义

## 为什么使用文件存储？

### 优势

1. **易于阅读和修改**：直接编辑JSON/MD文件即可
2. **版本控制友好**：可以使用Git管理所有数据
3. **无需数据库**：减少依赖，简化部署
4. **备份简单**：直接复制目录即可
5. **跨平台**：不依赖特定数据库系统
6. **易于迁移**：JSON格式通用，易于转换

### 适用场景

- 小型到中型项目
- 需要版本控制的项目
- 需要手动编辑数据的场景
- 单机或小规模部署

## 数据管理

### 备份

```bash
# 备份所有数据
cp -r characters/ backup/characters/
cp -r save/ backup/save/
cp -r conversations/ backup/conversations/
```

### 版本控制

所有文件都可以加入Git：

```bash
git add characters/ save/ conversations/
git commit -m "更新游戏数据"
```

### 迁移

如果需要迁移数据：

1. 导出：直接复制文件
2. 转换：JSON格式通用，易于转换
3. 导入：复制到新位置即可

## 注意事项

1. **文件编码**：所有文件使用UTF-8编码
2. **JSON格式**：确保JSON格式正确，否则可能无法读取
3. **文件权限**：确保有读写权限
4. **并发访问**：多进程同时写入同一文件可能导致问题，建议使用文件锁或队列

## 与数据库的对比

| 特性 | 文件存储 | 数据库 |
|------|---------|--------|
| 可读性 | ✅ 高（JSON/MD） | ❌ 低（需要工具） |
| 可编辑性 | ✅ 直接编辑 | ❌ 需要SQL |
| 版本控制 | ✅ 友好 | ❌ 困难 |
| 部署复杂度 | ✅ 低 | ❌ 高 |
| 查询性能 | ⚠️ 中等 | ✅ 高 |
| 并发支持 | ⚠️ 有限 | ✅ 好 |
| 数据量 | ⚠️ 适合中小型 | ✅ 适合大型 |

对于智能体平台这种场景，文件存储是更好的选择。

