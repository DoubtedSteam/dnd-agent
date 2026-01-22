"""
对话历史管理：保存和加载最近N个步骤的指令和摘要
"""
import os
import json
from typing import List, Dict, Optional
from config import Config


class ConversationHistory:
    """对话历史管理器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    def save_conversation(self, theme: str, step: str, instruction: str, summary: str) -> bool:
        """
        保存对话历史（指令和摘要）
        
        Args:
            theme: 主题
            step: 存档步骤
            instruction: 玩家指令
            summary: 响应摘要
        
        Returns:
            是否保存成功
        """
        history_file = os.path.join(
            self.base_dir,
            self.config.SAVE_DIR,
            theme,
            step,
            "HISTORY.json"
        )
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            
            # 每个步骤只保存一条记录（该步骤创建时的指令和摘要）
            # 如果步骤已存在历史记录，覆盖而不是追加
            record = {
                "step": step,
                "instruction": instruction,
                "summary": summary
            }
            
            # 保存（每个步骤只有一条记录）
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump([record], f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存对话历史失败: {e}")
            return False
    
    def load_recent_history(self, theme: str, current_step: str, limit: int = 5) -> List[Dict]:
        """
        加载最近的对话历史
        
        Args:
            theme: 主题
            current_step: 当前步骤
            limit: 最多加载多少个步骤
        
        Returns:
            对话历史列表，按步骤顺序（从旧到新）
        """
        history_list = []
        
        # 获取所有步骤
        steps_dir = os.path.join(self.base_dir, self.config.SAVE_DIR, theme)
        if not os.path.exists(steps_dir):
            return history_list
        
        # 获取所有步骤并排序
        all_steps = []
        for item in os.listdir(steps_dir):
            item_path = os.path.join(steps_dir, item)
            if os.path.isdir(item_path) and item.endswith("_step"):
                all_steps.append(item)
        
        # 按步骤号排序
        def step_key(step):
            try:
                return int(step.replace("_step", ""))
            except ValueError:
                return 999999
        
        all_steps = sorted(all_steps, key=step_key)
        
        # 找到当前步骤的位置
        try:
            current_index = all_steps.index(current_step)
        except ValueError:
            current_index = len(all_steps)
        
        # 获取当前步骤之前的步骤（最多limit个）
        start_index = max(0, current_index - limit)
        steps_to_load = all_steps[start_index:current_index]
        
        # 加载每个步骤的历史
        for step in steps_to_load:
            history_file = os.path.join(steps_dir, step, "HISTORY.json")
            if os.path.exists(history_file):
                try:
                    with open(history_file, "r", encoding="utf-8") as f:
                        step_history = json.load(f)
                        # 取最后一条记录（该步骤的指令和摘要）
                        if step_history:
                            history_list.append(step_history[-1])
                except:
                    pass
        
        return history_list
    
    def get_history_text(self, history_list: List[Dict]) -> str:
        """
        将历史列表转换为文本格式（用于prompt）
        
        Args:
            history_list: 历史列表
        
        Returns:
            格式化的历史文本
        """
        if not history_list:
            return ""
        
        lines = ["【对话历史（最近5个步骤）】"]
        for i, record in enumerate(history_list, 1):
            step = record.get('step', '未知')
            instruction = record.get('instruction', '')
            summary = record.get('summary', '')
            lines.append(f"\n步骤 {step}:")
            lines.append(f"  玩家指令: {instruction}")
            lines.append(f"  摘要: {summary}")
        
        return "\n".join(lines)

