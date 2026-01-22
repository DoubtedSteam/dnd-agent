"""
存档管理器：管理存档步骤的创建和复制
"""
import os
import shutil
import json
from typing import Optional, List, Dict
from config import Config


class SaveManager:
    """存档管理器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    def get_next_step(self, theme: str, current_step: Optional[str] = None) -> str:
        """
        获取下一个存档步骤名称
        
        Args:
            theme: 主题
            current_step: 当前步骤（如 "0_step"），如果为None则从0开始
        
        Returns:
            下一个步骤名称（如 "1_step"）
        """
        if current_step is None:
            return "0_step"
        
        # 提取当前步骤号
        try:
            step_num = int(current_step.replace("_step", ""))
            next_num = step_num + 1
            return f"{next_num}_step"
        except ValueError:
            # 如果无法解析，使用时间戳
            import time
            return f"{int(time.time())}_step"
    
    def create_new_step(self, theme: str, from_step: str) -> Optional[str]:
        """
        创建新的存档步骤（复制当前步骤的所有文件）
        
        Args:
            theme: 主题
            from_step: 源步骤（如 "0_step"）
        
        Returns:
            新步骤名称（如 "1_step"），如果失败返回None
        """
        next_step = self.get_next_step(theme, from_step)
        
        source_dir = os.path.join(self.base_dir, self.config.SAVE_DIR, theme, from_step)
        target_dir = os.path.join(self.base_dir, self.config.SAVE_DIR, theme, next_step)
        
        # 如果源目录不存在，尝试从初始场景和角色文件创建0_step
        if not os.path.exists(source_dir):
            if from_step == "0_step":
                # 尝试初始化0_step
                if self._initialize_0_step(theme):
                    # 初始化成功，源目录现在应该存在了
                    if not os.path.exists(source_dir):
                        print(f"初始化0_step失败，源目录不存在: {source_dir}")
                        return None
                else:
                    print(f"无法初始化0_step，源目录不存在: {source_dir}")
                    return None
            else:
                print(f"源步骤目录不存在: {source_dir}")
                return None
        
        try:
            # 创建目标目录
            os.makedirs(target_dir, exist_ok=True)
            
            # 复制所有文件
            for item in os.listdir(source_dir):
                source_path = os.path.join(source_dir, item)
                target_path = os.path.join(target_dir, item)
                
                if os.path.isfile(source_path):
                    shutil.copy2(source_path, target_path)
                elif os.path.isdir(source_path):
                    shutil.copytree(source_path, target_path)
            
            return next_step
        except Exception as e:
            print(f"创建新存档步骤失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _initialize_0_step(self, theme: str) -> bool:
        """
        初始化0_step目录（基于新剧本系统）
        
        Args:
            theme: 主题
        
        Returns:
            是否初始化成功
        """
        try:
            from services.script_manager import ScriptManager
            from services.scene_state_manager import SceneStateManager
            
            # 创建0_step目录
            step_dir = os.path.join(self.base_dir, self.config.SAVE_DIR, theme, "0_step")
            os.makedirs(step_dir, exist_ok=True)
            
            # 初始化剧本管理器和场景状态管理器
            script_manager = ScriptManager(self.config)
            scene_state_manager = SceneStateManager(self.config)
            
            # 获取起始场景ID
            starting_scene_id = script_manager.get_starting_scene_id(theme)
            if not starting_scene_id:
                print(f"无法获取起始场景ID: theme={theme}")
                return False
            
            # 设置初始场景ID
            scene_state_manager.set_current_scene(theme, "0_step", starting_scene_id)
            scene_state_manager.set_current_room(theme, "0_step", None)  # 初始在一级场景中
            
            # 初始化场景状态
            initial_state = {
                "scene_id": starting_scene_id,
                "room_id": None,
                "state_changes": {},
                "triggered_events": []
            }
            state_file = os.path.join(step_dir, "SCENE_STATE.json")
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(initial_state, f, ensure_ascii=False, indent=2)
            
            # 从themes目录复制所有角色文件
            # 优先从新格式目录查找：themes/{theme}/characters/
            source_characters_dir = os.path.join(self.base_dir, self.config.CHARACTER_CONFIG_DIR, theme, "characters")
            if not os.path.exists(source_characters_dir):
                # 兼容旧格式：themes/{theme}/
                source_characters_dir = os.path.join(self.base_dir, self.config.CHARACTER_CONFIG_DIR, theme)
            
            if os.path.exists(source_characters_dir):
                for item in os.listdir(source_characters_dir):
                    if item.endswith('.json') and not item.startswith('.'):
                        # 排除非角色卡文件
                        if item in ['core_events.json', 'random_events.json', 'scene_network.json', 'monster_bindings.json']:
                            continue
                        source_char = os.path.join(source_characters_dir, item)
                        target_char = os.path.join(step_dir, item)
                        shutil.copy2(source_char, target_char)
            
            return True
        except Exception as e:
            print(f"初始化0_step失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def list_steps(self, theme: str) -> List[str]:
        """
        列出所有存档步骤
        
        Args:
            theme: 主题
        
        Returns:
            步骤名称列表（按数字排序）
        """
        theme_dir = os.path.join(self.base_dir, self.config.SAVE_DIR, theme)
        if not os.path.exists(theme_dir):
            return []
        
        steps = []
        for item in os.listdir(theme_dir):
            item_path = os.path.join(theme_dir, item)
            if os.path.isdir(item_path) and item.endswith("_step"):
                steps.append(item)
        
        # 按步骤号排序
        def step_key(step):
            try:
                return int(step.replace("_step", ""))
            except ValueError:
                return 999999
        
        return sorted(steps, key=step_key)
    
    def delete_step(self, theme: str, step: str) -> bool:
        """
        删除指定的存档步骤
        
        Args:
            theme: 主题
            step: 步骤名称（如 "1_step"）
        
        Returns:
            是否删除成功
        """
        step_dir = os.path.join(self.base_dir, self.config.SAVE_DIR, theme, step)
        
        if not os.path.exists(step_dir):
            return False
        
        try:
            shutil.rmtree(step_dir)
            return True
        except Exception as e:
            print(f"删除存档步骤失败: {e}")
            return False
    
    def delete_all_steps(self, theme: str, keep_steps: List[str] = None) -> Dict[str, bool]:
        """
        删除主题下的所有存档步骤（可保留指定步骤）
        
        Args:
            theme: 主题
            keep_steps: 要保留的步骤列表（如 ["0_step", "1_step"]），如果为None则保留0_step
        
        Returns:
            删除结果字典 {step: success}
        """
        if keep_steps is None:
            keep_steps = ["0_step"]  # 默认保留初始步骤
        
        steps = self.list_steps(theme)
        results = {}
        
        for step in steps:
            if step not in keep_steps:
                results[step] = self.delete_step(theme, step)
        
        return results
    
    def delete_theme(self, theme: str) -> bool:
        """
        删除整个主题的所有存档
        
        Args:
            theme: 主题名称
        
        Returns:
            是否删除成功
        """
        theme_dir = os.path.join(self.base_dir, self.config.SAVE_DIR, theme)
        
        if not os.path.exists(theme_dir):
            return False
        
        try:
            shutil.rmtree(theme_dir)
            return True
        except Exception as e:
            print(f"删除主题存档失败: {e}")
            return False
    
    def get_step_size(self, theme: str, step: str) -> int:
        """
        获取存档步骤的大小（字节）
        
        Args:
            theme: 主题
            step: 步骤名称
        
        Returns:
            大小（字节）
        """
        step_dir = os.path.join(self.base_dir, self.config.SAVE_DIR, theme, step)
        
        if not os.path.exists(step_dir):
            return 0
        
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(step_dir):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(filepath)
        except:
            pass
        
        return total_size
    
    def get_theme_size(self, theme: str) -> int:
        """
        获取主题所有存档的总大小（字节）
        
        Args:
            theme: 主题名称
        
        Returns:
            总大小（字节）
        """
        steps = self.list_steps(theme)
        total_size = 0
        
        for step in steps:
            total_size += self.get_step_size(theme, step)
        
        return total_size

