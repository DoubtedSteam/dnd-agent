"""
响应聚合器：收集所有智能体响应，分析人物和环境变化
"""
import json
from typing import Dict, List
from config import Config
from services.agent import format_agent_response


class ResponseAggregator:
    """响应聚合器"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def aggregate_responses(self, agent_responses: List[Dict], scene_content: str) -> Dict:
        """
        聚合所有智能体响应，分析变化
        
        Args:
            agent_responses: 所有智能体的响应列表
            scene_content: 当前场景内容
        
        Returns:
            聚合结果，包含表/里信息
        """
        # 收集所有响应
        all_responses = []
        
        for resp in agent_responses:
            if not resp or not isinstance(resp, dict):
                continue
            character_id = resp.get('character_id')
            character_name = resp.get('character_name', '未知')
            response = format_agent_response(resp.get('response', ''))
            
            if not character_id:
                continue
            
            all_responses.append({
                'character_id': character_id,
                'character_name': character_name,
                'response': response
            })
        
        # 分离表/里信息
        surface_responses = []
        hidden_info = {}
        
        for resp in agent_responses:
            if not resp or not isinstance(resp, dict):
                continue
            character_id = resp.get('character_id')
            character_name = resp.get('character_name', '未知')
            response = format_agent_response(resp.get('response', ''))
            hidden = resp.get('hidden', {})
            inner_monologue = hidden.get('inner_monologue', '') if isinstance(hidden, dict) else ''
            
            if not character_id:
                continue
            
            # 表信息：玩家可见的响应
            surface_responses.append({
                'character_name': character_name,
                'response': response
            })
            
            # 里信息：隐藏的内心活动
            if inner_monologue:
                hidden_info[character_id] = {
                    'inner_monologue': inner_monologue
                }
        
        return {
            'surface': {
                'responses': surface_responses,
                'summary': self._generate_surface_summary(surface_responses)
            },
            'hidden': {
                'detailed_info': hidden_info
            }
        }
    
    def _generate_surface_summary(self, responses: List[Dict]) -> str:
        """生成表信息摘要"""
        if not responses:
            return "暂无响应"
        
        summary_parts = []
        for resp in responses:
            if not resp or not isinstance(resp, dict):
                continue
            character_name = resp.get('character_name', '未知')
            response = resp.get('response', '')
            if response:
                summary_parts.append(f"{character_name}: {response[:50]}...")
        
        return "\n".join(summary_parts) if summary_parts else "暂无响应"

