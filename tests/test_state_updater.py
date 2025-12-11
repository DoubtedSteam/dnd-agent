"""
StateUpdater 单元测试
"""
import unittest
from unittest.mock import patch, mock_open
import json
import os
from services.state_updater import StateUpdater
from config import Config


class TestStateUpdater(unittest.TestCase):
    """StateUpdater 类测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = Config()
        self.updater = StateUpdater(self.config)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_update_character_state_success(self, mock_exists, mock_file):
        """测试更新角色状态成功"""
        # 模拟现有角色数据
        existing_character = {
            'id': 'hero',
            'name': '勇者',
            'attributes': {
                'class': '勇者',
                'state': {
                    'surface': {},
                    'hidden': {}
                }
            }
        }
        
        mock_file.return_value.read.return_value = json.dumps(existing_character)
        mock_exists.return_value = True
        
        state_changes = {
            'surface': {
                'perceived_state': '显得更加专注'
            },
            'hidden': {
                'observer_state': '握紧武器',
                'inner_monologue': '必须完成任务'
            }
        }
        
        attribute_changes = {
            'vitals': {
                'hp': 100,
                'mp': 50
            }
        }
        
        result = self.updater.update_character_state(
            'adventure_party',
            '0_step',
            'hero',
            state_changes,
            attribute_changes
        )
        
        self.assertTrue(result)
        
        # 验证文件被写入
        self.assertTrue(mock_file.called)
    
    @patch('os.path.exists')
    def test_update_character_state_not_found(self, mock_exists):
        """测试更新角色状态（文件不存在）"""
        mock_exists.return_value = False
        
        result = self.updater.update_character_state(
            'adventure_party',
            '0_step',
            'nonexistent',
            {},
            {}
        )
        
        self.assertFalse(result)
    
    @patch('builtins.open', new_callable=mock_open, read_data="# 场景\n## 重大事件\n- 事件1\n\n## 里")
    @patch('os.path.exists')
    def test_update_scene_state_success(self, mock_exists, mock_file):
        """测试更新场景状态成功"""
        mock_exists.return_value = True
        
        major_events = ['发现重要线索', '击败了敌人']
        
        result = self.updater.update_scene_state(
            'adventure_party',
            '0_step',
            {},
            major_events
        )
        
        self.assertTrue(result)
    
    @patch('os.path.exists')
    def test_update_scene_state_not_found(self, mock_exists):
        """测试更新场景状态（文件不存在）"""
        mock_exists.return_value = False
        
        result = self.updater.update_scene_state(
            'adventure_party',
            '0_step',
            {},
            []
        )
        
        self.assertFalse(result)
    
    @patch('builtins.open', new_callable=mock_open, read_data="# 场景\n## 里")
    @patch('os.path.exists')
    def test_update_scene_state_add_events_section(self, mock_exists, mock_file):
        """测试更新场景状态（添加重大事件部分）"""
        mock_exists.return_value = True
        
        major_events = ['新事件']
        
        result = self.updater.update_scene_state(
            'adventure_party',
            '0_step',
            {},
            major_events
        )
        
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()

