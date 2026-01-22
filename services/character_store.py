import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from config import Config


class CharacterStore:
    """文件化人物卡存储"""

    def __init__(self, config: Config):
        self.config = config
        self.base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", self.config.CHARACTER_CONFIG_DIR)
        )
        os.makedirs(self.base_dir, exist_ok=True)

    def _file_path(self, character_id: str, theme: str) -> str:
        """
        获取人物卡文件路径
        优先从 themes/{theme}/characters/ 目录查找，如果不存在则从 themes/{theme}/ 目录查找（兼容旧格式）
        """
        # 新格式：themes/{theme}/characters/{character_id}.json
        characters_dir = os.path.join(self.base_dir, theme, "characters")
        new_path = os.path.join(characters_dir, f"{character_id}.json")
        if os.path.exists(new_path):
            return new_path
        
        # 旧格式：themes/{theme}/{character_id}.json（兼容）
        theme_dir = os.path.join(self.base_dir, theme)
        old_path = os.path.join(theme_dir, f"{character_id}.json")
        return old_path

    def _find_file(self, character_id: str) -> Optional[str]:
        """在所有主题目录下查找人物文件"""
        for root, _, files in os.walk(self.base_dir):
            for filename in files:
                if filename == f"{character_id}.json":
                    return os.path.join(root, filename)
        return None

    def list_characters(self) -> List[Dict]:
        """
        列出所有人物卡
        优先从 themes/{theme}/characters/ 目录查找，也兼容旧格式
        """
        characters = []
        loaded_ids = set()  # 用于去重
        
        # 遍历所有主题目录
        for theme_dir in os.listdir(self.base_dir):
            theme_path = os.path.join(self.base_dir, theme_dir)
            if not os.path.isdir(theme_path):
                continue
            
            # 优先从新格式目录查找：themes/{theme}/characters/
            characters_subdir = os.path.join(theme_path, "characters")
            if os.path.exists(characters_subdir):
                for filename in os.listdir(characters_subdir):
                    if filename.endswith(".json"):
                        character_id = filename.replace(".json", "")
                        if character_id not in loaded_ids:
                            data = self.get_character(character_id)
                            if data:
                                characters.append(data)
                                loaded_ids.add(character_id)
            
            # 兼容旧格式：themes/{theme}/
            for filename in os.listdir(theme_path):
                if filename.endswith(".json") and filename not in ["core_events.json", "random_events.json", "scene_network.json", "monster_bindings.json"]:
                    character_id = filename.replace(".json", "")
                    if character_id not in loaded_ids:
                        data = self.get_character(character_id)
                        if data:
                            characters.append(data)
                            loaded_ids.add(character_id)
        
        return sorted(characters, key=lambda x: x.get("created_at", ""))

    def create_character(
        self,
        name: str,
        description: str,
        attributes: Optional[Dict] = None,
        theme: str = "default",
    ) -> Dict:
        character_id = uuid4().hex
        now = datetime.utcnow().isoformat()
        data = {
            "id": character_id,
            "name": name,
            "description": description,
            "attributes": attributes or {},
            "theme": theme,
            "created_at": now,
            "updated_at": now,
        }
        self._save(character_id, data, theme)
        return data

    def get_character(self, character_id: str) -> Optional[Dict]:
        path = self._find_file(character_id)
        if not path:
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def update_character(self, character_id: str, payload: Dict) -> Optional[Dict]:
        data = self.get_character(character_id)
        if not data:
            return None
        changed = False
        for key in ["name", "description", "attributes", "theme"]:
            if key in payload:
                data[key] = payload[key]
                changed = True
        if changed:
            data["updated_at"] = datetime.utcnow().isoformat()
            theme = data.get("theme", "default")
            self._save(character_id, data, theme)
        return data

    def delete_character(self, character_id: str) -> bool:
        path = self._find_file(character_id)
        if not path:
            return False
        os.remove(path)
        return True

    def _save(self, character_id: str, data: Dict, theme: str) -> None:
        """
        保存人物卡
        优先保存到 themes/{theme}/characters/ 目录（新格式）
        """
        # 使用新格式目录
        characters_dir = os.path.join(self.base_dir, theme, "characters")
        os.makedirs(characters_dir, exist_ok=True)
        path = os.path.join(characters_dir, f"{character_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

