"""
时间管理器：管理游戏内时间流逝
"""
import json
import os
from typing import Dict, Optional
from datetime import datetime, timedelta
from config import Config


class TimeManager:
    """时间管理器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    def get_game_time(self, theme: str, save_step: str) -> Dict:
        """
        获取游戏内时间
        
        Args:
            theme: 主题
            save_step: 存档步骤
            
        Returns:
            游戏时间字典，包含：
            - start_time: 游戏开始时间（ISO格式）
            - current_time: 当前游戏时间（ISO格式）
            - elapsed_time: 已流逝的游戏时间（秒）
            - game_time: 游戏内时间（如：第1天 14:30）
        """
        time_file = os.path.join(
            self.base_dir,
            self.config.SAVE_DIR,
            theme,
            save_step,
            "GAME_TIME.json"
        )
        
        if os.path.exists(time_file):
            try:
                with open(time_file, "r", encoding="utf-8") as f:
                    time_data = json.load(f)
                    return time_data
            except Exception:
                pass
        
        # 返回默认时间（游戏开始）
        default_time = {
            "start_time": datetime.now().isoformat(),
            "current_time": datetime.now().isoformat(),
            "elapsed_time": 0,
            "game_time": {
                "day": 1,
                "hour": 12,
                "minute": 0
            }
        }
        return default_time
    
    def update_game_time(self, theme: str, save_step: str, elapsed_seconds: float) -> bool:
        """
        更新游戏内时间
        
        Args:
            theme: 主题
            save_step: 存档步骤
            elapsed_seconds: 流逝的秒数（游戏内时间）
            
        Returns:
            是否更新成功
        """
        step_dir = os.path.join(self.base_dir, self.config.SAVE_DIR, theme, save_step)
        os.makedirs(step_dir, exist_ok=True)
        
        time_file = os.path.join(step_dir, "GAME_TIME.json")
        
        # 读取现有时间
        current_time_data = self.get_game_time(theme, save_step)
        
        # 更新流逝时间
        current_time_data["elapsed_time"] = current_time_data.get("elapsed_time", 0) + elapsed_seconds
        current_time_data["current_time"] = datetime.now().isoformat()
        
        # 更新游戏内时间（假设1秒游戏时间 = 1分钟游戏内时间）
        game_time = current_time_data.get("game_time", {"day": 1, "hour": 12, "minute": 0})
        total_minutes = game_time["hour"] * 60 + game_time["minute"] + int(elapsed_seconds)
        
        # 计算新的游戏内时间
        new_day = game_time["day"] + total_minutes // (24 * 60)
        remaining_minutes = total_minutes % (24 * 60)
        new_hour = remaining_minutes // 60
        new_minute = remaining_minutes % 60
        
        current_time_data["game_time"] = {
            "day": new_day,
            "hour": new_hour,
            "minute": new_minute
        }
        
        try:
            with open(time_file, "w", encoding="utf-8") as f:
                json.dump(current_time_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"更新游戏时间失败: {e}")
            return False
    
    def format_game_time(self, game_time: Dict) -> str:
        """
        格式化游戏内时间为字符串
        
        Args:
            game_time: 游戏时间字典
            
        Returns:
            格式化的时间字符串，如："第1天 14:30"
        """
        day = game_time.get("day", 1)
        hour = game_time.get("hour", 12)
        minute = game_time.get("minute", 0)
        return f"第{day}天 {hour:02d}:{minute:02d}"
    
    def get_time_since_last_event(self, theme: str, save_step: str) -> float:
        """
        获取距离上次事件的时间（秒）
        
        Args:
            theme: 主题
            save_step: 存档步骤
            
        Returns:
            距离上次事件的秒数
        """
        # 从场景状态中获取上次事件时间
        state_file = os.path.join(
            self.base_dir,
            self.config.SAVE_DIR,
            theme,
            save_step,
            "SCENE_STATE.json"
        )
        
        if os.path.exists(state_file):
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    last_event_time = state.get("last_event_time", 0)
                    current_time_data = self.get_game_time(theme, save_step)
                    current_elapsed = current_time_data.get("elapsed_time", 0)
                    return current_elapsed - last_event_time
            except Exception:
                pass
        
        return 0.0

