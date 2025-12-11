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
        theme_dir = os.path.join(self.base_dir, theme)
        os.makedirs(theme_dir, exist_ok=True)
        return os.path.join(theme_dir, f"{character_id}.json")

    def _find_file(self, character_id: str) -> Optional[str]:
        """在所有主题目录下查找人物文件"""
        for root, _, files in os.walk(self.base_dir):
            for filename in files:
                if filename == f"{character_id}.json":
                    return os.path.join(root, filename)
        return None

    def list_characters(self) -> List[Dict]:
        characters = []
        for root, _, files in os.walk(self.base_dir):
            for filename in files:
                if not filename.endswith(".json"):
                    continue
                character_id = filename.replace(".json", "")
                data = self.get_character(character_id)
                if data:
                    characters.append(data)
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
        path = self._file_path(character_id, theme)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

