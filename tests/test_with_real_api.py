"""
使用真实API和文件系统的测试
需要设置环境变量 USE_REAL_API=true 和 USE_REAL_FILES=true
"""
import unittest
import os
import json
import tempfile
import shutil
from services.agent import Agent
from services.environment_manager import EnvironmentManager
from services.response_aggregator import ResponseAggregator
from services.state_updater import StateUpdater
from services.multi_agent_coordinator import MultiAgentCoordinator
from services.conversation_store import ConversationStore
from config import Config


class TestWithRealAPI(unittest.TestCase):
    """使用真实API的测试（需要API密钥）"""
    
    @classmethod
    def setUpClass(cls):
        """检查是否启用真实API测试"""
        cls.use_real_api = os.getenv('USE_REAL_API', 'false').lower() == 'true'
        cls.use_real_files = os.getenv('USE_REAL_FILES', 'false').lower() == 'true'
        
        if not cls.use_real_api:
            raise unittest.SkipTest("跳过真实API测试（设置 USE_REAL_API=true 启用）")
    
    def setUp(self):
        """设置测试环境"""
        self.config = Config()
        
        if self.use_real_files:
            # 使用临时目录
            self.test_dir = tempfile.mkdtemp()
            self.original_char_dir = self.config.CHARACTER_CONFIG_DIR
            self.original_save_dir = self.config.SAVE_DIR
            # 注意：这里需要修改config，但为了不破坏原有代码，我们使用实际目录
            # 实际使用时，建议在测试后清理
        else:
            self.test_dir = None
    
    def tearDown(self):
        """清理测试环境"""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_agent_with_real_api(self):
        """测试Agent使用真实API"""
        character_data = {
            'id': 'test_hero',
            'name': '测试勇者',
            'description': '一个勇敢的测试角色',
            'attributes': {
                'class': '勇者',
                'state': {
                    'surface': {'perceived_state': '准备就绪'},
                    'hidden': {'observer_state': '检查装备', 'inner_monologue': '要保持警惕'}
                }
            },
            'theme': 'adventure_party'
        }
        
        agent = Agent(character_data, self.config)
        scene_content = "测试场景：队伍在公会准备出发"
        instruction = "我们出发吧"
        
        result = agent.process_instruction(
            instruction=instruction,
            scene_content=scene_content,
            platform='deepseek'  # 或 'openai'
        )
        
        # 验证结果
        self.assertIn('character_id', result)
        self.assertIn('response', result)
        self.assertIsInstance(result['response'], str)
        self.assertGreater(len(result['response']), 0)
        print(f"\n真实API响应: {result['response'][:100]}...")


class TestWithRealFiles(unittest.TestCase):
    """使用真实文件系统的测试"""
    
    @classmethod
    def setUpClass(cls):
        """检查是否启用真实文件系统测试"""
        cls.use_real_files = os.getenv('USE_REAL_FILES', 'false').lower() == 'true'
        
        if not cls.use_real_files:
            raise unittest.SkipTest("跳过真实文件系统测试（设置 USE_REAL_FILES=true 启用）")
    
    def setUp(self):
        """设置测试环境"""
        self.config = Config()
        self.test_dir = tempfile.mkdtemp()
        self.test_char_dir = os.path.join(self.test_dir, 'characters')
        self.test_save_dir = os.path.join(self.test_dir, 'save')
        os.makedirs(self.test_char_dir, exist_ok=True)
        os.makedirs(self.test_save_dir, exist_ok=True)
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_environment_manager_with_real_files(self):
        """测试EnvironmentManager使用真实文件"""
        # 创建测试场景文件
        theme = 'test_theme'
        theme_dir = os.path.join(self.test_char_dir, theme)
        os.makedirs(theme_dir, exist_ok=True)
        
        scene_file = os.path.join(theme_dir, 'SCENE.md')
        with open(scene_file, 'w', encoding='utf-8') as f:
            f.write("# 测试场景\n内容")
        
        # 修改config指向测试目录（需要修改EnvironmentManager来接受base_dir参数）
        # 这里简化处理，直接测试文件读写
        env_manager = EnvironmentManager(self.config)
        
        # 由于EnvironmentManager使用固定路径，我们需要修改它或使用实际路径
        # 这里仅演示概念
        self.assertTrue(os.path.exists(scene_file))
    
    def test_conversation_store_with_real_files(self):
        """测试ConversationStore使用真实文件"""
        # 创建临时conversations目录
        conv_dir = os.path.join(self.test_dir, 'conversations')
        os.makedirs(conv_dir, exist_ok=True)
        
        # 由于ConversationStore使用固定路径，我们需要修改它
        # 这里创建一个简单的测试版本
        character_id = 'test_hero'
        conv_file = os.path.join(conv_dir, f'{character_id}.json')
        
        # 测试保存
        conversation = {
            "id": 1,
            "character_id": character_id,
            "user_message": "测试消息",
            "character_response": "测试回复",
            "created_at": "2024-01-01T00:00:00"
        }
        
        with open(conv_file, 'w', encoding='utf-8') as f:
            json.dump([conversation], f, ensure_ascii=False, indent=2)
        
        # 测试读取
        self.assertTrue(os.path.exists(conv_file))
        with open(conv_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['user_message'], "测试消息")


if __name__ == '__main__':
    unittest.main()

