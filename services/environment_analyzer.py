"""
环境分析器：使用LLM分析智能体响应，提取环境变化
"""
import json
from typing import Dict, List
from services.chat_service import ChatService
from config import Config


class EnvironmentAnalyzer:
    """环境分析器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.chat_service = ChatService()
    
    def analyze_environment_changes(self, scene_content: str, agent_responses: List[Dict], 
                                   platform: str = None) -> Dict:
        """
        分析智能体响应，提取环境变化
        
        Args:
            scene_content: 当前场景内容
            agent_responses: 所有智能体的响应列表
            platform: API平台
        
        Returns:
            包含环境变化的字典
        """
        if not agent_responses:
            return {
                'scene_changes': {
                    'surface': {},
                    'hidden': {}
                },
                'major_events': []
            }
        
        # 收集所有响应文本
        responses_text = "\n\n".join([
            f"【{resp['character_name']}】\n{resp['response']}"
            for resp in agent_responses
        ])
        
        # 构建分析提示词
        system_prompt = f"""你是一个环境分析助手。请分析智能体的响应，提取环境变化。

【信息来源：当前场景状态】
{scene_content}

【信息来源：智能体响应】
{responses_text}

请分析以上智能体的响应，提取以下信息：

1. **场景变化**（表/里分离）：
   - 表信息（surface）：玩家可见的场景变化
     - **基础信息更新**：如果时间、地点发生变化，请更新：
       - `time`: 当前时间（如："黎明6:30"、"上午8:00"等）
       - `location`: 详细位置信息
         - `region`: 区域（如："绿雾边境小镇"、"遗迹入口"等）
         - `specific_location`: 具体位置（如："公会大厅"、"遗迹入口前"、"商路中段"等）
         - `coordinates`: 坐标/方位（如："小镇中心"、"东北方向3公里"、"商路东侧"等）
         - `environment`: 环境描述（如："石制大厅"、"稀疏林地"、"遗迹入口的石门"等）
     - **当前叙述**：玩家可见的当前场景描述
     - **目标**：当前目标（如果有变化）
     - **资源**：可用资源（如果有变化）
   - 里信息（hidden）：LLM推演用的隐藏信息
     - **最终目标**：隐藏的最终目标（如果有变化）
     - **潜在敌人（隐藏情报）**：隐藏的敌人信息（如果有变化）
     - **风险提示**：隐藏的风险信息（如果有变化）

2. **重大事件**：从响应中提取的重大事件列表

**重要**：
- 如果智能体执行了移动指令，**必须**更新位置信息（location）
- 位置信息要具体，不要只写"移动了"，要写具体到了哪里
- 时间信息如果明显流逝（如移动、战斗等），也要更新

请以JSON格式回复：
{{
    "scene_changes": {{
        "surface": {{
            "time": "更新后的时间（如果有变化）",
            "location": {{
                "region": "区域",
                "specific_location": "具体位置",
                "coordinates": "坐标/方位",
                "environment": "环境描述"
            }},
            "current_narrative": "当前叙述（玩家可见的场景描述）",
            "goal": "当前目标（如果有变化）",
            "resources": "可用资源（如果有变化）"
        }},
        "hidden": {{
            "final_goal": "最终目标（如果有变化）",
            "potential_enemies": "潜在敌人（隐藏情报，如果有变化）",
            "risk_hints": "风险提示（如果有变化）"
        }}
    }},
    "major_events": [
        // 重大事件列表，如："队伍出发前往遗迹"、"到达遗迹入口"、"发现重要线索"等
    ]
}}"""
        
        user_message = "请分析智能体响应，提取环境变化和重大事件。"
        
        platform = platform or self.config.DEFAULT_API_PLATFORM
        
        # 调用LLM分析
        try:
            if platform.lower() == 'deepseek':
                response_text = self.chat_service._call_deepseek_api(
                    [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_message}],
                    operation='environment_analysis'
                )
            elif platform.lower() == 'openai':
                response_text = self.chat_service._call_openai_api(
                    [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_message}],
                    operation='environment_analysis'
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
                    'scene_changes': result.get('scene_changes', {'surface': {}, 'hidden': {}}),
                    'major_events': result.get('major_events', [])
                }
            except json.JSONDecodeError:
                # 如果解析失败，返回空变化
                return {
                    'scene_changes': {
                        'surface': {},
                        'hidden': {}
                    },
                    'major_events': []
                }
        except Exception as e:
            print(f"环境分析失败: {e}")
            return {
                'scene_changes': {
                    'surface': {},
                    'hidden': {}
                },
                'major_events': []
            }

