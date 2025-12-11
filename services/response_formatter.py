"""
响应格式化器：将Agent的JSON响应转换为适合玩家角色的文本
"""
import json
from typing import Dict, List, Optional
from services.chat_service import ChatService
from config import Config


class ResponseFormatter:
    """响应格式化器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.chat_service = ChatService()
    
    def format_responses_for_player(self, agent_responses: List[Dict], player_role: str,
                                   scene_content: str, platform: str = None) -> Dict:
        """
        将智能体响应格式化为适合玩家角色的文本
        
        Args:
            agent_responses: 所有智能体的响应列表（包含JSON格式的response）
            player_role: 玩家扮演的角色
            scene_content: 场景内容
            platform: API平台
        
        Returns:
            格式化后的响应，包含表/里信息
        """
        if not agent_responses:
            return {
                'surface': {
                    'responses': [],
                    'summary': '暂无响应'
                },
                'hidden': {}
            }
        
        # 收集所有响应文本
        responses_text = "\n\n".join([
            f"【{resp['character_name']}】\n{resp['response']}"
            for resp in agent_responses
        ])
        
        # 构建格式化提示词
        system_prompt = f"""你是一个响应格式化助手。请将智能体的响应转换为适合玩家角色的文本。

【信息来源：玩家角色】
玩家扮演的角色：{player_role}

【信息来源：当前场景状态】
{scene_content}

【信息来源：智能体响应（原始JSON格式）】
{responses_text}

请将以上智能体的响应转换为适合玩家角色（{player_role}）的文本描述。

要求：
1. 以玩家角色的视角来描述发生的事件
2. 将智能体的对话和行动自然地融入叙述中
3. 不要直接暴露JSON结构，要转换为流畅的文本
4. 保持角色对话的原汁原味
5. 可以适当添加环境描述，让场景更生动

请以JSON格式回复：
{{
    "formatted_responses": [
        {{
            "character_name": "角色名",
            "formatted_text": "格式化后的文本（从玩家视角描述该角色的响应）"
        }}
    ],
    "summary": "整体摘要（从玩家视角的简要描述）"
}}"""
        
        user_message = f"请将智能体响应格式化为适合玩家角色（{player_role}）的文本。"
        
        platform = platform or self.config.DEFAULT_API_PLATFORM
        
        # 调用LLM格式化
        try:
            if platform.lower() == 'deepseek':
                response_text = self.chat_service._call_deepseek_api(
                    [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_message}],
                    operation='response_formatting'
                )
            elif platform.lower() == 'openai':
                response_text = self.chat_service._call_openai_api(
                    [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_message}],
                    operation='response_formatting'
                )
            else:
                raise ValueError(f"不支持的API平台: {platform}")
        except Exception as e:
            # API调用失败，使用简单格式化
            print(f"响应格式化API调用失败: {e}")
            return self._simple_format(agent_responses)
        
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
            formatted_responses = result.get('formatted_responses', [])
            summary = result.get('summary', '')
            
            return {
                'surface': {
                    'responses': formatted_responses,
                    'summary': summary
                },
                'hidden': {
                    'raw_responses': agent_responses  # 保留原始响应供内部使用
                }
            }
        except json.JSONDecodeError:
            # 如果解析失败，使用简单格式化
            return self._simple_format(agent_responses)
        except Exception as e:
            print(f"响应格式化失败: {e}")
            return self._simple_format(agent_responses)
    
    def _simple_format(self, agent_responses: List[Dict]) -> Dict:
        """简单格式化（fallback）"""
        formatted = []
        for resp in agent_responses:
            formatted.append({
                'character_name': resp['character_name'],
                'formatted_text': resp.get('response', '')
            })
        
        summary = "\n".join([
            f"{resp['character_name']}: {resp.get('response', '')[:50]}..."
            for resp in agent_responses
        ])
        
        return {
            'surface': {
                'responses': formatted,
                'summary': summary
            },
            'hidden': {
                'raw_responses': agent_responses
            }
        }

