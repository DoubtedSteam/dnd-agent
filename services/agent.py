"""
智能体类：每个角色作为独立的智能体
"""
import json
from typing import Dict, Optional
from services.chat_service import ChatService
from config import Config


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
                           player_role: str = None, conversation_history: str = None) -> Dict:
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
        
        # 构建用户消息（包含玩家指令）
        user_message = f"""玩家指令：{instruction}

【重要】你必须执行玩家指令，但要注意：
1. **指令必须执行**：玩家指令是必须执行的行动，不是建议或讨论
   - 例如："爬上去" 意味着你要执行"爬"这个动作，而不是讨论是否要爬
   - 例如："移动到遗迹入口" 意味着你要执行"移动"这个动作
   
2. **执行可能失败**：由于环境因素，指令执行可能失败
   - 例如：爬墙时可能因为墙壁太滑而失败
   - 例如：移动时可能因为障碍物而无法到达
   - 如果执行失败，要在响应中明确说明失败的原因和结果
   
3. **执行过程要具体**：描述你如何执行指令
   - 不要只说"好的，我执行了"，要描述具体的行动过程
   - 例如："我开始向上攀爬，但墙壁太滑，尝试了几次后滑了下来"
   - 例如："我向遗迹入口方向移动，但前方有深沟阻挡，无法直接通过"

请根据你的角色设定、当前场景状态和玩家指令，生成以下内容：

1. **响应**：你对玩家指令的回应和行动过程
   - 必须执行指令，描述具体的行动
   - 如果执行失败，说明失败的原因和结果
   - 如果执行成功，说明成功的结果
   
2. **状态变化**：你的状态可能发生的变化（JSON格式）
   - 如果状态有变化，请提供更新后的 state.surface.perceived_state
   - 如果状态有变化，请提供更新后的 state.hidden.observer_state
   - 如果状态有变化，请提供更新后的 state.hidden.inner_monologue
   - 其他属性变化（如 vitals、equipment 等）
   - 如果执行失败，可能影响体力、生命值等属性

请以JSON格式回复：
{{
    "response": "你的响应内容（必须包含具体的行动过程和结果）",
    "state_changes": {{
        "surface": {{
            "perceived_state": "更新后的直观状态（如果有变化）"
        }},
        "hidden": {{
            "observer_state": "更新后的客观观察状态（如果有变化）",
            "inner_monologue": "更新后的内心独白（如果有变化）"
        }}
    }},
    "attribute_changes": {{
        // 其他属性变化，如 vitals: {{"hp": 180, "mp": 40, "stamina": 120}}
        // 如果执行失败，可能消耗体力或受到伤害
    }},
    "execution_result": {{
        "success": true/false,  // 指令是否成功执行
        "failure_reason": "失败原因（如果失败）",  // 可选
        "actual_outcome": "实际结果描述"  // 实际发生了什么
    }}
}}"""
        
        # 调用LLM生成响应
        platform = platform or self.config.DEFAULT_API_PLATFORM
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
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
        else:
            raise ValueError(f"不支持的API平台: {platform}")
        
        # 解析响应
        try:
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
            return {
                'character_id': self.character_id,
                'character_name': self.character_name,
                'response': result.get('response', ''),
                'state_changes': result.get('state_changes', {}),
                'attribute_changes': result.get('attribute_changes', {}),
                'execution_result': result.get('execution_result', {
                    'success': True,
                    'actual_outcome': '指令已执行'
                })
            }
        except json.JSONDecodeError:
            # 如果解析失败，返回原始响应
            return {
                'character_id': self.character_id,
                'character_name': self.character_name,
                'response': response_text,
                'state_changes': {},
                'attribute_changes': {}
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
        
        prompt = f"""你是一个角色扮演智能体。你代表角色：{self.character_name}

【信息来源：人物卡配置】
=== 人物设定 ===
人物描述：
{self.description}

人物属性（结构化设定，仅用于参考，不要机械复述）：
{json.dumps(self.attributes, ensure_ascii=False, indent=2)}

【信息来源：CHARACTER_ATTRIBUTES.md - 属性字段含义说明】
{attr_guide}

【信息来源：SCENE.md - 场景设定】
=== 场景设定 ===
{scene_content}
{player_role_info}
{history_info}
=== 重要要求 ===
1. 你是一个独立的智能体，需要根据你的角色设定、当前场景和玩家指令做出反应
2. **玩家角色信息**：请特别注意场景中提到的玩家角色，理解玩家指令的上下文和意图
3. 你的响应应该符合角色的性格、背景和说话风格
4. 你需要考虑场景中的重大事件和当前状态
5. 你的状态可能会因为指令和场景变化而改变
6. 注意区分表/里信息：
   - 表信息（surface）：玩家可见的直观状态
   - 里信息（hidden）：隐藏的推演信息，帮助你理解角色的真实想法
7. 只有在状态确实发生变化时才提供 state_changes，否则可以省略
"""
        return prompt

