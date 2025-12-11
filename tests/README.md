# 测试文档

## 📚 文档导航

- **[QUICK_START.md](QUICK_START.md)** - 5分钟快速开始指南 ⭐推荐
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - 完整的测试指南（详细版）
- **[README.md](README.md)** - 本文件（测试结构说明）

## 测试结构

测试文件位于 `tests/` 目录下：

- `test_agent.py` - Agent 类单元测试
- `test_environment_manager.py` - EnvironmentManager 类单元测试
- `test_response_aggregator.py` - ResponseAggregator 类单元测试
- `test_state_updater.py` - StateUpdater 类单元测试
- `test_environment_modification.py` - **环境修改测试（真实文件系统）** ⭐
- `test_multi_agent_coordinator.py` - MultiAgentCoordinator 类单元测试
- `test_integration.py` - 集成测试
- `test_conversation_store.py` - ConversationStore 类单元测试
- `run_tests.py` - 运行所有测试的脚本

## 运行测试

### 方法1：使用 run_tests.py

```bash
python tests/run_tests.py
```

### 方法2：使用 unittest

```bash
# 运行所有测试
python -m unittest discover tests

# 运行特定测试文件
python -m unittest tests.test_agent

# 运行特定测试类
python -m unittest tests.test_agent.TestAgent

# 运行特定测试方法
python -m unittest tests.test_agent.TestAgent.test_agent_initialization
```

### 方法3：使用 pytest（如果已安装）

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_agent.py

# 显示详细输出
pytest tests/ -v

# 显示覆盖率
pytest tests/ --cov=services --cov-report=html
```

## 测试覆盖

### Agent 测试
- ✅ 智能体初始化
- ✅ 处理指令成功
- ✅ 处理指令（JSON包装）
- ✅ 处理指令（无效JSON）
- ✅ 构建智能体提示词

### EnvironmentManager 测试
- ✅ 从存档加载场景
- ✅ 从初始场景加载
- ✅ 场景不存在
- ✅ 应用响应到环境
- ✅ 更新场景成功
- ✅ 更新场景（文件不存在）

### ResponseAggregator 测试
- ✅ 基本响应聚合
- ✅ 包含状态变化的响应聚合
- ✅ 空响应列表
- ✅ 生成表信息摘要
- ✅ 生成空摘要

### StateUpdater 测试
- ✅ 更新角色状态成功
- ✅ 更新角色状态（文件不存在）
- ✅ 更新场景状态成功
- ✅ 更新场景状态（文件不存在）
- ✅ 更新场景状态（添加重大事件部分）

### MultiAgentCoordinator 测试
- ✅ 处理指令成功
- ✅ 处理指令（场景不存在）
- ✅ 处理指令（指定角色）
- ✅ 提取重大事件

### 集成测试
- ✅ 完整工作流程
- ✅ 包含状态变化的工作流程

### 环境修改测试（真实文件系统）
- ✅ 更新角色状态会正确写入文件
- ✅ 更新场景状态会添加重大事件
- ✅ 更新场景状态会替换现有事件
- ✅ 更新角色状态会合并变化
- ✅ 更新不存在的文件会失败
- ✅ 环境管理器能加载更新后的场景
- ✅ 完整的环境更新工作流程

## 测试模式

### 默认模式（Mock）
- 使用mock模拟API调用和文件操作
- 快速、安全、不消耗API额度
- 适合日常开发和CI/CD

### 真实API/文件系统模式
设置环境变量启用：
```bash
export USE_REAL_API=true      # 使用真实API
export USE_REAL_FILES=true    # 使用真实文件系统
```

**注意**：
- 需要有效的API密钥（在`.env`文件中配置）
- 会消耗API额度
- 文件操作使用临时目录，测试后自动清理

## 注意事项

1. **Mock 使用**：默认测试使用 `unittest.mock` 来模拟外部依赖
2. **真实API测试**：设置 `USE_REAL_API=true` 可以使用真实API（需要API密钥）
3. **真实文件系统**：设置 `USE_REAL_FILES=true` 可以使用真实文件系统（使用临时目录）
4. **并行处理**：MultiAgentCoordinator 的并行处理通过 ThreadPoolExecutor 实现

## 添加新测试

添加新测试时，请遵循以下规范：

1. 测试文件命名：`test_<module_name>.py`
2. 测试类命名：`Test<ClassName>`
3. 测试方法命名：`test_<functionality>`
4. 使用 `setUp()` 方法设置测试环境
5. 使用 `unittest.mock` 模拟外部依赖
6. 添加清晰的文档字符串说明测试目的

## 持续集成

可以在 CI/CD 流程中运行测试：

```yaml
# 示例 GitHub Actions
- name: Run tests
  run: python tests/run_tests.py
```

