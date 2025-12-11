"""
环境管理器：管理场景状态、处理智能体响应、更新环境
"""
import os
from typing import Dict, List, Optional
from config import Config
from services.environment_analyzer import EnvironmentAnalyzer


class EnvironmentManager:
    """环境管理器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.analyzer = EnvironmentAnalyzer(config)
    
    def load_scene(self, theme: str, save_step: Optional[str] = None) -> Optional[str]:
        """加载场景内容"""
        # 优先读取存档场景
        if save_step:
            scene_path = os.path.join(self.base_dir, self.config.SAVE_DIR, theme, save_step, "SCENE.md")
            if os.path.exists(scene_path):
                try:
                    with open(scene_path, "r", encoding="utf-8") as f:
                        return f.read()
                except Exception:
                    pass
        
        # 其次读取初始场景
        scene_path = os.path.join(self.base_dir, self.config.CHARACTER_CONFIG_DIR, theme, "SCENE.md")
        if os.path.exists(scene_path):
            try:
                with open(scene_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
        return None
    
    def apply_responses_to_environment(self, scene_content: str, agent_responses: List[Dict],
                                       platform: str = None) -> Dict:
        """
        将智能体响应应用到环境，分析环境变化
        
        Args:
            scene_content: 当前场景内容
            agent_responses: 所有智能体的响应列表
            platform: API平台（用于LLM分析）
        
        Returns:
            包含环境变化的字典
        """
        # 使用LLM分析环境变化
        return self.analyzer.analyze_environment_changes(
            scene_content,
            agent_responses,
            platform
        )
    
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

