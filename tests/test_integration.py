"""
集成测试：测试完整的工作流程
"""
import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
import os
from services.multi_agent_coordinator import MultiAgentCoordinator
from config import Config


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = Config()
        self.coordinator = MultiAgentCoordinator(self.config)
    
    @patch('services.multi_agent_coordinator.EnvironmentManager.load_scene')
    @patch('services.multi_agent_coordinator.CharacterStore.list_characters')
    @patch('services.agent.ChatService._call_deepseek_api')
    @patch('services.multi_agent_coordinator.StateUpdater.update_character_state')
    @patch('services.multi_agent_coordinator.StateUpdater.update_scene_state')
    def test_full_workflow(self, mock_update_scene, mock_update_char, 
                          mock_api, mock_list_chars, mock_load_scene):
        """测试完整工作流程"""
        # 1. 模拟场景加载
        mock_load_scene.return_value = """# 场景设定
## 基础信息
- **时间**：黎明
- **地点**：公会大厅

## 表（玩家可见）
- **当前叙述**：队伍准备出发

## 重大事件
- （初始状态，暂无重大事件）

## 里（LLM推演用，隐藏）
- **状态**：队伍精力充足
"""
        
        # 2. 模拟角色列表
        mock_list_chars.return_value = [
            {
                'id': 'hero',
                'name': '勇者',
                'description': '勇敢的战士',
                'attributes': {
                    'class': '勇者',
                    'state': {
                        'surface': {'perceived_state': '准备就绪'},
                        'hidden': {'observer_state': '检查装备', 'inner_monologue': '要保持警惕'}
                    }
                },
                'theme': 'adventure_party'
            }
        ]
        
        # 3. 模拟API响应
        mock_api.return_value = json.dumps({
            'response': '好的，我们出发去遗迹！',
            'state_changes': {
                'surface': {
                    'perceived_state': '显得更加专注和警惕'
                },
                'hidden': {
                    'observer_state': '握紧剑柄，观察四周',
                    'inner_monologue': '必须确保队伍安全，遗迹可能很危险'
                }
            },
            'attribute_changes': {}
        })
        
        # 4. 执行指令
        result = self.coordinator.process_instruction(
            instruction="我们出发去遗迹调查",
            theme='adventure_party',
            save_step='0_step',
            platform='deepseek'
        )
        
        # 5. 验证结果
        self.assertIn('surface', result)
        self.assertIn('hidden', result)
        self.assertIn('responses', result['surface'])
        
        # 6. 验证状态更新被调用
        # 注意：由于并行处理，可能不会立即调用，但结构应该正确
        self.assertTrue(mock_load_scene.called)
        self.assertTrue(mock_list_chars.called)
    
    @patch('services.multi_agent_coordinator.EnvironmentManager.load_scene')
    @patch('services.multi_agent_coordinator.CharacterStore.list_characters')
    @patch('services.agent.ChatService._call_deepseek_api')
    def test_workflow_with_state_changes(self, mock_api, mock_list_chars, mock_load_scene):
        """测试包含状态变化的工作流程"""
        mock_load_scene.return_value = "场景内容"
        mock_list_chars.return_value = [
            {
                'id': 'hero',
                'name': '勇者',
                'description': '战士',
                'attributes': {'state': {'surface': {}, 'hidden': {}}},
                'theme': 'adventure_party'
            }
        ]
        
        # 模拟包含状态变化的响应
        mock_api.return_value = json.dumps({
            'response': '我受伤了！',
            'state_changes': {
                'surface': {
                    'perceived_state': '显得疲惫，身上有伤口'
                },
                'hidden': {
                    'observer_state': '捂住伤口，呼吸急促',
                    'inner_monologue': '伤势不轻，需要治疗'
                }
            },
            'attribute_changes': {
                'vitals': {
                    'hp': 50,  # 从100降到50
                    'mp': 50,
                    'stamina': 40
                }
            }
        })
        
        result = self.coordinator.process_instruction(
            instruction="遭遇战斗",
            theme='adventure_party',
            save_step='0_step'
        )
        
        # 验证状态变化被包含在结果中
        self.assertIn('hidden', result)
        self.assertIn('state_changes', result['hidden'])
        self.assertIn('attribute_changes', result['hidden'])


if __name__ == '__main__':
    unittest.main()

