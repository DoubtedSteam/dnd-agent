# LLM调用日志指南

## 概述

LLM调用日志功能可以让你在运行测试时，清楚地看到所有对LLM的调用情况，包括：
- 📥 **输入**：发送给LLM的完整消息（system + user messages）
- 📤 **输出**：LLM返回的响应内容
- 📊 **Token数**：输入token、输出token、总计token
- 🔧 **平台信息**：使用的API平台、模型、温度参数
- 📄 **文件输出**：所有日志自动保存到文件，方便后续查看

## 快速开始

### 1. 启用真实API测试

```bash
# Windows PowerShell
$env:USE_REAL_API="true"

# Linux/Mac
export USE_REAL_API=true
```

### 2. 运行带日志的测试

```bash
python -m unittest tests.test_with_llm_logging -v
```

## 输出示例

运行测试时，你会看到类似以下的输出：

```
================================================================================
📞 LLM API 调用 #1
================================================================================
⏰ 时间: 2024-01-01T12:00:00
🔧 平台: deepseek
🤖 模型: deepseek-chat
🌡️  温度: 0.7

📥 输入 (1234 tokens) (API返回):
--------------------------------------------------------------------------------

[1] SYSTEM:
你是一个角色扮演助手。请严格按照以下设定进行对话。

【信息来源：人物卡配置】
=== 人物设定 ===
人物描述：
一个勇敢的战士，擅长近战

人物属性（结构化设定，仅用于参考，不要机械复述）：
{
  "class": "勇者",
  "state": {
    "surface": {
      "perceived_state": "准备就绪"
    },
    "hidden": {
      "observer_state": "检查装备",
      "inner_monologue": "要保持警惕"
    }
  }
}

... (完整内容)

[2] USER:
玩家指令：我们出发去遗迹调查

请根据你的角色设定、当前场景状态和玩家指令，生成以下内容：

1. **响应**：你对玩家指令的回应（对话、行动等）
2. **状态变化**：你的状态可能发生的变化（JSON格式）
...

📤 输出 (567 tokens) (API返回):
--------------------------------------------------------------------------------
{
    "response": "好的，我们出发！让我先检查一下装备...",
    "state_changes": {
        "surface": {
            "perceived_state": "显得更加专注和警惕"
        },
        "hidden": {
            "observer_state": "握紧剑柄，观察四周",
            "inner_monologue": "必须确保队伍安全，遗迹可能很危险"
        }
    },
    "attribute_changes": {}
}

📊 总计: 1801 tokens
================================================================================
```

## Token数说明

### API返回的真实Token数

如果API返回了usage信息，会显示：
- `(API返回)` - 这是API返回的真实token数，最准确

### 估算的Token数

如果API没有返回usage信息，会显示：
- `(估算)` - 这是根据字符数估算的，可能不够准确

## 调用摘要

测试结束后，会显示调用摘要：

```
================================================================================
📊 LLM API 调用摘要
================================================================================
总调用次数: 4
总Token数: 7234

按平台统计:
  deepseek: 4 次调用, 7234 tokens
================================================================================
📄 完整日志已保存到: C:\Users\47549\Desktop\MyAgent\llm_calls.log
================================================================================
```

## 文件日志

### 日志文件位置

所有LLM调用日志会自动保存到：
- **默认位置**：项目根目录下的 `llm_calls.log`
- **完整路径**：测试结束后会在摘要中显示

### 查看日志文件

#### 方法1：使用日志查看器（推荐）

```bash
# 查看完整日志
python tests/llm_log_viewer.py

# 或指定文件
python tests/llm_log_viewer.py path/to/your/log.log

# 查看统计信息
python tests/llm_log_viewer.py stats
```

#### 方法2：直接打开文件

日志文件是纯文本格式，可以用任何文本编辑器打开：
- Windows: 记事本、VS Code、Notepad++
- Linux/Mac: vim、nano、VS Code

#### 方法3：在终端查看

```bash
# Windows PowerShell
Get-Content llm_calls.log

# Linux/Mac
cat llm_calls.log

# 或使用less分页查看
less llm_calls.log
```

### 日志文件格式

日志文件包含：
- ✅ **完整内容**：文件中的内容不会被截断（与终端显示不同）
- ✅ **所有调用**：每次LLM调用的完整记录
- ✅ **调用摘要**：测试结束后的统计信息

### 自定义日志文件位置

```python
from tests.llm_call_logger import LLMCallLogger

# 创建自定义日志文件
logger = LLMCallLogger(log_file="custom_path/llm_calls.log")
```

### 清理日志文件

日志文件默认是**追加模式**，每次测试都会追加到文件末尾。

如果需要清空日志文件：
```bash
# Windows PowerShell
Remove-Item llm_calls.log

# Linux/Mac
rm llm_calls.log
```

或者在代码中：
```python
from tests.llm_call_logger import logger

# 清空内存中的记录
logger.clear()

# 如果需要清空文件，可以删除文件
import os
if os.path.exists(logger.log_file):
    os.remove(logger.log_file)
```

## 使用方法

### 在测试中使用

```python
from tests.llm_call_logger import logger

class TestMyFeature(unittest.TestCase):
    def setUp(self):
        logger.clear()  # 清空之前的记录
    
    def test_something(self):
        # 你的测试代码
        # LLM调用会自动记录
        pass
    
    def tearDown(self):
        # 查看本次测试的调用
        print(f"本次测试进行了 {len(logger.calls)} 次LLM调用")
```

### 手动记录调用

```python
from tests.llm_call_logger import logger

logger.log_call(
    platform='deepseek',
    messages=[{"role": "system", "content": "..."}, {"role": "user", "content": "..."}],
    response="LLM的响应",
    model='deepseek-chat',
    temperature=0.7,
    usage={'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150}
)
```

### 控制日志输出

```python
from tests.llm_call_logger import logger

# 禁用日志
logger.disable()

# 启用日志
logger.enable()

# 清空记录
logger.clear()

# 获取摘要
summary = logger.get_summary()
print(summary)

# 打印摘要
logger.print_summary()
```

## 注意事项

1. **自动记录**：当使用真实API时，`ChatService`会自动记录所有调用
2. **性能影响**：记录功能对性能影响很小，主要是打印输出
3. **Token估算**：如果API不返回usage，token数是估算的，可能不够准确
4. **输出长度**：过长的内容会被截断显示（前500字符），但完整内容会保存在`logger.calls`中

## 查看完整调用记录

所有调用记录都保存在`logger.calls`列表中，你可以：

```python
from tests.llm_call_logger import logger

# 查看所有调用
for call in logger.calls:
    print(f"调用 #{call['timestamp']}")
    print(f"平台: {call['platform']}")
    print(f"Token: {call['total_tokens']}")
    print(f"输入: {call['input']['messages']}")
    print(f"输出: {call['output']['response']}")
```

## 导出调用记录

```python
import json
from tests.llm_call_logger import logger

# 导出为JSON
with open('llm_calls.json', 'w', encoding='utf-8') as f:
    json.dump(logger.calls, f, ensure_ascii=False, indent=2)
```

## 相关文件

- `tests/llm_call_logger.py` - LLM调用记录器实现
- `tests/test_with_llm_logging.py` - 带日志的测试示例
- `services/chat_service.py` - 自动记录LLM调用

