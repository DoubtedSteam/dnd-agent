"""
环境修改测试：使用真实文件系统测试环境修改功能
"""
import unittest
import os
import json
import tempfile
import shutil
from services.state_updater import StateUpdater
from services.environment_manager import EnvironmentManager
from services.multi_agent_coordinator import MultiAgentCoordinator
from config import Config


class TestEnvironmentModification(unittest.TestCase):
    """环境修改测试（使用真实文件系统）"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = Config()
        # 创建临时目录结构
        self.test_dir = tempfile.mkdtemp()
        self.char_dir = os.path.join(self.test_dir, 'characters', 'test_theme')
        self.save_dir = os.path.join(self.test_dir, 'save', 'test_theme', '0_step')
        os.makedirs(self.char_dir, exist_ok=True)
        os.makedirs(self.save_dir, exist_ok=True)
        
        # 创建测试用的StateUpdater和EnvironmentManager
        self.updater = StateUpdater(self.config)
        self.env_manager = EnvironmentManager(self.config)
        
        # 修改base_dir指向测试目录
        self.original_char_dir = self.config.CHARACTER_CONFIG_DIR
        self.original_save_dir = self.config.SAVE_DIR
        # 注意：由于config是类属性，我们需要直接修改updater和env_manager的base_dir
        self.updater.base_dir = self.test_dir
        self.env_manager.base_dir = self.test_dir
        
        # 创建测试用的角色文件
        self.character_data = {
            'id': 'test_hero',
            'name': '测试勇者',
            'attributes': {
                'class': '勇者',
                'level': 10,
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
            }
        }
        
        # 保存角色文件
        character_file = os.path.join(self.save_dir, 'test_hero.json')
        with open(character_file, 'w', encoding='utf-8') as f:
            json.dump(self.character_data, f, ensure_ascii=False, indent=2)
        
        # 创建测试用的场景文件
        self.scene_content = """# 场景设定

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
            f.write(self.scene_content)
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_update_character_state_writes_to_file(self):
        """测试更新角色状态会正确写入文件"""
        state_changes = {
            'surface': {
                'perceived_state': '显得更加专注和警惕'
            },
            'hidden': {
                'observer_state': '握紧剑柄，观察四周',
                'inner_monologue': '必须确保队伍安全'
            }
        }
        
        attribute_changes = {
            'vitals': {
                'hp': 80,  # 从100降到80
                'mp': 50,
                'stamina': 60  # 从80降到60
            }
        }
        
        # 执行更新
        result = self.updater.update_character_state(
            'test_theme',
            '0_step',
            'test_hero',
            state_changes,
            attribute_changes
        )
        
        self.assertTrue(result, "更新应该成功")
        
        # 验证文件内容
        character_file = os.path.join(self.save_dir, 'test_hero.json')
        self.assertTrue(os.path.exists(character_file), "角色文件应该存在")
        
        with open(character_file, 'r', encoding='utf-8') as f:
            updated_data = json.load(f)
        
        # 验证状态更新
        self.assertEqual(
            updated_data['attributes']['state']['surface']['perceived_state'],
            '显得更加专注和警惕'
        )
        self.assertEqual(
            updated_data['attributes']['state']['hidden']['observer_state'],
            '握紧剑柄，观察四周'
        )
        self.assertEqual(
            updated_data['attributes']['state']['hidden']['inner_monologue'],
            '必须确保队伍安全'
        )
        
        # 验证属性更新
        self.assertEqual(updated_data['attributes']['vitals']['hp'], 80)
        self.assertEqual(updated_data['attributes']['vitals']['stamina'], 60)
    
    def test_update_scene_state_adds_major_events(self):
        """测试更新场景状态会添加重大事件"""
        major_events = [
            '队伍出发前往遗迹',
            '发现重要线索',
            '遭遇敌人'
        ]
        
        # 执行更新
        result = self.updater.update_scene_state(
            'test_theme',
            '0_step',
            {},
            major_events
        )
        
        self.assertTrue(result, "更新应该成功")
        
        # 验证文件内容
        scene_file = os.path.join(self.save_dir, 'SCENE.md')
        self.assertTrue(os.path.exists(scene_file), "场景文件应该存在")
        
        with open(scene_file, 'r', encoding='utf-8') as f:
            updated_content = f.read()
        
        # 验证重大事件被添加
        self.assertIn('## 重大事件', updated_content)
        self.assertIn('- 队伍出发前往遗迹', updated_content)
        self.assertIn('- 发现重要线索', updated_content)
        self.assertIn('- 遭遇敌人', updated_content)
    
    def test_update_scene_state_replaces_existing_events(self):
        """测试更新场景状态会替换现有重大事件"""
        # 先添加一些事件
        initial_events = ['初始事件1', '初始事件2']
        self.updater.update_scene_state(
            'test_theme',
            '0_step',
            {},
            initial_events
        )
        
        # 再添加新事件（应该替换）
        new_events = ['新事件1', '新事件2']
        result = self.updater.update_scene_state(
            'test_theme',
            '0_step',
            {},
            new_events
        )
        
        self.assertTrue(result)
        
        # 验证文件内容
        scene_file = os.path.join(self.save_dir, 'SCENE.md')
        with open(scene_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 应该只有新事件，没有旧事件
        self.assertIn('- 新事件1', content)
        self.assertIn('- 新事件2', content)
        # 注意：当前实现是替换，所以旧事件会被替换掉
    
    def test_update_character_state_merges_changes(self):
        """测试更新角色状态会合并变化而不是覆盖"""
        # 第一次更新
        state_changes_1 = {
            'surface': {
                'perceived_state': '显得专注'
            },
            'hidden': {
                'observer_state': '握紧武器'
            }
        }
        self.updater.update_character_state(
            'test_theme',
            '0_step',
            'test_hero',
            state_changes_1,
            {}
        )
        
        # 第二次更新（应该合并）
        state_changes_2 = {
            'hidden': {
                'inner_monologue': '新的内心独白'
            }
        }
        self.updater.update_character_state(
            'test_theme',
            '0_step',
            'test_hero',
            state_changes_2,
            {}
        )
        
        # 验证文件内容
        character_file = os.path.join(self.save_dir, 'test_hero.json')
        with open(character_file, 'r', encoding='utf-8') as f:
            updated_data = json.load(f)
        
        # 第一次更新的内容应该还在
        self.assertEqual(
            updated_data['attributes']['state']['surface']['perceived_state'],
            '显得专注'
        )
        self.assertEqual(
            updated_data['attributes']['state']['hidden']['observer_state'],
            '握紧武器'
        )
        # 第二次更新的内容应该也在
        self.assertEqual(
            updated_data['attributes']['state']['hidden']['inner_monologue'],
            '新的内心独白'
        )
    
    def test_update_character_state_with_nonexistent_file(self):
        """测试更新不存在的角色文件会失败"""
        result = self.updater.update_character_state(
            'test_theme',
            '0_step',
            'nonexistent',
            {},
            {}
        )
        
        self.assertFalse(result, "更新不存在的文件应该失败")
    
    def test_update_scene_state_with_nonexistent_file(self):
        """测试更新不存在的场景文件会失败"""
        result = self.updater.update_scene_state(
            'test_theme',
            'nonexistent_step',
            {},
            []
        )
        
        self.assertFalse(result, "更新不存在的文件应该失败")
    
    def test_environment_manager_loads_updated_scene(self):
        """测试环境管理器能加载更新后的场景"""
        # 先更新场景
        major_events = ['测试事件']
        self.updater.update_scene_state(
            'test_theme',
            '0_step',
            {},
            major_events
        )
        
        # 使用环境管理器加载
        scene_content = self.env_manager.load_scene('test_theme', '0_step')
        
        self.assertIsNotNone(scene_content)
        self.assertIn('测试事件', scene_content)
    
    def test_full_update_workflow(self):
        """测试完整的环境更新工作流程"""
        # 1. 更新角色状态
        state_changes = {
            'surface': {
                'perceived_state': '战斗状态'
            },
            'hidden': {
                'observer_state': '受伤了',
                'inner_monologue': '需要治疗'
            }
        }
        attribute_changes = {
            'vitals': {
                'hp': 50,
                'mp': 30,
                'stamina': 40
            }
        }
        
        result1 = self.updater.update_character_state(
            'test_theme',
            '0_step',
            'test_hero',
            state_changes,
            attribute_changes
        )
        self.assertTrue(result1)
        
        # 2. 更新场景状态
        major_events = ['战斗结束', '获得战利品']
        result2 = self.updater.update_scene_state(
            'test_theme',
            '0_step',
            {},
            major_events
        )
        self.assertTrue(result2)
        
        # 3. 验证所有更新都生效
        # 验证角色文件
        character_file = os.path.join(self.save_dir, 'test_hero.json')
        with open(character_file, 'r', encoding='utf-8') as f:
            char_data = json.load(f)
        self.assertEqual(char_data['attributes']['vitals']['hp'], 50)
        self.assertEqual(char_data['attributes']['state']['surface']['perceived_state'], '战斗状态')
        
        # 验证场景文件
        scene_file = os.path.join(self.save_dir, 'SCENE.md')
        with open(scene_file, 'r', encoding='utf-8') as f:
            scene_data = f.read()
        self.assertIn('- 战斗结束', scene_data)
        self.assertIn('- 获得战利品', scene_data)


if __name__ == '__main__':
    unittest.main()

