# Token消耗统计功能

## 概述

系统现在会自动跟踪所有LLM API调用的token消耗，并提供详细的统计信息。

## 功能特性

### 1. 自动跟踪

所有通过 `ChatService` 的API调用都会自动记录token消耗，包括：
- 对话（chat）
- 智能体响应（agent_response）
- 一致性检查（consistency_check）
- 问题回答（question_answer）
- 环境分析（environment_analysis）
- 响应格式化（response_formatting）

### 2. 统计信息

Token统计包括：
- **总调用次数**：当前会话的API调用总数
- **总Token数**：输入token + 输出token
- **输入Token**：发送给API的token数
- **输出Token**：API返回的token数
- **按平台统计**：deepseek/openai分别的调用次数和token数
- **按操作类型统计**：不同操作类型的调用次数和token数
- **会话时长**：从会话开始到现在的时长

## 使用方法

### CLI命令

#### 查看详细统计

```
> tokens
```

显示完整的token消耗统计信息。

#### 在状态中查看简要统计

```
> status
```

`status` 命令会显示简要的token统计（总token数和调用次数）。

### API端点

#### 获取Token统计

```
GET /api/token-stats
```

返回JSON格式的统计信息：

```json
{
  "total_calls": 15,
  "total_tokens": 12345,
  "total_input_tokens": 8234,
  "total_output_tokens": 4111,
  "by_platform": {
    "deepseek": {
      "calls": 15,
      "tokens": 12345
    }
  },
  "by_operation": {
    "agent_response": {
      "calls": 4,
      "tokens": 5234
    },
    "environment_analysis": {
      "calls": 3,
      "tokens": 3456
    }
  },
  "session_duration": 323.5,
  "session_start": "2024-01-01T12:00:00"
}
```

## 操作类型说明

| 操作类型 | 说明 |
|---------|------|
| `chat` | 基础对话功能 |
| `agent_response` | 智能体响应玩家指令 |
| `consistency_check` | 一致性检查（提问功能） |
| `question_answer` | 问题回答 |
| `environment_analysis` | 环境分析（分析智能体响应） |
| `response_formatting` | 响应格式化（转换为玩家视角文本） |

## 技术实现

### TokenTracker类

`services/token_tracker.py` 提供了token跟踪功能：

```python
from services.token_tracker import token_tracker

# 记录一次调用
token_tracker.record_call(
    platform='deepseek',
    model='deepseek-chat',
    usage={'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150},
    operation='agent_response',
    context={'character_id': 'hero', 'theme': 'adventure_party'}
)

# 获取统计
stats = token_tracker.get_session_stats()

# 重置统计
token_tracker.reset()
```

### 自动集成

所有通过 `ChatService._call_deepseek_api()` 和 `ChatService._call_openai_api()` 的调用都会自动记录token消耗。

## 注意事项

1. **会话范围**：Token统计是会话级别的，重启服务会重置统计
2. **API要求**：需要API返回 `usage` 信息才能准确统计，否则无法记录
3. **性能影响**：Token跟踪对性能影响很小，主要是内存中的记录

## 示例输出

```
================================================================================
📊 Token消耗统计
================================================================================

总调用次数: 15
总Token数: 12,345
  输入Token: 8,234
  输出Token: 4,111

按平台统计:
  deepseek: 15 次调用, 12,345 tokens

按操作类型统计:
  智能体响应: 4 次调用, 5,234 tokens
  环境分析: 3 次调用, 3,456 tokens
  响应格式化: 3 次调用, 2,345 tokens
  一致性检查: 2 次调用, 1,234 tokens
  问题回答: 2 次调用, 76 tokens
  对话: 1 次调用, 0 tokens

会话时长: 5分23秒
```

