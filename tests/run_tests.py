"""
运行所有测试的脚本
"""
import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_all_tests():
    """运行所有测试"""
    # 发现并加载所有测试
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加各个测试模块
    test_modules = [
        'tests.test_agent',
        'tests.test_environment_manager',
        'tests.test_response_aggregator',
        'tests.test_state_updater',
        'tests.test_multi_agent_coordinator',
        'tests.test_integration',
        'tests.test_conversation_store',
        'tests.test_environment_modification',  # 环境修改测试（真实文件系统）
        'tests.test_scene_update_and_joint_call'  # 场景更新和联合调用测试
    ]
    
    # 如果设置了USE_REAL_API，添加真实API测试
    if os.getenv('USE_REAL_API', 'false').lower() == 'true':
        test_modules.extend([
            'tests.test_with_real_api',
            'tests.test_with_llm_logging'
        ])
    
    for module_name in test_modules:
        try:
            suite.addTests(loader.loadTestsFromName(module_name))
        except Exception as e:
            print(f"警告：无法加载测试模块 {module_name}: {e}")
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

