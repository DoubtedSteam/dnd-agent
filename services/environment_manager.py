"""
环境管理器：管理场景状态、处理智能体响应、更新环境
"""
import os
from typing import Dict, List, Optional
from config import Config
from services.script_manager import ScriptManager
from services.scene_state_manager import SceneStateManager


class EnvironmentManager:
    """环境管理器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.script_manager = ScriptManager(config)
        self.scene_state_manager = SceneStateManager(config)
    
    def load_scene(self, theme: str, save_step: Optional[str] = None) -> Optional[str]:
        """
        加载场景内容（基于剧本系统）
        
        Args:
            theme: 主题
            save_step: 存档步骤
            
        Returns:
            场景内容（从场景剧本的"表"部分生成）
        """
        if not save_step:
            return None
        
        # 获取当前场景ID和房间ID
        scene_id = self.scene_state_manager.get_current_scene_id(theme, save_step)
        room_id = self.scene_state_manager.get_current_room_id(theme, save_step)
        
        if not scene_id:
            return None
        
        # 读取场景状态（包含怪物和事件信息）
        scene_state = self.scene_state_manager.get_scene_state(theme, save_step)
        state_changes = scene_state.get("state_changes", {})
        monsters_info = state_changes.get("monsters", {})
        
        # 加载场景剧本
        if room_id:
            # 如果在房间中，加载房间剧本
            room_script = self.script_manager.load_room_script(theme, room_id)
            if room_script:
                # 从房间剧本的"表"部分生成场景描述
                surface = room_script.get("surface", {})
                description = surface.get("description", "")
                state = surface.get("state", {})
                
                # 合并怪物信息到场景描述中
                if monsters_info and monsters_info.get("monster_description"):
                    monster_desc = monsters_info.get("monster_description", "")
                    if description:
                        description = f"{description}\n\n{monster_desc}"
                    else:
                        description = monster_desc
                
                # 组合场景描述和状态
                scene_content = self._build_scene_content(description, state, room_id, scene_id, monsters_info)
                return scene_content
        else:
            # 如果在一级场景中，加载场景剧本
            scene_script = self.script_manager.load_scene_script(theme, scene_id)
            if scene_script:
                # 从场景剧本的"表"部分生成场景描述
                surface = scene_script.get("surface", {})
                description = surface.get("description", "")
                state = surface.get("state", {})
                
                # 合并怪物信息到场景描述中
                if monsters_info and monsters_info.get("monster_description"):
                    monster_desc = monsters_info.get("monster_description", "")
                    if description:
                        description = f"{description}\n\n{monster_desc}"
                    else:
                        description = monster_desc
                
                # 组合场景描述和状态
                scene_content = self._build_scene_content(description, state, None, scene_id, monsters_info)
                return scene_content
        
        return None
    
    def _build_scene_content(self, description: str, state: Dict, room_id: Optional[str], scene_id: str, monsters_info: Optional[Dict] = None) -> str:
        """
        构建场景内容
        
        Args:
            description: 场景描述
            state: 场景状态
            room_id: 房间ID
            scene_id: 场景ID
            monsters_info: 怪物信息（从SCENE_STATE.json读取）
        """
        lines = [description]
        
        if state:
            lines.append("\n## 场景状态")
            for key, value in state.items():
                if key == "地点" and isinstance(value, dict):
                    # 地点是字典，格式化显示
                    lines.append(f"- **{key}**：")
                    for sub_key, sub_value in value.items():
                        lines.append(f"  - {sub_key}：{sub_value}")
                elif key == "可见元素" and isinstance(value, list):
                    # 可见元素是列表，每行一个
                    lines.append(f"- **{key}**：")
                    for element in value:
                        lines.append(f"  - {element}")
                else:
                    # 其他字段正常显示
                    lines.append(f"- **{key}**：{value}")
        
        # 添加怪物信息到场景状态（如果存在）
        if monsters_info:
            appeared_monsters = monsters_info.get("appeared_monsters", [])
            if appeared_monsters:
                monster_list = ", ".join(appeared_monsters) if isinstance(appeared_monsters, list) else str(appeared_monsters)
                lines.append(f"- **出现的怪物**：{monster_list}")
        
        # 添加场景ID元数据（注释形式）
        lines.append(f"\n<!-- scene_id: {scene_id} -->")
        if room_id:
            lines.append(f"<!-- room_id: {room_id} -->")
        
        return "\n".join(lines)
    
    
    def update_scene(self, theme: str, save_step: str, scene_changes: Dict) -> bool:
        """
        更新场景文件
        
        Args:
            theme: 主题
            save_step: 存档步骤
            scene_changes: 场景变化
        
        Returns:
            是否更新成功
        """
        scene_path = os.path.join(self.base_dir, self.config.SAVE_DIR, theme, save_step, "SCENE.md")
        if not os.path.exists(scene_path):
            return False
        
        try:
            # 读取当前场景
            with open(scene_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 这里可以添加场景更新逻辑
            # 暂时只返回成功
            
            return True
        except Exception:
            return False

