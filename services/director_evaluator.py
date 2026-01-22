"""
导演评估器：LLM作为导演评估当前状态，决定事件触发和场景转换
"""
import json
import re
from typing import Dict, Optional
from config import Config
from services.chat_service import ChatService
from services.agent import format_agent_response


class DirectorEvaluator:
    """LLM导演评估器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.chat_service = ChatService()
    
    def evaluate_as_director(self, context: Dict, platform: str = None) -> Dict:
        """
        LLM作为导演评估当前状态，这是一个LLM调用，包含两部分工作：
        1. 环境变化分析（第一部分）：分析Agent响应对环境的影响，以及Agent响应的实际执行情况
        2. 决策制定（第二部分）：基于环境变化分析结果，决定事件触发、怪物出现和场景/房间转换
        
        Args:
            context: 导演上下文，包含：
                - current_scene: 当前场景ID
                - current_room: 当前房间ID（可选）
                - scene_script: 场景剧本
                - room_script: 房间剧本（可选）
                - potential_events: 潜在事件列表
                - potential_monsters: 潜在怪物列表
                - connected_targets: 可连接的目标列表
                - scene_network: 场景连接网络
                - character_states: 角色状态
                - player_instruction: 玩家指令
                - story_overview: 故事总览
                - agent_responses: Agent响应列表
                - scene_content: 当前场景内容（用于环境变化分析）
        
        Returns:
            包含两部分结果的字典：
                - environment_analysis: 环境变化分析结果
                    - updated_scene_description: 更新后的场景描述
                    - scene_state_changes: 场景状态变化
                    - agent_execution_results: Agent执行结果列表
                - director_decision: 导演决策结果
                    - trigger_event: 事件ID或None
                    - event_description: 事件描述
                    - appear_monster: 怪物ID/名称列表（数组），可能包含多个怪物
                    - monster_description: 所有登场怪物的出场画面描述
                    - transition_target: 目标场景或房间ID
                    - transition_type: "scene" 或 "room"
                    - elapsed_time: 消耗的游戏内时间（分钟）
                    - reasoning: 决策理由（隐藏）
        """
        # 构建导演Prompt
        prompt = self._build_director_prompt(context)
        
        # 调用LLM（这是一个LLM调用，包含两部分工作）
        platform = platform or self.config.DEFAULT_API_PLATFORM
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "请作为导演，先完成环境变化分析，然后基于分析结果做出决策。"}
        ]
        context_dict = {'theme': context.get('current_scene', 'unknown')}
        
        try:
            if platform.lower() == 'deepseek':
                response = self.chat_service._call_deepseek_api(
                    messages,
                    operation='director_evaluate',
                    context=context_dict
                )
            elif platform.lower() == 'openai':
                response = self.chat_service._call_openai_api(
                    messages,
                    operation='director_evaluate',
                    context=context_dict
                )
            elif platform.lower() == 'aizex':
                response = self.chat_service._call_aizex_api(
                    messages,
                    operation='director_evaluate',
                    context=context_dict
                )
            else:
                raise ValueError(f"不支持的API平台: {platform}")
            
            # 解析响应（包含environment_analysis和director_decision两部分）
            result = self._parse_director_response(response)
            return result
        except Exception as e:
            print(f"导演评估失败: {e}")
            import traceback
            traceback.print_exc()
            # 返回默认结构
            return {
                "environment_analysis": {
                    "updated_scene_description": "",
                    "scene_state_changes": {},
                    "agent_execution_results": []
                },
                "director_decision": {
                    "trigger_event": None,
                    "event_description": "",
                    "appear_monster": None,
                    "monster_description": "",
                    "transition_target": None,
                    "transition_type": "scene",
                    "elapsed_time": 1.0,
                    "reasoning": f"评估失败: {str(e)}"
                }
            }
    
    def _build_director_prompt(self, context: Dict) -> str:
        """构建导演Prompt"""
        current_scene = context.get("current_scene", "未知")
        current_room = context.get("current_room")
        player_instruction = context.get("player_instruction", "")
        character_states = context.get("character_states", {})
        scene_state = context.get("scene_state", {})
        triggered_events = context.get("triggered_events", [])
        game_time = context.get("game_time", {})
        enter_time = context.get("enter_time")
        agent_responses = context.get("agent_responses", [])
        
        # 获取场景/房间描述（表部分）
        scene_script = context.get("scene_script", {})
        room_script = context.get("room_script")
        
        surface_desc = ""
        if room_script:
            surface_desc = room_script.get("surface", {}).get("description", "")
        else:
            surface_desc = scene_script.get("surface", {}).get("description", "")
        
        # 获取潜在事件和怪物（里部分）
        potential_events = context.get("potential_events", [])
        potential_monsters = context.get("potential_monsters", [])
        connected_targets = context.get("connected_targets", [])
        
        # 构建事件列表文本（区分核心事件和随机事件，标记已触发状态）
        core_events_text = ""
        random_events_text = ""
        
        for i, event in enumerate(potential_events, 1):
            event_id = event.get('id', '')
            event_type = event.get('type', 'random')  # 从JSON加载的事件使用type字段
            if not event_type:
                event_type = event.get('event_type', 'random')  # 兼容旧格式
            event_name = event.get('name', '未知')
            event_description = event.get('description', '')
            trigger_conditions = event.get('trigger_conditions', {})
            
            # 检查事件是否已触发
            is_triggered = event_id in triggered_events if event_id else False
            status_mark = " [已触发]" if is_triggered else " [未触发]"
            
            event_info = f"\n事件{i}: {event_name} (ID: {event_id}){status_mark}"
            if event_type == "core":
                event_info += " [核心事件]"
            else:
                event_info += " [随机事件]"
            
            # 添加简单介绍
            if event_description:
                event_info += f"\n  简介: {event_description}"
            
            # 添加触发条件（简化显示）
            if trigger_conditions:
                conditions_summary = []
                if trigger_conditions.get("time_condition"):
                    conditions_summary.append(f"时间: {trigger_conditions['time_condition']}")
                if trigger_conditions.get("behavior_condition"):
                    conditions_summary.append(f"行为: {trigger_conditions['behavior_condition'][:50]}...")
                if trigger_conditions.get("state_condition") and trigger_conditions.get("state_condition") != "无特殊要求":
                    conditions_summary.append(f"状态: {trigger_conditions['state_condition']}")
                if trigger_conditions.get("random_factor"):
                    conditions_summary.append(f"随机: {trigger_conditions['random_factor']}")
                
                if conditions_summary:
                    event_info += f"\n  触发条件: {' | '.join(conditions_summary)}"
            
            # 添加描述模板（简要）
            description_template = event.get('description_template', '')
            if description_template:
                event_info += f"\n  描述预览: {description_template[:100]}..."
            
            if event_type == "core":
                core_events_text += event_info
            else:
                random_events_text += event_info
        
        events_text = ""
        if core_events_text:
            events_text += "\n【核心事件】（可以转换状态和推进剧本阶段）:"
            events_text += core_events_text
        if random_events_text:
            events_text += "\n【随机事件】（如遭遇战、发现财宝等，不触发场景转换）:"
            events_text += random_events_text
        
        # 构建怪物列表文本（从怪物卡加载）
        monsters_text = ""
        for i, monster in enumerate(potential_monsters, 1):
            monster_id = monster.get('id', '未知')
            monster_name = monster.get('name', '未知')
            monster_type = monster.get('type', '')
            monster_level = monster.get('level', '')
            monster_desc = monster.get('description', '')
            attributes = monster.get('attributes', {})
            appearance_conditions = monster.get('appearance_conditions', {})
            battle_template = monster.get('battle_description_template', '')
            battle_effects = monster.get('battle_effects', {})
            director_hints = monster.get('director_hints', {})
            
            monsters_text += f"\n怪物{i}: {monster_name} (ID: {monster_id})\n"
            monsters_text += f"  类型: {monster_type}\n"
            monsters_text += f"  等级/难度: {monster_level}\n"
            monsters_text += f"  描述: {monster_desc}\n"
            if attributes:
                monsters_text += f"  属性: HP={attributes.get('hp', 'N/A')}, 攻击={attributes.get('attack', 'N/A')}, 防御={attributes.get('defense', 'N/A')}\n"
                if attributes.get('special_abilities'):
                    monsters_text += f"  特殊能力: {', '.join(attributes.get('special_abilities', []))}\n"
            if appearance_conditions:
                monsters_text += f"  出现条件: {json.dumps(appearance_conditions, ensure_ascii=False)}\n"
            if battle_template:
                monsters_text += f"  战斗描述模板: {battle_template}\n"
            if battle_effects:
                monsters_text += f"  战斗影响: {json.dumps(battle_effects, ensure_ascii=False)}\n"
            if director_hints:
                monsters_text += f"  导演提示: {json.dumps(director_hints, ensure_ascii=False)}\n"
        
        # 构建可连接目标列表文本
        targets_text = ""
        for target in connected_targets:
            target_type = target.get("type", "scene")
            target_id = target.get("target", "")
            description = target.get("description", "")
            trigger_events = target.get("trigger_events", [])
            prerequisite = target.get("prerequisite")
            
            targets_text += f"\n- {target_id} ({target_type})"
            if description:
                targets_text += f" - {description}"
            if trigger_events:
                targets_text += f" [触发事件: {', '.join(trigger_events)}]"
            if prerequisite:
                targets_text += f" [前置条件: {prerequisite}]"
        
        # 构建场景状态文本
        scene_state_text = f"场景ID: {current_scene}"
        if current_room:
            scene_state_text += f", 房间ID: {current_room}"
        if scene_state.get("state_changes"):
            state_changes = scene_state.get("state_changes", {})
            # 排除enter_time，单独显示
            filtered_changes = {k: v for k, v in state_changes.items() if k != "enter_time"}
            if filtered_changes:
                scene_state_text += f"\n状态变化: {json.dumps(filtered_changes, ensure_ascii=False)}"
        
        # 构建时间信息文本
        time_info_text = ""
        if game_time:
            game_time_obj = game_time.get("game_time", {})
            if game_time_obj:
                day = game_time_obj.get("day", 1)
                hour = game_time_obj.get("hour", 12)
                minute = game_time_obj.get("minute", 0)
                time_info_text = f"当前游戏时间: 第{day}天 {hour:02d}:{minute:02d}"
        
        # 构建进入时间信息文本
        enter_time_text = ""
        if enter_time is not None:
            # enter_time是秒数，转换为分钟
            enter_minutes = enter_time / 60.0
            current_elapsed = game_time.get("elapsed_time", 0) if game_time else 0
            current_minutes = current_elapsed / 60.0
            stay_minutes = current_minutes - enter_minutes
            enter_time_text = f"进入当前场景/房间时间: {enter_minutes:.1f}分钟前（游戏内时间）\n"
            enter_time_text += f"在当前场景/房间停留时间: {stay_minutes:.1f}分钟（游戏内时间）"
        
        # 构建事件状态文本
        event_state_text = f"已触发事件数: {len(triggered_events)}"
        if triggered_events:
            event_state_text += f"\n已触发事件ID: {', '.join(triggered_events)}"
        
        # 获取场景内容（用于环境变化分析）
        scene_content = context.get("scene_content", "")
        
        # 构建Agent响应文本（用于环境变化分析和决策制定）
        agent_responses_text = ""
        if agent_responses:
            agent_responses_text = "\n【重要角色的想法/决策】**（最重要，用于环境变化分析和决策制定）**\n"
            agent_responses_text += "**注意**：只有重要角色会生成Agent响应。环境NPC（如村民、路人等）的反应由你在环境变化分析中处理。\n"
            for i, resp in enumerate(agent_responses, 1):
                character_id = resp.get("character_id", "")
                character_name = resp.get("character_name", "未知")
                response = format_agent_response(resp.get("response", ""))
                hidden = resp.get("hidden", {})
                inner_monologue = hidden.get("inner_monologue", "") if isinstance(hidden, dict) else ""
                
                agent_responses_text += f"\n重要角色{i}: {character_name} (ID: {character_id})\n"
                agent_responses_text += f"  响应: {response}\n"
                if inner_monologue:
                    agent_responses_text += f"  内心活动: {inner_monologue}\n"
        else:
            agent_responses_text = "\n【重要角色的想法/决策】: 暂无重要角色响应\n"
            agent_responses_text += "**注意**：如果没有重要角色，环境NPC（如村民、路人等）的反应由你在环境变化分析中处理。\n"
        
        prompt = f"""# Role: 游戏剧情导演 (Game Director)

你负责推进游戏剧情，处理环境变化并制定游戏进程决策。
**核心指令：这是一个单次 LLM 调用，你必须严格按照顺序完成两个阶段的任务：【阶段一：多角色判定与模拟】 -> 【阶段二：全局决策】。**

---

### 1. 输入上下文 (Context)

**【当前场景状态】**
{scene_state_text}
**【时间信息】**
{time_info_text} | {enter_time_text}
**【事件状态】**
{event_state_text}

**【玩家指令】**
{player_instruction}

**【Agent 响应数据 (多角色列表)】**
*注意：这里包含**一个或多个** Agent 的响应。每个响应包含 `dialogue` (事实) 和 `action_intent` (待判定的尝试)。*
{agent_responses_text}

**【场景描述 (玩家可见)】**
{surface_desc}
**【角色状态】**
{json.dumps(character_states, ensure_ascii=False, indent=2)}

**【隐藏信息 (仅导演可见)】**
- **可能事件列表**: {events_text}
- **潜在怪物列表**: {monsters_text}
- **可连接目标**: {targets_text}

---

### 2. 任务流程 (Workflow)

请在同一个 JSON 输出中，依次完成以下两个阶段的思考与生成：

#### 阶段一：环境变化分析 (Environment Analysis)
**目标**：遍历处理**所有** Agent 的行为结果，并更新环境描述。

1.  **多角色动作执行判定 (Batch Adjudication)**：
    * **必须遍历列表中的每一个 Agent**，不要遗漏。
    * 读取每个 Agent 的 `action_intent`。
    * **判定逻辑**：根据环境限制（如锁、障碍、敌人数量）判定 `success` (true/false)。
    * **填写 output**：在 `agent_execution_results` 数组中为**每一个** Agent 生成对应的结果对象。
2.  **场景描述重绘**:
    * 更新 `updated_scene_description`。
    * **综合叙事**：必须将**所有** Agent 的对话和动作结果融合在一起，形成一段连贯的群像描写。

#### 阶段二：决策制定 (Director Decision)
**目标**：基于全局状态，决定唯一的下一步流向。

**A. 意图与阻断检查**
    * 检查**任意** Agent 是否表达了移动/转场意图。
    * **逻辑阻断**：如果转场需要前置条件（如“全队集合”或“开门”），且相关动作在阶段一中失败，则**阻止转场**（`transition_target: null`）。

**B. 优先级规则 (事件互斥逻辑)**
    * **规则 1 (单事件触发 - 最高优先级)**：检查 `【可能事件列表】`。
        * **唯一性原则**：即使满足多个事件的条件，**同时也只能触发一个事件**。
        * **筛选标准**：优先选择剧情优先级最高、或与当前玩家行为最相关的**这一个**事件 ID 填入 `trigger_event`。
    * **规则 2 (转场)**：如果没有触发事件，且意图明确、地点可达、动作判定成功，填入 `transition_target`。
    * **规则 3 (原地)**：以上皆不满足，保持在当前场景。

**C. 怪物生成 (多实体支持)**
    * 检查 `【潜在怪物列表】`。
    * 如果剧情需要战斗（如遭遇埋伏、进入巢穴），可以从列表中选择**一个或多个**怪物。
    * *示例*：可以同时选择 "Goblin_Archer" 和 "Goblin_Warrior" 组成混合编队。
    * 将选中的所有怪物 ID/名称填入 `appear_monster` 列表。

---

### 3. 输出格式 (Output Format)

必须输出为严格的 JSON 格式，`appear_monster` 必须为列表。

```json
{{
  "environment_analysis": {{
    "updated_scene_description": "融合了多角色对话、多动作判定结果和NPC反应的完整群像剧情描述",
    "scene_state_changes": {{
      "location": "当前位置",
      "time": "时间变化描述，无变化则为 null",
      "weather": "天气变化描述，无变化则为 null"
    }},
    "agent_execution_results": [
      {{
        "character_id": "角色ID_1",
        "character_name": "角色名_1",
        "execution_result": {{
          "success": true,
          "failure_reason": "失败原因，成功则为 null",
          "actual_outcome": "动作的实际结果描述"
        }}
      }},
      ...可能有多个Agent响应
    ]
  }},
  "director_decision": {{
    "trigger_event": "唯一的事件ID 或 null (严格互斥)",
    "event_description": "事件描述文本",
    "appear_monster": ["怪物ID_1", "怪物ID_2", ...可能有多个怪物], 
    "monster_description": "描述所有登场怪物的出场画面（如：一只巨魔撞破大门，身后跟着两只狂叫的地精）",
    "transition_target": "目标场景ID 或 null",
    "transition_type": "scene 或 room",
    "elapsed_time": 5.0,
    "reasoning": "决策链思维：多角色动作判定 -> 事件互斥筛选 -> 怪物编队选择 -> 最终决定"
  }}
}}
"""
        return prompt
    
    def _parse_director_response(self, response: str) -> Dict:
        """解析导演响应（包含environment_analysis和director_decision两部分）"""
        # 清理响应文本
        response_text = response.strip()
        
        # 尝试提取JSON
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        
        # 尝试提取JSON对象
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)
        
        try:
            result = json.loads(response_text)
            
            # 确保包含environment_analysis和director_decision两部分
            default_result = {
                "environment_analysis": {
                    "updated_scene_description": "",
                    "scene_state_changes": {},
                    "agent_execution_results": []
                },
                "director_decision": {
                    "trigger_event": None,
                    "event_description": "",
                    "appear_monster": [],
                    "monster_description": "",
                    "transition_target": None,
                    "transition_type": "scene",
                    "elapsed_time": 1.0,
                    "reasoning": ""
                }
            }
            
            # 如果返回格式是旧的（只有director_decision），转换为新格式
            if "environment_analysis" not in result and "director_decision" not in result:
                # 旧格式，只有决策部分
                old_decision = result
                result = {
                    "environment_analysis": default_result["environment_analysis"],
                    "director_decision": {}
                }
                # 将旧格式的字段迁移到director_decision
                for key in default_result["director_decision"]:
                    result["director_decision"][key] = old_decision.get(key, default_result["director_decision"][key])
            elif "environment_analysis" not in result:
                result["environment_analysis"] = default_result["environment_analysis"]
            elif "director_decision" not in result:
                result["director_decision"] = default_result["director_decision"]
            
            # 确保environment_analysis的所有字段存在
            for key in default_result["environment_analysis"]:
                if key not in result["environment_analysis"]:
                    result["environment_analysis"][key] = default_result["environment_analysis"][key]
            
            # 确保director_decision的所有字段存在
            for key in default_result["director_decision"]:
                if key not in result["director_decision"]:
                    result["director_decision"][key] = default_result["director_decision"][key]
            
            # 处理null字符串和空值
            if result["director_decision"].get("trigger_event") == "null" or result["director_decision"].get("trigger_event") == "":
                result["director_decision"]["trigger_event"] = None
            if result["director_decision"].get("transition_target") == "null" or result["director_decision"].get("transition_target") == "":
                result["director_decision"]["transition_target"] = None
            
            # 处理appear_monster：兼容旧格式（字符串）和新格式（数组）
            appear_monster = result["director_decision"].get("appear_monster")
            if appear_monster is None or appear_monster == "null" or appear_monster == "":
                result["director_decision"]["appear_monster"] = []
            elif isinstance(appear_monster, str):
                # 旧格式：字符串，转换为数组
                result["director_decision"]["appear_monster"] = [appear_monster] if appear_monster else []
            elif not isinstance(appear_monster, list):
                # 如果不是列表，转换为列表
                result["director_decision"]["appear_monster"] = [appear_monster] if appear_monster else []
            
            # 确保elapsed_time是数字
            if not isinstance(result["director_decision"].get("elapsed_time"), (int, float)):
                result["director_decision"]["elapsed_time"] = 1.0
            
            return result
        except json.JSONDecodeError as e:
            print(f"解析导演响应失败: {e}")
            print(f"响应内容: {response_text[:500]}")
            return {
                "environment_analysis": {
                    "updated_scene_description": "",
                    "scene_state_changes": {},
                    "agent_execution_results": []
                },
                "director_decision": {
                    "trigger_event": None,
                    "event_description": "",
                    "appear_monster": [],
                    "monster_description": "",
                    "transition_target": None,
                    "transition_type": "scene",
                    "elapsed_time": 1.0,
                    "reasoning": f"解析失败: {str(e)}"
                }
            }

