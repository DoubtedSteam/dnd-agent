"""
带LLM调用日志的测试
显示所有LLM调用的输入、输出和token数
"""
import unittest
import os
from tests.llm_call_logger import logger
from services.agent import Agent
from services.multi_agent_coordinator import MultiAgentCoordinator
from config import Config


class TestWithLLMLogging(unittest.TestCase):
    """带LLM调用日志的测试"""
    
    @classmethod
    def setUpClass(cls):
        """检查是否启用真实API测试"""
        cls.use_real_api = os.getenv('USE_REAL_API', 'false').lower() == 'true'
        
        if not cls.use_real_api:
            raise unittest.SkipTest("跳过真实API测试（设置 USE_REAL_API=true 启用）")
        
        # 启用LLM调用记录
        logger.enable()
        logger.clear()
    
    @classmethod
    def tearDownClass(cls):
        """打印调用摘要"""
        logger.print_summary()
    
    def setUp(self):
        """设置测试环境"""
        self.config = Config()
        logger.clear()  # 每个测试前清空记录
        # 设置测试上下文
        test_module = self.__class__.__module__.replace('tests.', '')
        test_name = self._testMethodName
        logger.set_test_context(test_module=test_module, test_name=test_name)
    
    def tearDown(self):
        """测试后打印本次测试的调用"""
        if logger.calls:
            print(f"\n本次测试共进行了 {len(logger.calls)} 次LLM调用")
    
    def test_agent_with_logging(self):
        """测试Agent，显示LLM调用"""
        print("\n" + "="*80)
        print("测试：Agent处理指令（带LLM调用日志）")
        print("="*80)
        
        character_data = {
            'id': 'hero',
            'name': '勇者',
            'description': '一个勇敢的战士，擅长近战',
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
        scene_content = """# 场景设定
## 基础信息
- **时间**：黎明
- **地点**：公会大厅

## 表（玩家可见）
- **当前叙述**：队伍准备出发
"""
        instruction = "我们出发去遗迹调查"
        
        result = agent.process_instruction(
            instruction=instruction,
            scene_content=scene_content,
            platform='deepseek'
        )
        
        # 验证结果
        self.assertIn('character_id', result)
        self.assertIn('response', result)
        print(f"\n✅ Agent响应: {result['response'][:100]}...")
    
    def test_multi_agent_coordinator_with_logging(self):
        """测试MultiAgentCoordinator，显示所有智能体的LLM调用"""
        print("\n" + "="*80)
        print("测试：多智能体协调器（带LLM调用日志）")
        print("="*80)
        
        coordinator = MultiAgentCoordinator(self.config)
        
        result = coordinator.process_instruction(
            instruction="我们出发去遗迹调查",
            theme='adventure_party',
            save_step='0_step',
            platform='deepseek'
        )
        
        # 验证结果
        self.assertIn('surface', result)
        self.assertIn('hidden', result)
        
        print(f"\n✅ 共收到 {len(result['surface']['responses'])} 个智能体响应")
        print(f"✅ 共进行了 {len(logger.calls)} 次LLM调用")


if __name__ == '__main__':
    unittest.main()

