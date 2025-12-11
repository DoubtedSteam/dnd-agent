"""
响应聚合器：收集所有智能体响应，分析人物和环境变化
"""
import json
from typing import Dict, List
from config import Config


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
        all_state_changes = {}
        all_attribute_changes = {}
        
        for resp in agent_responses:
            all_responses.append({
                'character_id': resp['character_id'],
                'character_name': resp['character_name'],
                'response': resp['response']
            })
            
            if resp.get('state_changes'):
                all_state_changes[resp['character_id']] = resp['state_changes']
            
            if resp.get('attribute_changes'):
                all_attribute_changes[resp['character_id']] = resp['attribute_changes']
        
        # 分离表/里信息
        surface_responses = []
        hidden_info = {}
        
        for resp in agent_responses:
            # 表信息：玩家可见的响应
            surface_responses.append({
                'character_name': resp['character_name'],
                'response': resp['response']
            })
            
            # 里信息：隐藏的状态变化和执行结果
            if resp.get('state_changes') or resp.get('execution_result'):
                hidden_info[resp['character_id']] = {
                    'state_changes': resp.get('state_changes', {}),
                    'attribute_changes': resp.get('attribute_changes', {}),
                    'execution_result': resp.get('execution_result', {})
                }
        
        return {
            'surface': {
                'responses': surface_responses,
                'summary': self._generate_surface_summary(surface_responses)
            },
            'hidden': {
                'state_changes': all_state_changes,
                'attribute_changes': all_attribute_changes,
                'detailed_info': hidden_info
            }
        }
    
    def _generate_surface_summary(self, responses: List[Dict]) -> str:
        """生成表信息摘要"""
        if not responses:
            return "暂无响应"
        
        summary_parts = []
        for resp in responses:
            summary_parts.append(f"{resp['character_name']}: {resp['response'][:50]}...")
        
        return "\n".join(summary_parts)

