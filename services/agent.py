"""
智能体类：每个角色作为独立的智能体
"""
import json
from typing import Dict, Optional
from services.chat_service import ChatService
from config import Config


def format_agent_response(response_data) -> str:
    """
    格式化Agent响应为文本
    
    Args:
        response_data: response字段，可能是字符串或对象（包含dialogue和action_intent）
    
    Returns:
        格式化后的文本字符串
    """
    if isinstance(response_data, str):
        # 兼容旧格式：如果response是字符串，直接返回
        return response_data
    elif isinstance(response_data, dict):
        # 新格式：response是对象，组合dialogue和action_intent
        dialogue = response_data.get('dialogue', '')
        action_intent = response_data.get('action_intent', '')
        
        parts = []
        if dialogue:
            parts.append(dialogue)
        if action_intent:
            parts.append(action_intent)
        
        return ' '.join(parts) if parts else ''
    else:
        return ''


class Agent:
    """单个智能体，代表一个角色"""
    
    def __init__(self, character_data: Dict, config: Config):
        """
        初始化智能体
        
        Args:
            character_data: 人物卡数据
            config: 配置对象
        """
        self.character_id = character_data['id']
        self.character_name = character_data['name']
        self.description = character_data['description']
        self.attributes = character_data.get('attributes', {})
        self.theme = character_data.get('theme', 'default')
        self.chat_service = ChatService()
        self.config = config
    
    def process_instruction(self, instruction: str, scene_content: str, 
                           platform: str = None, save_step: Optional[str] = None,
                           player_role: str = None, conversation_history: str = None,
                           expected_event: Optional[str] = None) -> Dict:
        """
        处理玩家指令，生成响应
        
        Args:
            instruction: 玩家指令
            scene_content: 场景内容
            platform: API平台
            save_step: 存档步骤
            player_role: 玩家扮演的角色
        
        Returns:
            包含响应和状态变化的字典
        """
        # 构建智能体专用的系统提示词
        system_prompt = self._build_agent_prompt(scene_content, player_role, conversation_history)
        
        # 构建用户消息（包含玩家指令和预期事件）
        event_note = ""
        if expected_event:
            event_note = f"\n【重要：预期事件】在执行指令过程中，如果遇到以下事件，必须立即停止并描述情况：\n{expected_event}\n所有角色应该在同一时刻遇到这个事件并停止。如果队伍在一起行动，要么都到达目标，要么都遇到事件，不能出现部分角色到达而部分角色遇到事件的情况。"
        
        # 确保instruction不为None
        instruction = instruction or ""
        
        user_message = f"""指令：{instruction}{event_note}

要求：
1. 执行指令（可能因环境失败，需说明原因）
2. 描述具体行动过程，不要只说"执行了"
3. **如果遇到预期事件，必须立即停止，描述情况等待玩家**
4. **队伍一致性：如果队伍在一起行动，所有角色应该在同一个时刻停止（要么都到达目标，要么都遇到事件）**
5. 主动观察环境变化（天气/声音/地形等），简洁描述
6. 严格遵循角色说话风格和性格特点，保持语气一致

输出JSON：
{{
    "response": {{
        "dialogue": "角色的语言内容（如果此刻不说话则留空）",
        "action_intent": "角色的肢体动作或行动尝试（不做结果判定）"
    }},
    "hidden": {{
        "inner_monologue": "基于性格的心理活动（用于解释为何做出上述行动，仅导演可见）"
    }}
}}

**注意**: 
- state_changes、attribute_changes、execution_result 由导演评估统一决定，Agent 不需要提供
- Agent 只需提供 response（包含dialogue和action_intent）和 hidden.inner_monologue（心理活动）"""
        
        # 调用LLM生成响应
        platform = platform or self.config.DEFAULT_API_PLATFORM
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            if platform.lower() == 'deepseek':
                response_text = self.chat_service._call_deepseek_api(
                    messages, operation='agent_response', 
                    context={'character_id': self.character_id, 'theme': self.theme}
                )
            elif platform.lower() == 'openai':
                response_text = self.chat_service._call_openai_api(
                    messages, operation='agent_response',
                    context={'character_id': self.character_id, 'theme': self.theme}
                )
            elif platform.lower() == 'aizex':
                response_text = self.chat_service._call_aizex_api(
                    messages, operation='agent_response',
                    context={'character_id': self.character_id, 'theme': self.theme}
                )
            else:
                raise ValueError(f"不支持的API平台: {platform}")
        except Exception as e:
            # API调用失败，返回错误响应
            error_msg = f"API调用失败: {str(e)}"
            print(f"[{self.character_name}] {error_msg}")
            return {
                'character_id': self.character_id,
                'character_name': self.character_name,
                'response': {
                    'dialogue': f"抱歉，我无法处理这个指令。{error_msg}",
                    'action_intent': ''
                },
                'hidden': {
                    'inner_monologue': f'无法处理指令：{error_msg}'
                }
            }
        
        # 解析响应
        try:
            # 清理响应文本：移除推理标记及其内容
            import re
            # 移除各种推理标记及其内容（不区分大小写，支持多行）
            # 移除 <think>...</think> 标记
            response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL | re.IGNORECASE)
            # 移除 <think>...</think> 标记
            response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL | re.IGNORECASE)
            # 移除单独的未闭合标记（如果没有闭合标签）
            response_text = re.sub(r'<(think|redacted_reasoning)>.*?$', '', response_text, flags=re.DOTALL | re.IGNORECASE | re.MULTILINE)
            # 移除 **Thinking about...** 这样的标记
            response_text = re.sub(r'\*\*Thinking about.*?\*\*', '', response_text, flags=re.DOTALL | re.IGNORECASE)
            
            # 尝试提取JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            result = json.loads(response_text)
            
            # 处理response字段（可能是字符串或对象）
            response_data = result.get('response', {})
            if isinstance(response_data, str):
                # 兼容旧格式：如果response是字符串，转换为新格式
                response_obj = {
                    'dialogue': response_data,
                    'action_intent': ''
                }
            elif isinstance(response_data, dict):
                # 新格式：response是对象，只提取存在的字段
                response_obj = {
                    'dialogue': response_data.get('dialogue', ''),
                    'action_intent': response_data.get('action_intent', '')
                }
            else:
                response_obj = {
                    'dialogue': '',
                    'action_intent': ''
                }
            
            # 处理hidden字段，只提取存在的字段
            hidden_data = result.get('hidden', {})
            if isinstance(hidden_data, dict):
                hidden_obj = {
                    'inner_monologue': hidden_data.get('inner_monologue', '')
                }
            else:
                hidden_obj = {
                    'inner_monologue': ''
                }
            
            return {
                'character_id': self.character_id,
                'character_name': self.character_name,
                'response': response_obj,
                'hidden': hidden_obj
            }
        except json.JSONDecodeError:
            # 如果解析失败，清理响应文本后返回
            import re
            # 再次清理，确保没有推理标记
            cleaned_response = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL | re.IGNORECASE)
            cleaned_response = re.sub(r'<think>.*?</think>', '', cleaned_response, flags=re.DOTALL | re.IGNORECASE)
            cleaned_response = re.sub(r'<(think|redacted_reasoning)>.*?$', '', cleaned_response, flags=re.DOTALL | re.IGNORECASE | re.MULTILINE)
            cleaned_response = re.sub(r'\*\*Thinking about.*?\*\*', '', cleaned_response, flags=re.DOTALL | re.IGNORECASE)
            cleaned_response = cleaned_response.strip()
            
            return {
                'character_id': self.character_id,
                'character_name': self.character_name,
                'response': {
                    'dialogue': cleaned_response,
                    'action_intent': ''
                },
                'hidden': {
                    'inner_monologue': ''
                }
            }
    
    def _build_agent_prompt(self, scene_content: str, player_role: str = None, 
                           conversation_history: str = None) -> str:
        """构建智能体专用的系统提示词"""
        attr_guide = self.chat_service._load_attr_guide(self.theme)
        
        # 从场景中提取玩家角色信息
        if not player_role and "玩家角色" in scene_content:
            # 尝试从场景中提取玩家角色
            lines = scene_content.split('\n')
            for line in lines:
                if "玩家角色" in line or "玩家扮演" in line:
                    player_role = line.split('：')[-1].split('，')[0].strip() if '：' in line else None
                    break
        
        player_role_info = ""
        if player_role:
            player_role_info = f"\n【重要】玩家角色：{player_role}\n- 玩家指令来自玩家角色，你需要理解玩家角色的身份和立场\n- 你的响应应该考虑玩家角色的视角和需求\n"
        
        history_info = ""
        if conversation_history:
            history_info = f"\n{conversation_history}\n"
        
        # 提取关键的性格和说话风格信息
        traits = self.attributes.get('traits', [])
        speaking_style = self.attributes.get('speaking_style', '')
        background = self.attributes.get('background', '')
        
        traits_text = f"性格特点：{', '.join(traits) if isinstance(traits, list) else traits}" if traits else ""
        speaking_style_text = f"说话风格：{speaking_style}" if speaking_style else ""
        background_text = f"背景：{background}" if background else ""
        
        # 精简角色特征部分
        style_key = ""
        if traits or speaking_style:
            style_parts = []
            if traits:
                style_parts.append(f"性格：{', '.join(traits) if isinstance(traits, list) else traits}")
            if speaking_style:
                style_parts.append(f"说话：{speaking_style}")
            style_key = f"\n【核心特征】{' | '.join(style_parts)}\n- 严格遵循说话风格和性格，保持语气一致，禁止通用化语言\n"
        
        prompt = f"""# Role: 跑团角色智能体 (TRPG Character Agent)

**角色名称**: {self.character_name}

---

### 1. 深度角色设定 (Character Profile)

**【核心档案】**
- 描述: {self.description}
- 当前状态/属性: {json.dumps(self.attributes, ensure_ascii=False)}
{style_key}

**【扮演指南】**
{attr_guide}
- 语言风格：请严格模仿角色的口癖、用词习惯和语调。
- 思维逻辑：基于角色的智力、性格和过往经历来决策，而非基于最优解。

---

### 2. 当前情境 (Current Context)

**【环境与事件】**
{scene_content}

**【在场人员】**
{player_role_info}

**【剧情记忆】**
{history_info}

---

### 3. 核心指令 (Prime Directives)

1.  **绝对的角色沉浸**: 你不仅是文本生成器，你是 {self.character_name} 本人。任何回复必须符合角色人设，禁止跳出角色（OOC）。
2.  **行动意图边界 (关键)**: 
    - 你**只能**描述你“试图”做的动作或你说的台词。
    - **严禁**描述行动的后果、环境的反馈或其他角色的反应。
    - *错误示例*: "我一拳打倒了守卫。" (描述了结果)
    - *正确示例*: "我握紧拳头，瞄准守卫的下巴挥去。" (仅描述意图)
3.  **信息分层**:
    - **Surface (表层)**: 玩家和其他角色能看到、听到的内容。
    - **Hidden (里层)**: 你的真实心理活动、战术盘算或对他人的隐秘看法。
4.  **响应限制**: 保持简练，单次响应控制在2-3句以内，等待其他玩家或导演的反馈。

---

### 4. 输出协议 (Output Protocol)

请输出严格的 JSON 格式：

{{
    "response": {{
        "dialogue": "角色的语言内容（如果此刻不说话则留空）",
        "action_intent": "角色的肢体动作或行动尝试（不做结果判定）"
    }},
    "hidden": {{
        "inner_monologue": "基于性格的心理活动（用于解释为何做出上述行动，仅导演可见）",
    }}
}}

**系统强调**: 不要自行生成 state_changes 或 execution_result，那是导演（Director）的工作。
"""
        return prompt

