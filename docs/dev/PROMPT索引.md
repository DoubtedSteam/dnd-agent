# Prompt索引文档

本文档索引了系统中所有LLM调用的prompt位置，方便修改和调整。

## 目录

1. [Agent响应生成Prompt](#1-agent响应生成prompt)
2. [导演评估Prompt](#2-导演评估prompt)
3. [响应格式化Prompt](#3-响应格式化prompt)
4. [一致性检查Prompt](#4-一致性检查prompt)
5. [提问服务Prompt](#5-提问服务prompt)
6. [对话服务Prompt](#6-对话服务prompt)

---

## 1. Agent响应生成Prompt

**文件位置**：`services/agent.py`  
**函数**：`Agent._build_agent_prompt()`  
**行号**：279-342  
**调用时机**：每个角色处理玩家指令时，并行生成响应  
**用途**：让每个角色根据自身设定、场景和指令生成响应

---

## 2. 导演评估Prompt

**文件位置**：`services/director_evaluator.py`  
**函数**：`DirectorEvaluator._build_director_prompt()`  
**行号**：292-399  
**调用时机**：Agent响应生成后，评估环境变化并做出决策  
**用途**：分析环境变化，决定事件触发、怪物出现、场景转换

**输出格式**：返回JSON格式，包含：
- `environment_analysis`：环境变化分析结果
- `director_decision`：导演决策结果

---

## 3. 响应格式化Prompt

### 3.1 主要格式化Prompt

**文件位置**：`services/response_formatter.py`  
**函数**：`ResponseFormatter.format_responses_for_player()`  
**行号**：100-148  
**调用时机**：Agent响应生成后，将原始响应格式化为玩家可见的文本  
**用途**：将Agent的原始响应转换为玩家视角的流畅文本

### 3.2 摘要生成Prompt

**文件位置**：`services/response_formatter.py`  
**函数**：`ResponseFormatter._generate_summary_only()`  
**行号**：288-320  
**调用时机**：生成第三人称、小说风格的摘要  
**用途**：生成摘要文本

---

## 4. 一致性检查Prompt

### 4.1 角色一致性检查

**文件位置**：`services/consistency_checker.py`  
**函数**：`ConsistencyChecker.check_consistency()`  
**行号**：144-181  
**调用时机**：检查角色回复是否符合设定  
**用途**：验证角色回复是否与角色设定一致

### 4.2 提问一致性检查

**文件位置**：`services/question_consistency_checker.py`  
**函数**：`QuestionConsistencyChecker.check_answer_consistency()`  
**行号**：102-141  
**调用时机**：检查回答与历史一致性  
**用途**：验证回答是否与历史对话一致

---

## 5. 提问服务Prompt

**文件位置**：`services/question_service.py`  
**函数**：`QuestionService._build_question_prompt()`  
**行号**：223-257  
**调用时机**：玩家提问时  
**用途**：回答玩家的问题

---

## 6. 对话服务Prompt

**文件位置**：`services/chat_service.py`  
**函数**：`ChatService.chat()`  
**行号**：341-371  
**调用时机**：通过API直接调用对话服务时  
**用途**：生成角色对话回复（独立于游戏流程）

---

## Prompt修改指南

### 修改原则

1. **保持格式一致性**：所有prompt都使用类似的格式和结构
2. **明确区分表/里**：确保prompt中明确说明哪些信息是"表"（玩家可见），哪些是"里"（隐藏）
3. **提供具体示例**：在关键部分提供具体示例，帮助LLM理解
4. **强调优先级**：使用**加粗**或特殊标记强调重要要求
5. **输出格式明确**：对于需要JSON输出的prompt，明确说明格式要求

### 修改流程

1. 找到对应的prompt位置（参考本文档）
2. 阅读当前prompt内容
3. 理解prompt的用途和上下文
4. 进行修改
5. 测试修改后的效果
6. 更新本文档（如果prompt结构有重大变化）

### 常见修改场景

1. **调整语气和风格**：修改"要求"部分，改变LLM的输出风格
2. **添加新信息**：在prompt中添加新的输入信息
3. **修改输出格式**：调整JSON输出格式或文本格式
4. **优化示例**：更新或添加更具体的示例
5. **强调特定规则**：使用加粗或特殊标记强调重要规则

---

## 总结

系统中主要的LLM调用prompt有：

1. **Agent响应生成**（`services/agent.py:279-342`）：每个角色生成响应
2. **导演评估**（`services/director_evaluator.py:292-399`）：环境分析和决策制定（最重要、最复杂）
3. **响应格式化**（`services/response_formatter.py:100-148`）：格式化响应
4. **摘要生成**（`services/response_formatter.py:288-320`）：生成摘要
5. **一致性检查**（`services/consistency_checker.py:144-181`, `services/question_consistency_checker.py:102-141`）：检查一致性
6. **提问服务**（`services/question_service.py:223-257`）：回答玩家问题
7. **对话服务**（`services/chat_service.py:341-371`）：独立对话服务

其中，**导演评估Prompt**是最重要和最复杂的，包含了环境变化分析和决策制定的完整逻辑。

### 已删除的Prompt

以下prompt已被删除，功能已合并到导演评估中：
- **环境分析Prompt**（`services/environment_analyzer.py`）：已合并到导演评估
- **预期事件生成Prompt**（`services/multi_agent_coordinator.py`）：已合并到导演评估
