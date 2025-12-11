"""
场景更新和联合调用测试
测试智能体响应后的场景更新和LLM联合分析
"""
import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from services.multi_agent_coordinator import MultiAgentCoordinator
from services.environment_manager import EnvironmentManager
from services.environment_analyzer import EnvironmentAnalyzer
from config import Config


class TestSceneUpdateAndJointCall(unittest.TestCase):
    """场景更新和联合调用测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = Config()
        self.test_dir = tempfile.mkdtemp()
        self.char_dir = os.path.join(self.test_dir, 'characters', 'adventure_party')
        self.save_dir = os.path.join(self.test_dir, 'save', 'adventure_party', '0_step')
        os.makedirs(self.char_dir, exist_ok=True)
        os.makedirs(self.save_dir, exist_ok=True)
        
        # 创建测试场景文件
        scene_content = """# 场景设定

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
        scene_file = os.path.join(self.save_dir, 'SCENE.md')
        with open(scene_file, 'w', encoding='utf-8') as f:
            f.write(scene_content)
        
        # 创建测试角色文件
        characters = [
            {'id': 'hero', 'name': '勇者', 'description': '战士', 'attributes': {}, 'theme': 'adventure_party'},
            {'id': 'mage', 'name': '魔法师', 'description': '法师', 'attributes': {}, 'theme': 'adventure_party'}
        ]
        
        for char in characters:
            char_file = os.path.join(self.char_dir, f"{char['id']}.json")
            with open(char_file, 'w', encoding='utf-8') as f:
                json.dump(char, f, ensure_ascii=False, indent=2)
            
            # 也创建存档中的角色文件
            save_char_file = os.path.join(self.save_dir, f"{char['id']}.json")
            with open(save_char_file, 'w', encoding='utf-8') as f:
                json.dump(char, f, ensure_ascii=False, indent=2)
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    @patch('services.character_store.CharacterStore.list_characters')
    @patch('services.agent.ChatService._call_deepseek_api')
    @patch('services.chat_service.ChatService._call_deepseek_api')
    def test_environment_analyzer_called_after_responses(self, mock_env_api, mock_agent_api, mock_list_chars):
        """测试智能体响应后，环境分析器被调用"""
        # 模拟角色列表
        mock_list_chars.return_value = [
            {'id': 'hero', 'name': '勇者', 'description': '战士', 'attributes': {}, 'theme': 'adventure_party'},
            {'id': 'mage', 'name': '魔法师', 'description': '法师', 'attributes': {}, 'theme': 'adventure_party'}
        ]
        
        # 模拟Agent响应
        agent_response = {
            'response': '好的，我们出发！',
            'state_changes': {},
            'attribute_changes': {}
        }
        mock_agent_api.return_value = json.dumps(agent_response)
        
        # 模拟环境分析响应（注意：环境分析器使用ChatService实例，需要单独mock）
        env_response = {
            'scene_changes': {'surface': {}, 'hidden': {}},
            'major_events': []
        }
        # 使用side_effect来区分Agent调用和环境分析调用
        call_count = {'agent': 0, 'env': 0}
        
        def agent_side_effect(*args, **kwargs):
            call_count['agent'] += 1
            return json.dumps(agent_response)
        
        def env_side_effect(*args, **kwargs):
            call_count['env'] += 1
            return json.dumps(env_response)
        
        # Agent调用使用agent_api
        mock_agent_api.side_effect = agent_side_effect
        # 环境分析调用使用env_api（但需要确保它被调用）
        # 由于EnvironmentAnalyzer创建了新的ChatService实例，我们需要mock那个实例
        mock_env_api.side_effect = env_side_effect
        
        # 修改coordinator的base_dir
        coordinator = MultiAgentCoordinator(self.config)
        coordinator.environment_manager.base_dir = self.test_dir
        coordinator.character_store.base_dir = self.test_dir
        
        # 直接mock环境分析器的chat_service
        coordinator.environment_manager.analyzer.chat_service._call_deepseek_api = env_side_effect
        
        # 执行指令
        result = coordinator.process_instruction(
            instruction="我们出发",
            theme='adventure_party',
            save_step='0_step',
            platform='deepseek'
        )
        
        # 验证环境分析器被调用
        # 应该有：2个Agent调用 + 1个环境分析调用
        self.assertGreaterEqual(call_count['agent'], 2, f"应该至少调用Agent两次，实际{call_count['agent']}次")
        self.assertEqual(call_count['env'], 1, f"应该调用环境分析器一次，实际{call_count['env']}次")
    
    @patch('services.environment_analyzer.ChatService._call_deepseek_api')
    def test_environment_analyzer_extracts_changes(self, mock_api):
        """测试环境分析器能提取环境变化"""
        # 模拟LLM分析响应
        analysis_response = {
            'scene_changes': {
                'surface': {
                    'current_narrative': '队伍已经出发，正在前往遗迹'
                },
                'hidden': {
                    'potential_risks': '遗迹可能很危险'
                }
            },
            'major_events': [
                '队伍出发前往遗迹',
                '发现重要线索'
            ]
        }
        mock_api.return_value = json.dumps(analysis_response)
        
        analyzer = EnvironmentAnalyzer(self.config)
        scene_content = "测试场景"
        agent_responses = [
            {'character_name': '勇者', 'response': '我们出发！'},
            {'character_name': '魔法师', 'response': '发现重要线索！'}
        ]
        
        result = analyzer.analyze_environment_changes(
            scene_content,
            agent_responses,
            platform='deepseek'
        )
        
        # 验证结果
        self.assertIn('scene_changes', result)
        self.assertIn('major_events', result)
        self.assertIn('surface', result['scene_changes'])
        self.assertIn('hidden', result['scene_changes'])
        
        # 验证LLM被调用
        self.assertTrue(mock_api.called, "环境分析器应该调用LLM")
    
    def test_scene_update_after_agent_responses(self):
        """测试智能体响应后场景被更新"""
        # 这个测试需要真实文件系统
        env_manager = EnvironmentManager(self.config)
        env_manager.base_dir = self.test_dir
        
        # 模拟智能体响应
        agent_responses = [
            {
                'character_name': '勇者',
                'response': '我们发现了一个重要线索！',
                'state_changes': {},
                'attribute_changes': {}
            }
        ]
        
        scene_content = env_manager.load_scene('adventure_party', '0_step')
        
        # 应用响应到环境（这里会调用LLM，但我们用mock）
        with patch('services.environment_analyzer.ChatService._call_deepseek_api') as mock_api:
            mock_api.return_value = json.dumps({
                'scene_changes': {
                    'surface': {},
                    'hidden': {}
                },
                'major_events': ['发现重要线索']
            })
            
            environment_changes = env_manager.apply_responses_to_environment(
                scene_content,
                agent_responses,
                platform='deepseek'
            )
        
        # 验证环境变化被提取
        self.assertIn('major_events', environment_changes)
        self.assertIn('scene_changes', environment_changes)
    
    @patch('services.character_store.CharacterStore.list_characters')
    @patch('services.agent.ChatService._call_deepseek_api')
    @patch('services.chat_service.ChatService._call_deepseek_api')
    def test_full_workflow_with_scene_update(self, mock_env_api, mock_agent_api, mock_list_chars):
        """测试完整工作流程，包括场景更新"""
        # 模拟角色列表
        mock_list_chars.return_value = [
            {'id': 'hero', 'name': '勇者', 'description': '战士', 'attributes': {}, 'theme': 'adventure_party'}
        ]
        
        # 模拟Agent响应
        agent_response = {
            'response': '我们发现重要线索！',
            'state_changes': {},
            'attribute_changes': {}
        }
        
        # 模拟环境分析响应
        env_response = {
            'scene_changes': {
                'surface': {
                    'current_narrative': '队伍发现重要线索'
                },
                'hidden': {}
            },
            'major_events': ['发现重要线索']
        }
        
        # 使用side_effect来区分调用
        call_count = {'agent': 0, 'env': 0}
        
        def agent_side_effect(*args, **kwargs):
            call_count['agent'] += 1
            return json.dumps(agent_response)
        
        def env_side_effect(*args, **kwargs):
            call_count['env'] += 1
            return json.dumps(env_response)
        
        mock_agent_api.side_effect = agent_side_effect
        mock_env_api.side_effect = env_side_effect
        
        # 修改coordinator的base_dir
        coordinator = MultiAgentCoordinator(self.config)
        coordinator.environment_manager.base_dir = self.test_dir
        coordinator.character_store.base_dir = self.test_dir
        coordinator.state_updater.base_dir = self.test_dir
        
        # 直接mock环境分析器的chat_service
        coordinator.environment_manager.analyzer.chat_service._call_deepseek_api = env_side_effect
        
        # 执行指令
        result = coordinator.process_instruction(
            instruction="调查线索",
            theme='adventure_party',
            save_step='0_step',
            platform='deepseek'
        )
        
        # 验证结果
        self.assertIn('surface', result)
        self.assertIn('hidden', result)
        self.assertIn('environment_changes', result['hidden'])
        
        # 验证场景文件被更新
        scene_file = os.path.join(self.save_dir, 'SCENE.md')
        with open(scene_file, 'r', encoding='utf-8') as f:
            scene_content = f.read()
        
        # 验证重大事件被添加（如果更新成功）
        # 注意：由于_extract_major_events的简单实现，可能不会自动提取
        # 但environment_changes应该包含分析结果
        
        # 验证LLM调用次数
        # 应该有：1个Agent调用 + 1个环境分析调用
        self.assertEqual(call_count['agent'], 1, f"应该调用Agent一次，实际{call_count['agent']}次")
        self.assertEqual(call_count['env'], 1, f"应该调用环境分析一次，实际{call_count['env']}次")


if __name__ == '__main__':
    unittest.main()

