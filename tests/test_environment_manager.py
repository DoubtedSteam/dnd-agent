"""
EnvironmentManager 单元测试
"""
import unittest
from unittest.mock import patch, mock_open
import os
from services.environment_manager import EnvironmentManager
from config import Config


class TestEnvironmentManager(unittest.TestCase):
    """EnvironmentManager 类测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = Config()
        self.env_manager = EnvironmentManager(self.config)
    
    @patch('builtins.open', new_callable=mock_open, read_data="# 测试场景\n内容")
    @patch('os.path.exists')
    def test_load_scene_from_save(self, mock_exists, mock_file):
        """测试从存档加载场景"""
        mock_exists.side_effect = lambda path: 'save' in path
        
        scene = self.env_manager.load_scene('adventure_party', '0_step')
        
        self.assertIsNotNone(scene)
        self.assertIn('测试场景', scene)
    
    @patch('builtins.open', new_callable=mock_open, read_data="# 初始场景\n内容")
    @patch('os.path.exists')
    def test_load_scene_from_initial(self, mock_exists, mock_file):
        """测试从初始场景加载"""
        def exists_side_effect(path):
            return 'characters' in path
        
        mock_exists.side_effect = exists_side_effect
        
        scene = self.env_manager.load_scene('adventure_party', None)
        
        self.assertIsNotNone(scene)
        self.assertIn('初始场景', scene)
    
    @patch('os.path.exists')
    def test_load_scene_not_found(self, mock_exists):
        """测试场景不存在"""
        mock_exists.return_value = False
        
        scene = self.env_manager.load_scene('nonexistent', None)
        
        self.assertIsNone(scene)
    
    def test_apply_responses_to_environment(self):
        """测试应用响应到环境"""
        scene_content = "测试场景"
        agent_responses = [
            {
                'character_name': '勇者',
                'response': '好的，我们出发！'
            },
            {
                'character_name': '魔法师',
                'response': '让我准备一下法术'
            }
        ]
        
        result = self.env_manager.apply_responses_to_environment(
            scene_content,
            agent_responses
        )
        
        # 验证返回结构
        self.assertIn('scene_changes', result)
        self.assertIn('major_events', result)
        self.assertIn('surface', result['scene_changes'])
        self.assertIn('hidden', result['scene_changes'])
    
    @patch('builtins.open', new_callable=mock_open, read_data="# 场景\n内容")
    @patch('os.path.exists')
    def test_update_scene_success(self, mock_exists, mock_file):
        """测试更新场景成功"""
        mock_exists.return_value = True
        
        result = self.env_manager.update_scene(
            'adventure_party',
            '0_step',
            {'scene_changes': {}}
        )
        
        self.assertTrue(result)
    
    @patch('os.path.exists')
    def test_update_scene_not_found(self, mock_exists):
        """测试更新场景（文件不存在）"""
        mock_exists.return_value = False
        
        result = self.env_manager.update_scene(
            'adventure_party',
            '0_step',
            {'scene_changes': {}}
        )
        
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()

