"""
ResponseAggregator 单元测试
"""
import unittest
from services.response_aggregator import ResponseAggregator
from config import Config


class TestResponseAggregator(unittest.TestCase):
    """ResponseAggregator 类测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = Config()
        self.aggregator = ResponseAggregator(self.config)
    
    def test_aggregate_responses_basic(self):
        """测试基本响应聚合"""
        agent_responses = [
            {
                'character_id': 'hero',
                'character_name': '勇者',
                'response': '好的，我们出发！',
                'state_changes': {},
                'attribute_changes': {}
            },
            {
                'character_id': 'mage',
                'character_name': '魔法师',
                'response': '让我准备一下法术',
                'state_changes': {},
                'attribute_changes': {}
            }
        ]
        
        scene_content = "测试场景"
        result = self.aggregator.aggregate_responses(agent_responses, scene_content)
        
        # 验证表信息
        self.assertIn('surface', result)
        self.assertIn('responses', result['surface'])
        self.assertEqual(len(result['surface']['responses']), 2)
        
        # 验证里信息
        self.assertIn('hidden', result)
        self.assertIn('state_changes', result['hidden'])
        self.assertIn('attribute_changes', result['hidden'])
    
    def test_aggregate_responses_with_state_changes(self):
        """测试包含状态变化的响应聚合"""
        agent_responses = [
            {
                'character_id': 'hero',
                'character_name': '勇者',
                'response': '我准备好了',
                'state_changes': {
                    'surface': {
                        'perceived_state': '显得更加专注'
                    },
                    'hidden': {
                        'observer_state': '握紧武器',
                        'inner_monologue': '必须完成任务'
                    }
                },
                'attribute_changes': {
                    'vitals': {
                        'hp': 100,
                        'mp': 50
                    }
                }
            }
        ]
        
        result = self.aggregator.aggregate_responses(agent_responses, "场景")
        
        # 验证状态变化被正确聚合
        self.assertIn('hero', result['hidden']['state_changes'])
        self.assertIn('hero', result['hidden']['attribute_changes'])
        self.assertEqual(
            result['hidden']['state_changes']['hero']['surface']['perceived_state'],
            '显得更加专注'
        )
    
    def test_aggregate_responses_empty(self):
        """测试空响应列表"""
        result = self.aggregator.aggregate_responses([], "场景")
        
        self.assertEqual(len(result['surface']['responses']), 0)
        self.assertEqual(len(result['hidden']['state_changes']), 0)
    
    def test_generate_surface_summary(self):
        """测试生成表信息摘要"""
        responses = [
            {'character_name': '勇者', 'response': '好的，我们出发！'},
            {'character_name': '魔法师', 'response': '让我准备一下法术'}
        ]
        
        summary = self.aggregator._generate_surface_summary(responses)
        
        self.assertIn('勇者', summary)
        self.assertIn('魔法师', summary)
        self.assertIn('好的，我们出发', summary)
    
    def test_generate_surface_summary_empty(self):
        """测试生成空摘要"""
        summary = self.aggregator._generate_surface_summary([])
        self.assertEqual(summary, "暂无响应")


if __name__ == '__main__':
    unittest.main()

