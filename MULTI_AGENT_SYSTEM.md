# 多智能体系统文档

## 系统架构

多智能体系统将每个角色视为独立的智能体，实现以下工作流程：

```
玩家给出指令
    ↓
发送给每一个智能体（并行处理）
    ↓
智能体按照自己的设定+环境+玩家指令给出响应
    ↓
将响应放置到环境中
    ↓
获得所有人物变化+环境变化
    ↓
按照表里区分，反应给玩家+更新人物卡和环境
```

## 核心组件

### 1. Agent（智能体）
- **文件**: `services/agent.py`
- **功能**: 每个角色作为独立的智能体
- **职责**:
  - 根据角色设定、场景状态和玩家指令生成响应
  - 分析自身状态变化
  - 返回响应和状态变化

### 2. EnvironmentManager（环境管理器）
- **文件**: `services/environment_manager.py`
- **功能**: 管理场景状态
- **职责**:
  - 加载场景内容
  - 处理智能体响应，分析环境变化
  - 更新场景文件

### 3. ResponseAggregator（响应聚合器）
- **文件**: `services/response_aggregator.py`
- **功能**: 收集和分析所有智能体响应
- **职责**:
  - 聚合所有智能体响应
  - 分离表/里信息
  - 生成摘要

### 4. StateUpdater（状态更新器）
- **文件**: `services/state_updater.py`
- **功能**: 更新人物卡和环境文件
- **职责**:
  - 更新角色状态（存档中的人物卡）
  - 更新场景状态（重大事件等）
  - 按照表/里区分更新

### 5. MultiAgentCoordinator（多智能体协调器）
- **文件**: `services/multi_agent_coordinator.py`
- **功能**: 协调所有智能体的工作流程
- **职责**:
  - 加载场景和角色
  - 并行处理所有智能体
  - 协调响应聚合和状态更新

## API 接口

### 1. 执行指令

```http
POST /api/themes/{theme}/execute
Content-Type: application/json
```

**请求体**:
```json
{
  "instruction": "玩家指令内容",
  "save_step": "0_step",  // 可选：存档步骤
  "character_ids": ["hero", "mage"],  // 可选：指定角色ID列表，如果为空则使用所有角色
  "platform": "deepseek"  // 可选：指定API平台
}
```

**响应**:
```json
{
  "surface": {
    "responses": [
      {
        "character_name": "勇者",
        "response": "好的，我们出发吧！"
      },
      {
        "character_name": "魔法师",
        "response": "让我先检查一下魔法装备..."
      }
    ],
    "summary": "勇者: 好的，我们出发吧！...\n魔法师: 让我先检查一下魔法装备..."
  },
  "hidden": {
    "state_changes": {
      "hero": {
        "surface": {
          "perceived_state": "显得更加警惕，检查装备"
        },
        "hidden": {
          "observer_state": "握紧剑柄，观察四周",
          "inner_monologue": "必须确保队伍安全"
        }
      }
    },
    "attribute_changes": {
      "hero": {
        "vitals": {
          "hp": 180,
          "mp": 40,
          "stamina": 140
        }
      }
    },
    "environment_changes": {
      "scene_changes": {
        "surface": {},
        "hidden": {}
      },
      "major_events": []
    }
  }
}
```

### 2. 提问功能

```http
POST /api/themes/{theme}/question
Content-Type: application/json
```

**请求体**:
```json
{
  "question": "队伍现在有多少人？",
  "save_step": "0_step",  // 可选：指定存档步骤
  "character_ids": ["hero", "mage"],  // 可选：指定参考的角色
  "platform": "deepseek",  // 可选：指定API平台
  "player_role": "冒险者小队队长"  // 可选：玩家角色
}
```

**响应**:
```json
{
  "answer": "作为队长，你知道队伍目前有4名成员：勇者艾伦、魔法师莉娜、牧师艾米和盗贼凯。",
  "question": "队伍现在有多少人？"
}
```

**特点**:
- ✅ 不推进游戏步骤
- ✅ 不创建新存档
- ✅ 不更新状态
- ✅ 只调用一次LLM，快速响应
- ✅ 基于玩家角色、人物卡、环境信息回答

## 工作流程详解

### 1. 玩家给出指令
玩家通过API发送指令，例如："我们出发去遗迹"

### 2. 发送给每一个智能体
系统会：
- 加载场景内容（SCENE.md，包含玩家角色信息）
- 提取玩家角色
- 加载所有角色（或指定角色）
- 为每个角色创建Agent实例
- 使用线程池并行处理所有智能体（传递玩家角色信息）

### 3. 智能体生成响应
每个智能体：
- 接收玩家指令（理解玩家角色上下文）
- 结合自己的角色设定
- 参考当前场景状态
- 生成JSON格式的响应和状态变化

### 4. 将响应放置到环境中
- 收集所有智能体响应
- 聚合响应，分离表/里信息
- 使用LLM分析环境变化
- 提取重大事件

### 5. 创建新存档步骤
- 从当前步骤（如`0_step`）复制到新步骤（如`1_step`）
- 保留历史记录，支持回滚

### 6. 更新状态（在新步骤中）
- 更新角色状态（人物卡JSON文件）
- 更新场景状态（SCENE.md，包括重大事件）
- 所有更新都在新步骤中进行

### 7. 格式化响应（在更新状态之后）
- 使用更新后的场景信息
- 将JSON响应转换为适合玩家角色的文本
- 以玩家视角描述事件

### 8. 返回结果
- **表信息**：格式化后的文本响应，适合玩家阅读
- **里信息**：详细状态变化、原始JSON响应（供系统使用）
- **新步骤**：新创建的存档步骤名称

## 表/里信息区分

### 表信息（Surface）
- 玩家可见的响应
- 角色对玩家指令的回应
- 摘要信息

### 里信息（Hidden）
- 角色的状态变化（observer_state, inner_monologue）
- 属性变化（vitals, equipment等）
- 环境变化详情
- 重大事件

## 状态更新机制

### 角色状态更新
- 更新存档目录下的人物卡（`save/{theme}/{save_step}/{character_id}.json`）
- 更新 `state.surface` 和 `state.hidden`
- 更新其他属性（如 vitals）

### 场景状态更新
- 更新场景文件（`save/{theme}/{save_step}/SCENE.md`）
- 更新"重大事件"部分
- 记录环境变化

## 使用示例

### Python 示例

```python
import requests

BASE_URL = "http://localhost:5000"

# 执行指令
data = {
    "instruction": "我们出发去遗迹调查",
    "save_step": "0_step",
    "platform": "deepseek"
}

response = requests.post(
    f"{BASE_URL}/api/themes/adventure_party/execute",
    json=data
)

result = response.json()

# 表信息：玩家可见
print("角色响应：")
for resp in result['surface']['responses']:
    print(f"{resp['character_name']}: {resp['response']}")

# 里信息：隐藏的状态变化
print("\n状态变化：")
for char_id, changes in result['hidden']['state_changes'].items():
    print(f"{char_id}: {changes}")
```

## 注意事项

1. **并行处理**：所有智能体并行处理，提高效率
2. **状态一致性**：确保状态更新的一致性
3. **表里分离**：严格区分表/里信息，保护游戏体验
4. **错误处理**：单个智能体失败不影响其他智能体
5. **Token消耗**：每个智能体独立调用LLM，注意token消耗

## 扩展功能

未来可以扩展：
- 智能体之间的交互
- 更复杂的环境变化分析
- 智能体决策树
- 动态场景生成

