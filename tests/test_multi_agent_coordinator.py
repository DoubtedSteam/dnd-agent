"""
MultiAgentCoordinator 单元测试
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from services.multi_agent_coordinator import MultiAgentCoordinator
from config import Config


class TestMultiAgentCoordinator(unittest.TestCase):
    """MultiAgentCoordinator 类测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = Config()
        self.coordinator = MultiAgentCoordinator(self.config)
    
    @patch('services.multi_agent_coordinator.EnvironmentManager.load_scene')
    @patch('services.multi_agent_coordinator.CharacterStore.list_characters')
    @patch('services.multi_agent_coordinator.Agent.process_instruction')
    @patch('services.multi_agent_coordinator.ResponseAggregator.aggregate_responses')
    @patch('services.multi_agent_coordinator.EnvironmentManager.apply_responses_to_environment')
    def test_process_instruction_success(self, mock_env_apply, mock_aggregate, 
                                         mock_agent_process, mock_list_chars, mock_load_scene):
        """测试处理指令成功"""
        # 模拟场景内容
        mock_load_scene.return_value = "测试场景内容"
        
        # 模拟角色列表
        mock_list_chars.return_value = [
            {
                'id': 'hero',
                'name': '勇者',
                'description': '勇敢的战士',
                'attributes': {},
                'theme': 'adventure_party'
            },
            {
                'id': 'mage',
                'name': '魔法师',
                'description': '强大的法师',
                'attributes': {},
                'theme': 'adventure_party'
            }
        ]
        
        # 模拟智能体响应
        mock_agent_process.side_effect = [
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
                'response': '让我准备一下',
                'state_changes': {},
                'attribute_changes': {}
            }
        ]
        
        # 模拟聚合结果
        mock_aggregate.return_value = {
            'surface': {
                'responses': [
                    {'character_name': '勇者', 'response': '好的，我们出发！'},
                    {'character_name': '魔法师', 'response': '让我准备一下'}
                ],
                'summary': '测试摘要'
            },
            'hidden': {
                'state_changes': {},
                'attribute_changes': {},
                'detailed_info': {}
            }
        }
        
        # 模拟环境变化
        mock_env_apply.return_value = {
            'scene_changes': {'surface': {}, 'hidden': {}},
            'major_events': []
        }
        
        result = self.coordinator.process_instruction(
            instruction="我们出发吧",
            theme='adventure_party',
            save_step='0_step'
        )
        
        # 验证结果结构
        self.assertIn('surface', result)
        self.assertIn('hidden', result)
        self.assertIn('responses', result['surface'])
        self.assertEqual(len(result['surface']['responses']), 2)
        
        # 验证方法被调用
        self.assertTrue(mock_load_scene.called)
        self.assertTrue(mock_list_chars.called)
        self.assertTrue(mock_aggregate.called)
    
    @patch('services.multi_agent_coordinator.EnvironmentManager.load_scene')
    def test_process_instruction_no_scene(self, mock_load_scene):
        """测试处理指令（场景不存在）"""
        mock_load_scene.return_value = None
        
        result = self.coordinator.process_instruction(
            instruction="测试",
            theme='adventure_party'
        )
        
        self.assertIn('error', result)
        self.assertEqual(result['error'], '无法加载场景')
    
    @patch('services.multi_agent_coordinator.EnvironmentManager.load_scene')
    @patch('services.multi_agent_coordinator.CharacterStore.get_character')
    def test_process_instruction_specific_characters(self, mock_get_char, mock_load_scene):
        """测试处理指令（指定角色）"""
        mock_load_scene.return_value = "场景内容"
        
        mock_get_char.side_effect = [
            {
                'id': 'hero',
                'name': '勇者',
                'description': '战士',
                'attributes': {},
                'theme': 'adventure_party'
            },
            None  # 第二个角色不存在
        ]
        
        with patch.object(self.coordinator, 'character_store') as mock_store:
            with patch('services.multi_agent_coordinator.Agent.process_instruction') as mock_process:
                mock_process.return_value = {
                    'character_id': 'hero',
                    'character_name': '勇者',
                    'response': '响应',
                    'state_changes': {},
                    'attribute_changes': {}
                }
                
                with patch('services.multi_agent_coordinator.ResponseAggregator.aggregate_responses') as mock_agg:
                    mock_agg.return_value = {
                        'surface': {'responses': [], 'summary': ''},
                        'hidden': {'state_changes': {}, 'attribute_changes': {}, 'detailed_info': {}}
                    }
                    
                    with patch('services.multi_agent_coordinator.EnvironmentManager.apply_responses_to_environment') as mock_env:
                        mock_env.return_value = {
                            'scene_changes': {'surface': {}, 'hidden': {}},
                            'major_events': []
                        }
                        
                        result = self.coordinator.process_instruction(
                            instruction="测试",
                            theme='adventure_party',
                            character_ids=['hero', 'nonexistent']
                        )
                        
                        # 应该只处理存在的角色
                        self.assertIn('surface', result)
    
    def test_extract_major_events(self):
        """测试提取重大事件"""
        agent_responses = [
            {
                'character_name': '勇者',
                'response': '我发现了一个重要线索！'
            },
            {
                'character_name': '魔法师',
                'response': '我获得了新的法术书'
            },
            {
                'character_name': '盗贼',
                'response': '普通对话'
            }
        ]
        
        events = self.coordinator._extract_major_events(agent_responses)
        
        # 应该提取包含关键词的响应
        self.assertGreater(len(events), 0)
        self.assertTrue(any('发现' in event or '获得' in event for event in events))


if __name__ == '__main__':
    unittest.main()

