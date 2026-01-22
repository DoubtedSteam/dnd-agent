"""
场景状态管理器：管理基于场景ID和房间ID的存档系统
"""
import os
import json
from typing import Dict, Optional
from config import Config


class SceneStateManager:
    """场景状态管理器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    def get_current_scene_id(self, theme: str, save_step: str) -> Optional[str]:
        """
        获取当前场景ID
        
        Args:
            theme: 主题
            save_step: 存档步骤
            
        Returns:
            场景ID，如果不存在返回None
        """
        scene_id_file = os.path.join(
            self.base_dir,
            self.config.SAVE_DIR,
            theme,
            save_step,
            "SCENE_ID.txt"
        )
        
        if os.path.exists(scene_id_file):
            try:
                with open(scene_id_file, "r", encoding="utf-8") as f:
                    scene_id = f.read().strip()
                    return scene_id if scene_id else None
            except Exception:
                pass
        
        return None
    
    def get_current_room_id(self, theme: str, save_step: str) -> Optional[str]:
        """
        获取当前房间ID
        
        Args:
            theme: 主题
            save_step: 存档步骤
            
        Returns:
            房间ID，如果不存在或在一级场景中返回None
        """
        room_id_file = os.path.join(
            self.base_dir,
            self.config.SAVE_DIR,
            theme,
            save_step,
            "ROOM_ID.txt"
        )
        
        if os.path.exists(room_id_file):
            try:
                with open(room_id_file, "r", encoding="utf-8") as f:
                    room_id = f.read().strip()
                    return room_id if room_id else None
            except Exception:
                pass
        
        return None
    
    def set_current_scene(self, theme: str, save_step: str, scene_id: str) -> bool:
        """
        设置当前场景ID
        
        Args:
            theme: 主题
            save_step: 存档步骤
            scene_id: 场景ID
            
        Returns:
            是否设置成功
        """
        step_dir = os.path.join(self.base_dir, self.config.SAVE_DIR, theme, save_step)
        os.makedirs(step_dir, exist_ok=True)
        
        scene_id_file = os.path.join(step_dir, "SCENE_ID.txt")
        
        try:
            with open(scene_id_file, "w", encoding="utf-8") as f:
                f.write(scene_id)
            return True
        except Exception as e:
            print(f"设置场景ID失败: {e}")
            return False
    
    def set_current_room(self, theme: str, save_step: str, room_id: Optional[str]) -> bool:
        """
        设置当前房间ID
        
        Args:
            theme: 主题
            save_step: 存档步骤
            room_id: 房间ID，如果为None则清除房间ID（表示在一级场景中）
            
        Returns:
            是否设置成功
        """
        step_dir = os.path.join(self.base_dir, self.config.SAVE_DIR, theme, save_step)
        os.makedirs(step_dir, exist_ok=True)
        
        room_id_file = os.path.join(step_dir, "ROOM_ID.txt")
        
        try:
            if room_id:
                with open(room_id_file, "w", encoding="utf-8") as f:
                    f.write(room_id)
            else:
                # 如果room_id为None，删除文件（表示在一级场景中）
                if os.path.exists(room_id_file):
                    os.remove(room_id_file)
            return True
        except Exception as e:
            print(f"设置房间ID失败: {e}")
            return False
    
    def get_scene_state(self, theme: str, save_step: str) -> Dict:
        """
        获取场景状态
        
        Args:
            theme: 主题
            save_step: 存档步骤
            
        Returns:
            场景状态字典
        """
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
                    return json.load(f)
            except Exception:
                pass
        
        # 返回默认状态
        return {
            "scene_id": None,
            "room_id": None,
            "state_changes": {},
            "triggered_events": []  # 已触发的事件ID列表
        }
    
    def update_scene_state(self, theme: str, save_step: str, state_changes: Dict) -> bool:
        """
        更新场景状态
        
        Args:
            theme: 主题
            save_step: 存档步骤
            state_changes: 状态变化字典
            
        Returns:
            是否更新成功
        """
        step_dir = os.path.join(self.base_dir, self.config.SAVE_DIR, theme, save_step)
        os.makedirs(step_dir, exist_ok=True)
        
        state_file = os.path.join(step_dir, "SCENE_STATE.json")
        
        # 读取现有状态
        current_state = self.get_scene_state(theme, save_step)
        
        # 更新状态
        if "state_changes" not in current_state:
            current_state["state_changes"] = {}
        
        current_state["state_changes"].update(state_changes)
        
        # 更新场景ID和房间ID
        scene_id = self.get_current_scene_id(theme, save_step)
        room_id = self.get_current_room_id(theme, save_step)
        current_state["scene_id"] = scene_id
        current_state["room_id"] = room_id
        
        # 确保triggered_events字段存在
        if "triggered_events" not in current_state:
            current_state["triggered_events"] = []
        
        try:
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(current_state, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"更新场景状态失败: {e}")
            return False
    
    def add_triggered_event(self, theme: str, save_step: str, event_id: str) -> bool:
        """
        记录已触发的事件
        
        Args:
            theme: 主题
            save_step: 存档步骤
            event_id: 事件ID
            
        Returns:
            是否添加成功
        """
        current_state = self.get_scene_state(theme, save_step)
        
        if "triggered_events" not in current_state:
            current_state["triggered_events"] = []
        
        # 避免重复添加
        if event_id not in current_state["triggered_events"]:
            current_state["triggered_events"].append(event_id)
            return self.update_scene_state(theme, save_step, current_state.get("state_changes", {}))
        
        return True
    
    def get_triggered_events(self, theme: str, save_step: str) -> list:
        """
        获取已触发的事件列表
        
        Args:
            theme: 主题
            save_step: 存档步骤
            
        Returns:
            已触发的事件ID列表
        """
        current_state = self.get_scene_state(theme, save_step)
        return current_state.get("triggered_events", [])
    
    def transition_scene(self, theme: str, save_step: str, target_scene_id: str, 
                        target_room_id: Optional[str] = None) -> bool:
        """
        转换场景/房间
        
        Args:
            theme: 主题
            save_step: 存档步骤
            target_scene_id: 目标场景ID
            target_room_id: 目标房间ID（可选，如果为None表示在一级场景中）
            
        Returns:
            是否转换成功
        """
        # 设置场景ID
        if not self.set_current_scene(theme, save_step, target_scene_id):
            return False
        
        # 设置房间ID
        if not self.set_current_room(theme, save_step, target_room_id):
            return False
        
        # 更新场景状态
        state = {
            "scene_id": target_scene_id,
            "room_id": target_room_id,
            "state_changes": {}
        }
        
        # 记录进入场景/房间的时间
        from services.time_manager import TimeManager
        from config import Config
        time_manager = TimeManager(Config())
        game_time = time_manager.get_game_time(theme, save_step)
        current_elapsed = game_time.get("elapsed_time", 0)
        
        # 更新场景状态，记录进入时间
        state_changes = state.get("state_changes", {})
        state_changes["enter_time"] = current_elapsed
        
        return self.update_scene_state(theme, save_step, state_changes)
    
    def get_enter_time(self, theme: str, save_step: str) -> Optional[float]:
        """
        获取进入当前场景/房间的时间（游戏内时间，单位：秒）
        
        Args:
            theme: 主题
            save_step: 存档步骤
            
        Returns:
            进入时间（秒），如果不存在返回None
        """
        scene_state = self.get_scene_state(theme, save_step)
        state_changes = scene_state.get("state_changes", {})
        return state_changes.get("enter_time")

