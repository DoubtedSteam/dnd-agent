"""
Token消耗统计服务
"""
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict


class TokenTracker:
    """Token消耗统计器"""
    
    def __init__(self):
        self.calls: List[Dict] = []
        self.session_start = datetime.now()
    
    def record_call(self, platform: str, model: str, usage: Dict, 
                   operation: str = "unknown", context: Dict = None):
        """
        记录一次API调用
        
        Args:
            platform: API平台（deepseek/openai）
            model: 使用的模型
            usage: API返回的usage信息（包含token数）
            operation: 操作类型（chat/consistency_check/question/environment_analysis等）
            context: 上下文信息（如theme, character_id等）
        """
        if not usage:
            return
        
        call_record = {
            'timestamp': datetime.now().isoformat(),
            'platform': platform,
            'model': model,
            'operation': operation,
            'context': context or {},
            'input_tokens': usage.get('prompt_tokens', 0),
            'output_tokens': usage.get('completion_tokens', 0),
            'total_tokens': usage.get('total_tokens', 0)
        }
        
        self.calls.append(call_record)
    
    def get_session_stats(self) -> Dict:
        """
        获取当前会话的统计信息
        
        Returns:
            统计信息字典
        """
        if not self.calls:
            return {
                'total_calls': 0,
                'total_tokens': 0,
                'total_input_tokens': 0,
                'total_output_tokens': 0,
                'by_platform': {},
                'by_operation': {},
                'session_duration': 0
            }
        
        total_tokens = sum(c['total_tokens'] for c in self.calls)
        total_input = sum(c['input_tokens'] for c in self.calls)
        total_output = sum(c['output_tokens'] for c in self.calls)
        
        by_platform = defaultdict(lambda: {'calls': 0, 'tokens': 0})
        by_operation = defaultdict(lambda: {'calls': 0, 'tokens': 0})
        
        for call in self.calls:
            platform = call['platform']
            operation = call['operation']
            
            by_platform[platform]['calls'] += 1
            by_platform[platform]['tokens'] += call['total_tokens']
            
            by_operation[operation]['calls'] += 1
            by_operation[operation]['tokens'] += call['total_tokens']
        
        session_duration = (datetime.now() - self.session_start).total_seconds()
        
        return {
            'total_calls': len(self.calls),
            'total_tokens': total_tokens,
            'total_input_tokens': total_input,
            'total_output_tokens': total_output,
            'by_platform': dict(by_platform),
            'by_operation': dict(by_operation),
            'session_duration': session_duration,
            'session_start': self.session_start.isoformat()
        }
    
    def reset(self):
        """重置统计"""
        self.calls.clear()
        self.session_start = datetime.now()
    
    def get_recent_calls(self, limit: int = 10) -> List[Dict]:
        """获取最近的调用记录"""
        return self.calls[-limit:]


# 全局实例
token_tracker = TokenTracker()

