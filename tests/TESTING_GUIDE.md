# 单元测试指南

本指南将帮助你运行和理解项目的单元测试。

## 📋 目录

1. [快速开始](#快速开始)
2. [测试结构](#测试结构)
3. [运行测试](#运行测试)
4. [测试模式](#测试模式)
5. [测试覆盖](#测试覆盖)
6. [常见问题](#常见问题)
7. [添加新测试](#添加新测试)

## 🚀 快速开始

### 步骤1：安装依赖

```bash
pip install -r requirements.txt
```

### 步骤2：运行所有测试（默认模式）

```bash
# 方法1：使用提供的脚本
python tests/run_tests.py

# 方法2：使用unittest
python -m unittest discover tests -v

# 方法3：使用pytest（如果已安装）
pytest tests/ -v
```

### 步骤3：查看测试结果

测试运行后会显示：
- ✅ 通过的测试数量
- ❌ 失败的测试
- ⚠️ 跳过的测试（如果有）

## 📁 测试结构

```
tests/
├── __init__.py
├── test_agent.py                    # Agent类测试
├── test_environment_manager.py      # EnvironmentManager类测试
├── test_response_aggregator.py      # ResponseAggregator类测试
├── test_state_updater.py            # StateUpdater类测试
├── test_multi_agent_coordinator.py  # MultiAgentCoordinator类测试
├── test_conversation_store.py       # ConversationStore类测试
├── test_integration.py              # 集成测试
├── test_with_real_api.py            # 真实API测试（可选）
├── run_tests.py                     # 运行所有测试的脚本
├── README.md                        # 测试文档
└── TESTING_GUIDE.md                 # 本文件
```

## 🎯 运行测试

### 运行所有测试

```bash
python tests/run_tests.py
```

### 运行特定测试文件

```bash
# 测试Agent类
python -m unittest tests.test_agent -v

# 测试EnvironmentManager类
python -m unittest tests.test_environment_manager -v

# 测试ConversationStore类
python -m unittest tests.test_conversation_store -v
```

### 运行特定测试类

```bash
python -m unittest tests.test_agent.TestAgent -v
```

### 运行特定测试方法

```bash
python -m unittest tests.test_agent.TestAgent.test_agent_initialization -v
```

### 使用pytest（推荐）

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定文件
pytest tests/test_agent.py -v

# 显示覆盖率
pytest tests/ --cov=services --cov-report=html

# 只运行失败的测试
pytest tests/ --lf
```

## 🔧 测试模式

### 模式1：Mock模式（默认）

**特点**：
- ✅ 快速执行
- ✅ 不消耗API额度
- ✅ 不修改真实文件系统
- ✅ 适合CI/CD

**运行方式**：
```bash
# 直接运行，默认就是mock模式
python -m unittest discover tests -v
```

**工作原理**：
- 使用 `unittest.mock` 模拟API调用
- 使用 `mock_open` 模拟文件操作
- 所有外部依赖都被模拟

### 模式2：真实API模式

**特点**：
- ⚠️ 需要有效的API密钥
- ⚠️ 会消耗API额度
- ✅ 测试真实API调用
- ✅ 验证实际功能

**运行方式**：
```bash
# Windows PowerShell
$env:USE_REAL_API="true"
python -m unittest tests.test_with_real_api -v

# Linux/Mac
export USE_REAL_API=true
python -m unittest tests.test_with_real_api -v
```

**前置条件**：
1. 在 `.env` 文件中配置API密钥：
   ```
   DEEPSEEK_API_KEY=your_key_here
   OPENAI_API_KEY=your_key_here
   ```

2. 确保有足够的API额度

### 模式3：真实文件系统模式

**特点**：
- ✅ 测试真实文件操作
- ⚠️ 会创建/修改文件（使用临时目录）
- ✅ 测试后自动清理

**运行方式**：
```bash
# Windows PowerShell
$env:USE_REAL_FILES="true"
python -m unittest tests.test_conversation_store -v

# Linux/Mac
export USE_REAL_FILES=true
python -m unittest tests.test_conversation_store -v
```

## 📊 测试覆盖

### Agent 测试 (`test_agent.py`)

| 测试方法 | 说明 | 状态 |
|---------|------|------|
| `test_agent_initialization` | 测试智能体初始化 | ✅ |
| `test_process_instruction_success` | 测试处理指令成功 | ✅ |
| `test_process_instruction_with_json_wrapper` | 测试JSON包装的响应 | ✅ |
| `test_process_instruction_invalid_json` | 测试无效JSON处理 | ✅ |
| `test_build_agent_prompt` | 测试构建提示词 | ✅ |

### EnvironmentManager 测试 (`test_environment_manager.py`)

| 测试方法 | 说明 | 状态 |
|---------|------|------|
| `test_load_scene_from_save` | 测试从存档加载场景 | ✅ |
| `test_load_scene_from_initial` | 测试从初始场景加载 | ✅ |
| `test_load_scene_not_found` | 测试场景不存在 | ✅ |
| `test_apply_responses_to_environment` | 测试应用响应到环境 | ✅ |
| `test_update_scene_success` | 测试更新场景成功 | ✅ |
| `test_update_scene_not_found` | 测试更新场景（文件不存在） | ✅ |

### ResponseAggregator 测试 (`test_response_aggregator.py`)

| 测试方法 | 说明 | 状态 |
|---------|------|------|
| `test_aggregate_responses_basic` | 测试基本响应聚合 | ✅ |
| `test_aggregate_responses_with_state_changes` | 测试包含状态变化的聚合 | ✅ |
| `test_aggregate_responses_empty` | 测试空响应列表 | ✅ |
| `test_generate_surface_summary` | 测试生成表信息摘要 | ✅ |
| `test_generate_surface_summary_empty` | 测试生成空摘要 | ✅ |

### StateUpdater 测试 (`test_state_updater.py`)

| 测试方法 | 说明 | 状态 |
|---------|------|------|
| `test_update_character_state_success` | 测试更新角色状态成功 | ✅ |
| `test_update_character_state_not_found` | 测试更新角色状态（文件不存在） | ✅ |
| `test_update_scene_state_success` | 测试更新场景状态成功 | ✅ |
| `test_update_scene_state_not_found` | 测试更新场景状态（文件不存在） | ✅ |
| `test_update_scene_state_add_events_section` | 测试添加重大事件部分 | ✅ |

### MultiAgentCoordinator 测试 (`test_multi_agent_coordinator.py`)

| 测试方法 | 说明 | 状态 |
|---------|------|------|
| `test_process_instruction_success` | 测试处理指令成功 | ✅ |
| `test_process_instruction_no_scene` | 测试处理指令（场景不存在） | ✅ |
| `test_process_instruction_specific_characters` | 测试处理指令（指定角色） | ✅ |
| `test_extract_major_events` | 测试提取重大事件 | ✅ |

### ConversationStore 测试 (`test_conversation_store.py`)

| 测试方法 | 说明 | 状态 |
|---------|------|------|
| `test_save_conversation` | 测试保存对话记录 | ✅ |
| `test_save_multiple_conversations` | 测试保存多条对话记录 | ✅ |
| `test_get_conversations_empty` | 测试获取对话记录（空） | ✅ |
| `test_get_conversations_with_limit` | 测试获取对话记录（带限制） | ✅ |
| `test_get_conversations_all` | 测试获取所有对话记录 | ✅ |
| `test_conversation_file_format` | 测试对话记录文件格式 | ✅ |

### 集成测试 (`test_integration.py`)

| 测试方法 | 说明 | 状态 |
|---------|------|------|
| `test_full_workflow` | 测试完整工作流程 | ✅ |
| `test_workflow_with_state_changes` | 测试包含状态变化的工作流程 | ✅ |

## 🐛 常见问题

### Q1: 测试失败，提示找不到模块？

**A**: 确保已安装所有依赖：
```bash
pip install -r requirements.txt
```

### Q2: 如何查看详细的测试输出？

**A**: 使用 `-v` 参数：
```bash
python -m unittest discover tests -v
```

### Q3: 如何只运行失败的测试？

**A**: 使用pytest：
```bash
pytest tests/ --lf
```

### Q4: 如何查看测试覆盖率？

**A**: 使用pytest-cov：
```bash
# 安装
pip install pytest-cov

# 运行
pytest tests/ --cov=services --cov-report=html

# 查看报告
# 打开 htmlcov/index.html
```

### Q5: 真实API测试失败？

**A**: 检查：
1. `.env` 文件中是否配置了API密钥
2. API密钥是否有效
3. 是否有足够的API额度
4. 网络连接是否正常

### Q6: 测试运行很慢？

**A**: 
- Mock模式应该很快（< 1秒）
- 如果慢，可能是：
  - 并行测试的线程池问题
  - 某些测试没有正确mock
  - 使用了真实API（会慢）

### Q7: 如何跳过某些测试？

**A**: 使用 `@unittest.skip` 装饰器：
```python
@unittest.skip("跳过原因")
def test_something(self):
    pass
```

## ✏️ 添加新测试

### 步骤1：创建测试文件

在 `tests/` 目录下创建 `test_<module_name>.py`

### 步骤2：编写测试类

```python
import unittest
from unittest.mock import patch
from services.your_module import YourClass
from config import Config

class TestYourClass(unittest.TestCase):
    """YourClass 类测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = Config()
        self.instance = YourClass(self.config)
    
    def test_your_method(self):
        """测试你的方法"""
        # Arrange
        test_input = "测试输入"
        
        # Act
        result = self.instance.your_method(test_input)
        
        # Assert
        self.assertEqual(result, expected_value)
```

### 步骤3：运行测试

```bash
python -m unittest tests.test_your_module -v
```

### 测试编写规范

1. **命名规范**：
   - 测试文件：`test_<module_name>.py`
   - 测试类：`Test<ClassName>`
   - 测试方法：`test_<functionality>`

2. **使用setUp/tearDown**：
   ```python
   def setUp(self):
       # 设置测试环境
       pass
   
   def tearDown(self):
       # 清理测试环境
       pass
   ```

3. **使用Mock**：
   ```python
   @patch('module.external_dependency')
   def test_with_mock(self, mock_dependency):
       mock_dependency.return_value = "模拟值"
       # 测试代码
   ```

4. **清晰的断言**：
   ```python
   self.assertEqual(actual, expected)
   self.assertIn(item, container)
   self.assertTrue(condition)
   self.assertIsNone(value)
   ```

## 📈 测试最佳实践

1. **测试独立性**：每个测试应该独立，不依赖其他测试
2. **快速执行**：使用mock，避免真实API调用
3. **覆盖边界情况**：测试正常情况、异常情况、边界值
4. **清晰的命名**：测试名称应该清楚说明测试内容
5. **文档字符串**：为每个测试方法添加说明

## 🔍 调试测试

### 使用pdb调试

```python
import pdb

def test_something(self):
    pdb.set_trace()  # 在这里设置断点
    # 测试代码
```

### 打印调试信息

```python
def test_something(self):
    result = function_under_test()
    print(f"调试信息: {result}")  # 使用-v参数可以看到
    self.assertEqual(result, expected)
```

### 使用pytest的详细输出

```bash
pytest tests/ -v -s  # -s 显示print输出
```

## 📚 相关文档

- [测试README](README.md) - 测试文档
- [DATABASE_EXPLANATION.md](../DATABASE_EXPLANATION.md) - 数据库说明
- [STORAGE_EXPLANATION.md](../STORAGE_EXPLANATION.md) - 存储说明
- [MULTI_AGENT_SYSTEM.md](../MULTI_AGENT_SYSTEM.md) - 多智能体系统文档

## 🎓 学习资源

- [Python unittest文档](https://docs.python.org/3/library/unittest.html)
- [pytest文档](https://docs.pytest.org/)
- [unittest.mock文档](https://docs.python.org/3/library/unittest.mock.html)

---

**祝你测试顺利！** 🎉
