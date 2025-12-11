"""
对话记录存储服务：使用JSON文件存储对话历史
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from config import Config


class ConversationStore:
    """对话记录存储（JSON文件）"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "conversations"))
        os.makedirs(self.base_dir, exist_ok=True)
    
    def _get_file_path(self, character_id: str) -> str:
        """获取对话记录文件路径"""
        return os.path.join(self.base_dir, f"{character_id}.json")
    
    def save_conversation(self, character_id: str, user_message: str, 
                         character_response: str, consistency_score: Optional[float] = None,
                         consistency_feedback: Optional[str] = None) -> Dict:
        """
        保存对话记录
        
        Returns:
            保存的对话记录
        """
        file_path = self._get_file_path(character_id)
        
        # 读取现有记录
        conversations = []
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    conversations = json.load(f)
            except Exception:
                conversations = []
        
        # 添加新记录
        conversation = {
            "id": len(conversations) + 1,
            "character_id": character_id,
            "user_message": user_message,
            "character_response": character_response,
            "consistency_score": consistency_score,
            "consistency_feedback": consistency_feedback,
            "created_at": datetime.utcnow().isoformat()
        }
        
        conversations.append(conversation)
        
        # 保存到文件
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(conversations, f, ensure_ascii=False, indent=2)
        
        return conversation
    
    def get_conversations(self, character_id: str, limit: Optional[int] = None) -> List[Dict]:
        """
        获取对话历史
        
        Args:
            character_id: 角色ID
            limit: 限制返回数量（None表示返回全部）
        
        Returns:
            对话记录列表（按时间倒序）
        """
        file_path = self._get_file_path(character_id)
        
        if not os.path.exists(file_path):
            return []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                conversations = json.load(f)
            
            # 按时间倒序排序
            conversations.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            if limit:
                return conversations[:limit]
            return conversations
        except Exception:
            return []

