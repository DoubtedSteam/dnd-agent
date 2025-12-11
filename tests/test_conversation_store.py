"""
ConversationStore 单元测试
"""
import unittest
import os
import json
import tempfile
import shutil
from services.conversation_store import ConversationStore
from config import Config


class TestConversationStore(unittest.TestCase):
    """ConversationStore 类测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = Config()
        # 使用临时目录进行测试
        self.test_dir = tempfile.mkdtemp()
        self.store = ConversationStore(self.config)
        # 修改store的base_dir指向测试目录
        self.store.base_dir = os.path.join(self.test_dir, 'conversations')
        os.makedirs(self.store.base_dir, exist_ok=True)
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_save_conversation(self):
        """测试保存对话记录"""
        conversation = self.store.save_conversation(
            character_id='hero',
            user_message='你好',
            character_response='你好！我是勇者',
            consistency_score=0.95,
            consistency_feedback='回复符合设定'
        )
        
        # 验证返回的对话记录
        self.assertEqual(conversation['character_id'], 'hero')
        self.assertEqual(conversation['user_message'], '你好')
        self.assertEqual(conversation['character_response'], '你好！我是勇者')
        self.assertEqual(conversation['consistency_score'], 0.95)
        self.assertIn('created_at', conversation)
        
        # 验证文件被创建
        file_path = self.store._get_file_path('hero')
        self.assertTrue(os.path.exists(file_path))
        
        # 验证文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['user_message'], '你好')
    
    def test_save_multiple_conversations(self):
        """测试保存多条对话记录"""
        # 保存第一条
        self.store.save_conversation('hero', '消息1', '回复1')
        # 保存第二条
        self.store.save_conversation('hero', '消息2', '回复2')
        
        # 验证文件中有两条记录
        file_path = self.store._get_file_path('hero')
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]['user_message'], '消息1')
            self.assertEqual(data[1]['user_message'], '消息2')
    
    def test_get_conversations_empty(self):
        """测试获取对话记录（空）"""
        conversations = self.store.get_conversations('nonexistent')
        self.assertEqual(len(conversations), 0)
    
    def test_get_conversations_with_limit(self):
        """测试获取对话记录（带限制）"""
        # 保存多条记录
        for i in range(5):
            self.store.save_conversation('hero', f'消息{i}', f'回复{i}')
        
        # 获取前3条
        conversations = self.store.get_conversations('hero', limit=3)
        self.assertEqual(len(conversations), 3)
        
        # 验证按时间倒序
        self.assertEqual(conversations[0]['user_message'], '消息4')
        self.assertEqual(conversations[1]['user_message'], '消息3')
    
    def test_get_conversations_all(self):
        """测试获取所有对话记录"""
        # 保存多条记录
        for i in range(3):
            self.store.save_conversation('hero', f'消息{i}', f'回复{i}')
        
        conversations = self.store.get_conversations('hero')
        self.assertEqual(len(conversations), 3)
    
    def test_conversation_file_format(self):
        """测试对话记录文件格式"""
        self.store.save_conversation('hero', '测试', '回复')
        
        file_path = self.store._get_file_path('hero')
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # 验证JSON格式
            self.assertIsInstance(data, list)
            self.assertGreater(len(data), 0)
            
            conv = data[0]
            self.assertIn('id', conv)
            self.assertIn('character_id', conv)
            self.assertIn('user_message', conv)
            self.assertIn('character_response', conv)
            self.assertIn('created_at', conv)


if __name__ == '__main__':
    unittest.main()

