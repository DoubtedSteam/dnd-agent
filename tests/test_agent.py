"""
Agent 单元测试

默认使用mock，不调用真实API。
要使用真实API，设置环境变量 USE_REAL_API=true
"""
import unittest
import os
from unittest.mock import Mock, patch, MagicMock
import json
from services.agent import Agent
from config import Config


class TestAgent(unittest.TestCase):
    """Agent 类测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = Config()
        self.character_data = {
            'id': 'test_hero',
            'name': '测试勇者',
            'description': '一个勇敢的测试角色',
            'attributes': {
                'class': '勇者',
                'level': 10,
                'gender': '男',
                'vitals': {
                    'hp': 100,
                    'mp': 50,
                    'stamina': 80
                },
                'state': {
                    'surface': {
                        'perceived_state': '准备就绪'
                    },
                    'hidden': {
                        'observer_state': '检查装备',
                        'inner_monologue': '要保持警惕'
                    }
                }
            },
            'theme': 'adventure_party'
        }
        self.agent = Agent(self.character_data, self.config)
    
    def test_agent_initialization(self):
        """测试智能体初始化"""
        self.assertEqual(self.agent.character_id, 'test_hero')
        self.assertEqual(self.agent.character_name, '测试勇者')
        self.assertEqual(self.agent.description, '一个勇敢的测试角色')
        self.assertEqual(self.agent.theme, 'adventure_party')
    
    @patch('services.agent.ChatService._call_deepseek_api')
    def test_process_instruction_success(self, mock_api):
        """测试处理指令成功（使用mock）"""
        # 如果设置了USE_REAL_API，跳过mock测试
        if os.getenv('USE_REAL_API', 'false').lower() == 'true':
            self.skipTest("真实API测试在test_with_real_api.py中")
        
        # 模拟API响应
        mock_response = {
            'response': '好的，我准备好了！',
            'state_changes': {
                'surface': {
                    'perceived_state': '显得更加专注'
                },
                'hidden': {
                    'observer_state': '握紧武器',
                    'inner_monologue': '必须完成任务'
                }
            },
            'attribute_changes': {}
        }
        mock_api.return_value = json.dumps(mock_response)
        
        scene_content = "测试场景内容"
        instruction = "我们出发吧"
        
        result = self.agent.process_instruction(
            instruction=instruction,
            scene_content=scene_content,
            platform='deepseek'
        )
        
        # 验证结果
        self.assertEqual(result['character_id'], 'test_hero')
        self.assertEqual(result['character_name'], '测试勇者')
        self.assertIn('response', result)
        self.assertIn('state_changes', result)
        self.assertIn('attribute_changes', result)
        
        # 验证API被调用
        self.assertTrue(mock_api.called)
    
    @patch('services.agent.ChatService._call_deepseek_api')
    def test_process_instruction_with_json_wrapper(self, mock_api):
        """测试处理指令（JSON包装在代码块中）"""
        mock_response = f"""```json
{json.dumps({
    'response': '收到指令',
    'state_changes': {},
    'attribute_changes': {}
})}
```"""
        mock_api.return_value = mock_response
        
        result = self.agent.process_instruction(
            instruction="测试",
            scene_content="场景",
            platform='deepseek'
        )
        
        self.assertEqual(result['response'], '收到指令')
    
    @patch('services.agent.ChatService._call_deepseek_api')
    def test_process_instruction_invalid_json(self, mock_api):
        """测试处理指令（无效JSON）"""
        mock_api.return_value = "这不是JSON格式的响应"
        
        result = self.agent.process_instruction(
            instruction="测试",
            scene_content="场景",
            platform='deepseek'
        )
        
        # 应该返回原始响应
        self.assertEqual(result['response'], "这不是JSON格式的响应")
        self.assertEqual(result['state_changes'], {})
        self.assertEqual(result['attribute_changes'], {})
    
    def test_build_agent_prompt(self):
        """测试构建智能体提示词"""
        scene_content = "测试场景"
        prompt = self.agent._build_agent_prompt(scene_content)
        
        # 验证提示词包含必要信息
        self.assertIn('测试勇者', prompt)
        self.assertIn('一个勇敢的测试角色', prompt)
        self.assertIn('测试场景', prompt)
        self.assertIn('角色扮演智能体', prompt)


if __name__ == '__main__':
    unittest.main()

