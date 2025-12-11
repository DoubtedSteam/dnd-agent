# 单元测试快速开始

5分钟快速上手单元测试。

## 🎯 第一步：安装依赖

```bash
pip install -r requirements.txt
```

## 🚀 第二步：运行测试

### 最简单的方式

```bash
python tests/run_tests.py
```

### 或者使用unittest

```bash
python -m unittest discover tests -v
```

## ✅ 预期结果

如果一切正常，你会看到：

```
test_agent_initialization (tests.test_agent.TestAgent) ... ok
test_process_instruction_success (tests.test_agent.TestAgent) ... ok
...

----------------------------------------------------------------------
Ran XX tests in X.XXXs

OK
```

## 📝 测试什么？

测试覆盖了以下组件：

1. **Agent** - 智能体类
2. **EnvironmentManager** - 环境管理器
3. **ResponseAggregator** - 响应聚合器
4. **StateUpdater** - 状态更新器
5. **MultiAgentCoordinator** - 多智能体协调器
6. **ConversationStore** - 对话记录存储

## 🔍 运行特定测试

### 测试单个组件

```bash
# 测试Agent
python -m unittest tests.test_agent -v

# 测试ConversationStore
python -m unittest tests.test_conversation_store -v
```

### 测试单个方法

```bash
python -m unittest tests.test_agent.TestAgent.test_agent_initialization -v
```

## 🎨 使用真实API（可选）

如果你想测试真实的API调用并查看LLM调用详情：

1. 配置 `.env` 文件：
   ```
   DEEPSEEK_API_KEY=your_key_here
   ```

2. 设置环境变量：
   ```bash
   # Windows PowerShell
   $env:USE_REAL_API="true"
   
   # Linux/Mac
   export USE_REAL_API=true
   ```

3. 运行带LLM日志的测试（推荐）：
   ```bash
   python -m unittest tests.test_with_llm_logging -v
   ```
   
   这会显示每次LLM调用的：
   - 📥 **输入**：发送给LLM的完整消息
   - 📤 **输出**：LLM返回的响应
   - 📊 **Token数**：输入/输出/总计（如果API返回真实token数会标注）
   - 📄 **文件日志**：所有日志自动保存到 `llm_calls.log` 文件

4. 或运行普通真实API测试：
   ```bash
   python -m unittest tests.test_with_real_api -v
   ```

**注意**：这会消耗API额度！

## 📄 查看日志文件

测试运行后，所有LLM调用日志会保存到 `llm_calls.log` 文件：

```bash
# 使用日志查看器
python tests/llm_log_viewer.py

# 查看统计信息
python tests/llm_log_viewer.py stats

# 或直接用文本编辑器打开
# llm_calls.log
```

日志文件包含**完整内容**（不会被截断），方便后续查看和分析。

## ❓ 遇到问题？

### 问题1：找不到模块

**解决**：确保在项目根目录运行测试
```bash
cd C:\Users\47549\Desktop\MyAgent
python tests/run_tests.py
```

### 问题2：测试失败

**解决**：查看详细输出
```bash
python -m unittest discover tests -v
```

### 问题3：需要更多帮助

查看完整文档：[TESTING_GUIDE.md](TESTING_GUIDE.md)

## 📊 测试统计

运行测试后，你会看到：
- ✅ 通过的测试数量
- ❌ 失败的测试（如果有）
- ⏱️ 执行时间

## 🎓 下一步

1. 查看 [TESTING_GUIDE.md](TESTING_GUIDE.md) 了解详细内容
2. 查看 [README.md](README.md) 了解测试结构
3. 尝试修改测试，理解测试逻辑

---

**开始测试吧！** 🚀

