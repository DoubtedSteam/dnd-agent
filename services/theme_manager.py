"""
主题管理器：管理所有可用的主题（剧本）
"""
import os
from typing import List
from config import Config


class ThemeManager:
    """主题管理器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    def list_themes(self) -> List[str]:
        """
        列出所有可用的主题
        
        Returns:
            主题名称列表
        """
        themes = []
        characters_dir = os.path.join(self.base_dir, self.config.CHARACTER_CONFIG_DIR)
        
        if not os.path.exists(characters_dir):
            return themes
        
        # 遍历characters目录，每个子目录是一个主题
        for item in os.listdir(characters_dir):
            item_path = os.path.join(characters_dir, item)
            if os.path.isdir(item_path):
                # 检查是否有SCENE.md文件（表示这是一个有效的主题）
                scene_path = os.path.join(item_path, "SCENE.md")
                if os.path.exists(scene_path):
                    themes.append(item)
        
        return sorted(themes)
    
    def theme_exists(self, theme: str) -> bool:
        """
        检查主题是否存在
        
        Args:
            theme: 主题名称
        
        Returns:
            是否存在
        """
        theme_dir = os.path.join(self.base_dir, self.config.CHARACTER_CONFIG_DIR, theme)
        scene_path = os.path.join(theme_dir, "SCENE.md")
        return os.path.exists(scene_path)

