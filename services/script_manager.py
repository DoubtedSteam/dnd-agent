"""
剧本管理器：管理剧本系统的加载和查询
"""
import os
import json
import re
from typing import Dict, List, Optional, Tuple
from config import Config


class ScriptManager:
    """剧本管理器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self._story_overview_cache = {}  # 故事总览缓存
        self._scene_script_cache = {}  # 场景剧本缓存
        self._room_script_cache = {}  # 房间剧本缓存
        self._monster_cache = {}  # 怪物卡缓存
    
    def load_story_overview(self, theme: str) -> Dict:
        """
        加载故事总览
        
        Args:
            theme: 主题
            
        Returns:
            故事总览字典
        """
        cache_key = theme
        if cache_key in self._story_overview_cache:
            return self._story_overview_cache[cache_key]
        
        overview_path = os.path.join(
            self.base_dir,
            self.config.CHARACTER_CONFIG_DIR,
            theme,
            "STORY_OVERVIEW.md"
        )
        
        if not os.path.exists(overview_path):
            return {}
        
        try:
            with open(overview_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            overview = self._parse_story_overview(content, overview_path)
            self._story_overview_cache[cache_key] = overview
            return overview
        except Exception as e:
            print(f"加载故事总览失败: {e}")
            return {}
    
    def _parse_story_overview(self, content: str, overview_path: str) -> Dict:
        """解析故事总览内容"""
        overview = {
            "plot_main": "",
            "core_conflict": "",
            "final_goal": "",
            "scenes": [],
            "rooms": [],
            "scene_network": {},
            "room_network": {},
            "core_events": [],
            "director_guidance": "",
            "important_characters": []  # 重要角色列表（需要角色卡）
        }
        
        # 解析剧情主线
        plot_match = re.search(r'## 剧情主线\s*\n(.*?)(?=\n##|$)', content, re.DOTALL)
        if plot_match:
            plot_text = plot_match.group(1).strip()
            lines = plot_text.split('\n')
            for line in lines:
                if '主线描述' in line or '主线' in line:
                    overview["plot_main"] = line.split('：', 1)[-1].strip() if '：' in line else line.strip()
                elif '核心冲突' in line:
                    overview["core_conflict"] = line.split('：', 1)[-1].strip() if '：' in line else line.strip()
                elif '最终目标' in line:
                    overview["final_goal"] = line.split('：', 1)[-1].strip() if '：' in line else line.strip()
        
        # 解析场景池
        scenes_section = re.search(r'### 一级场景列表.*?\n(.*?)(?=\n###|##|$)', content, re.DOTALL)
        if scenes_section:
            scene_lines = scenes_section.group(1).strip().split('\n')
            for line in scene_lines:
                if line.strip().startswith('-'):
                    # 解析格式: - scene_001: 冒险者公会大厅（起始场景）
                    match = re.match(r'-\s*(\w+):\s*(.+?)(?:（(.+?)）)?$', line.strip())
                    if match:
                        scene_id, name, desc = match.groups()
                        overview["scenes"].append({
                            "id": scene_id,
                            "name": name.strip(),
                            "description": desc.strip() if desc else ""
                        })
        
        # 解析房间列表
        rooms_section = re.search(r'### 二级场景列表.*?\n(.*?)(?=\n###|##|$)', content, re.DOTALL)
        if rooms_section:
            room_lines = rooms_section.group(1).strip().split('\n')
            current_scene = None
            for line in room_lines:
                if line.strip().startswith('####'):
                    # 解析格式: #### scene_006 (魔王城) 的房间
                    match = re.search(r'\((\w+)\)', line)
                    if match:
                        current_scene = match.group(1)
                elif line.strip().startswith('-') and current_scene:
                    match = re.match(r'-\s*(\w+):\s*(.+?)(?:（(.+?)）)?$', line.strip())
                    if match:
                        room_id, name, desc = match.groups()
                        overview["rooms"].append({
                            "id": room_id,
                            "parent_scene": current_scene,
                            "name": name.strip(),
                            "description": desc.strip() if desc else ""
                        })
        
        # 加载场景连接网络（从JSON文件）
        network_file = os.path.join(
            os.path.dirname(overview_path),
            "scene_network.json"
        )
        if os.path.exists(network_file):
            try:
                with open(network_file, "r", encoding="utf-8") as f:
                    network_data = json.load(f)
                    overview["scene_network"] = network_data.get("scene_network", {})
                    overview["room_network"] = network_data.get("room_network", {})
            except Exception as e:
                print(f"加载场景连接网络失败: {e}")
        
        # 加载核心事件（从JSON文件）
        core_events_file = os.path.join(
            os.path.dirname(overview_path),
            "core_events.json"
        )
        if os.path.exists(core_events_file):
            try:
                with open(core_events_file, "r", encoding="utf-8") as f:
                    events_data = json.load(f)
                    overview["core_events"] = events_data.get("core_events", [])
            except Exception as e:
                print(f"加载核心事件失败: {e}")
        
        # 加载随机事件（从JSON文件）
        random_events_file = os.path.join(
            os.path.dirname(overview_path),
            "random_events.json"
        )
        if os.path.exists(random_events_file):
            try:
                with open(random_events_file, "r", encoding="utf-8") as f:
                    random_data = json.load(f)
                    overview["random_events"] = random_data.get("random_events", [])
            except Exception as e:
                print(f"加载随机事件失败: {e}")
        
        # 解析导演指引
        guidance_section = re.search(r'## 导演指引.*?\n(.*?)(?=\n##|$)', content, re.DOTALL)
        if guidance_section:
            overview["director_guidance"] = guidance_section.group(1).strip()
        
        # 解析重要角色列表
        important_chars_section = re.search(r'### 重要角色列表.*?\n(.*?)(?=\n###|##|$)', content, re.DOTALL)
        if important_chars_section:
            char_text = important_chars_section.group(1).strip()
            # 查找"重要角色"部分
            important_section = re.search(r'\*\*重要角色\*\*.*?\n(.*?)(?=\*\*|$)', char_text, re.DOTALL)
            if important_section:
                char_lines = important_section.group(1).strip().split('\n')
                for line in char_lines:
                    if line.strip().startswith('-'):
                        # 解析格式: - 角色名：描述
                        match = re.match(r'-\s*(.+?)(?:：|:)\s*(.+)$', line.strip())
                        if match:
                            name, desc = match.groups()
                            overview["important_characters"].append({
                                "name": name.strip(),
                                "description": desc.strip()
                            })
        
        return overview
    
    def _parse_scene_network(self, network_text: str) -> Dict:
        """解析场景连接网络"""
        network = {}
        current_scene = None
        
        for line in network_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # 匹配场景定义行: scene_001 (公会大厅)
            scene_match = re.match(r'(\w+)\s*\([^)]+\)', line)
            if scene_match:
                current_scene = scene_match.group(1)
                if current_scene not in network:
                    network[current_scene] = []
            elif line.startswith('├─>') or line.startswith('└─>'):
                # 匹配连接行: ├─> scene_002 (森林小径) [可通过事件：接受任务]
                match = re.match(r'[├└]─>\s*(\w+)\s*\([^)]+\)(?:\s*\[(.+?)\])?', line)
                if match and current_scene:
                    target_scene = match.group(1)
                    condition = match.group(2) if match.group(2) else ""
                    network[current_scene].append({
                        "target": target_scene,
                        "condition": condition,
                        "type": "scene"
                    })
        
        return network
    
    def _parse_room_network(self, network_text: str) -> Dict:
        """解析房间连接网络"""
        network = {}
        current_room = None
        current_scene = None
        
        for line in network_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # 匹配场景标题: scene_006 (魔王城) 的房间连接：
            scene_match = re.search(r'(\w+)\s*\([^)]+\)\s*的房间连接', line)
            if scene_match:
                current_scene = scene_match.group(1)
                continue
            
            # 匹配房间定义行: room_006_001 (入口大厅)
            room_match = re.match(r'(\w+)\s*\([^)]+\)', line)
            if room_match:
                current_room = room_match.group(1)
                if current_room not in network:
                    network[current_room] = []
            elif line.startswith('├─>') or line.startswith('└─>'):
                # 匹配连接行
                match = re.match(r'[├└]─>\s*(\w+)\s*\([^)]+\)(?:\s*\[(.+?)\])?', line)
                if match and current_room:
                    target = match.group(1)
                    condition = match.group(2) if match.group(2) else ""
                    target_type = "room" if target.startswith("room_") else "scene"
                    network[current_room].append({
                        "target": target,
                        "condition": condition,
                        "type": target_type
                    })
        
        return network
    
    def load_scene_script(self, theme: str, scene_id: str) -> Dict:
        """
        加载一级场景剧本（优先JSON格式，如果不存在则回退到Markdown）
        
        Args:
            theme: 主题
            scene_id: 场景ID
            
        Returns:
            场景剧本字典
        """
        cache_key = f"{theme}:{scene_id}"
        if cache_key in self._scene_script_cache:
            return self._scene_script_cache[cache_key]
        
        # 优先尝试加载JSON格式（支持可读文件名：scene_001_名称.json）
        scenarios_dir = os.path.join(
            self.base_dir,
            self.config.CHARACTER_CONFIG_DIR,
            theme,
            "scenarios"
        )
        
        # 查找匹配的文件（支持 scene_id.json 或 scene_id_*.json 格式）
        json_path = None
        if os.path.exists(scenarios_dir):
            for filename in os.listdir(scenarios_dir):
                if filename.endswith('.json') and (filename.startswith(f"{scene_id}_") or filename == f"{scene_id}.json"):
                    json_path = os.path.join(scenarios_dir, filename)
                    break
        
        if json_path and os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    script = json.load(f)
                # 验证 scene_id 是否匹配
                if script.get('scene_id') == scene_id:
                    self._scene_script_cache[cache_key] = script
                    return script
            except Exception as e:
                print(f"加载场景剧本JSON失败: {e}")
        
        # 回退到Markdown格式（向后兼容）
        md_path = os.path.join(
            self.base_dir,
            self.config.CHARACTER_CONFIG_DIR,
            theme,
            "scenarios",
            f"{scene_id}.md"
        )
        
        if not os.path.exists(md_path):
            return {}
        
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            script = self._parse_scene_script(content, scene_id)
            self._scene_script_cache[cache_key] = script
            return script
        except Exception as e:
            print(f"加载场景剧本失败: {e}")
            return {}
    
    def load_room_script(self, theme: str, room_id: str) -> Dict:
        """
        加载二级场景（房间）剧本（优先JSON格式，如果不存在则回退到Markdown）
        
        Args:
            theme: 主题
            room_id: 房间ID
            
        Returns:
            房间剧本字典
        """
        cache_key = f"{theme}:{room_id}"
        if cache_key in self._room_script_cache:
            return self._room_script_cache[cache_key]
        
        # 从房间ID提取场景ID（假设格式为 room_{scene_id}_{number}）
        parts = room_id.split('_')
        if len(parts) >= 3:
            scene_id = f"{parts[0]}_{parts[1]}"
        else:
            return {}
        
        # 优先尝试加载JSON格式（支持可读文件名：room_002_002_名称.json）
        rooms_dir = os.path.join(
            self.base_dir,
            self.config.CHARACTER_CONFIG_DIR,
            theme,
            "scenarios",
            scene_id,
            "rooms"
        )
        
        # 查找匹配的文件（支持 room_id.json 或 room_id_*.json 格式）
        json_path = None
        if os.path.exists(rooms_dir):
            for filename in os.listdir(rooms_dir):
                if filename.endswith('.json') and (filename.startswith(f"{room_id}_") or filename == f"{room_id}.json"):
                    json_path = os.path.join(rooms_dir, filename)
                    break
        
        if json_path and os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    script = json.load(f)
                # 验证 room_id 是否匹配
                if script.get('room_id') == room_id:
                    self._room_script_cache[cache_key] = script
                    return script
            except Exception as e:
                print(f"加载房间剧本JSON失败: {e}")
        
        # 回退到Markdown格式（向后兼容）
        md_path = os.path.join(
            self.base_dir,
            self.config.CHARACTER_CONFIG_DIR,
            theme,
            "scenarios",
            scene_id,
            "rooms",
            f"{room_id}.md"
        )
        
        if not os.path.exists(md_path):
            return {}
        
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            script = self._parse_room_script(content, room_id)
            self._room_script_cache[cache_key] = script
            return script
        except Exception as e:
            print(f"加载房间剧本失败: {e}")
            return {}
    
    def _parse_scene_script(self, content: str, scene_id: str) -> Dict:
        """解析场景剧本内容"""
        script = {
            "scene_id": scene_id,
            "scene_type": "一级场景",
            "surface": {
                "description": "",
                "state": {}
            },
            "hidden": {
                "events": [],
                "monsters": [],
                "director_guidance": "",
                "transition_possibilities": []
            }
        }
        
        # 解析表部分
        surface_section = re.search(r'## 表（玩家可见）\s*\n(.*?)(?=\n##|$)', content, re.DOTALL)
        if surface_section:
            surface_text = surface_section.group(1)
            script["surface"]["description"] = self._extract_section(surface_text, "场景描述")
            script["surface"]["state"] = self._parse_state_section(surface_text)
        
        # 解析里部分
        hidden_section = re.search(r'## 里（LLM推演用，隐藏）\s*\n(.*?)(?=\n##|$)', content, re.DOTALL)
        if hidden_section:
            hidden_text = hidden_section.group(1)
            script["hidden"]["events"] = self._parse_events(hidden_text)
            script["hidden"]["monsters"] = self._parse_monsters(hidden_text)
            script["hidden"]["director_guidance"] = self._extract_section(hidden_text, "导演指引")
            script["hidden"]["transition_possibilities"] = self._parse_transition_possibilities(hidden_text)
        
        return script
    
    def _parse_room_script(self, content: str, room_id: str) -> Dict:
        """解析房间剧本内容（与场景剧本类似）"""
        script = {
            "room_id": room_id,
            "scene_type": "二级场景",
            "parent_scene": None,
            "surface": {
                "description": "",
                "state": {}
            },
            "hidden": {
                "events": [],
                "monsters": [],
                "director_guidance": "",
                "transition_possibilities": []
            }
        }
        
        # 解析所属场景
        parent_match = re.search(r'## 所属场景\s*\n(.+?)(?=\n##|$)', content)
        if parent_match:
            script["parent_scene"] = parent_match.group(1).strip()
        
        # 解析表部分和里部分（与场景剧本相同）
        surface_section = re.search(r'## 表（玩家可见）\s*\n(.*?)(?=\n##|$)', content, re.DOTALL)
        if surface_section:
            surface_text = surface_section.group(1)
            script["surface"]["description"] = self._extract_section(surface_text, "房间描述")
            script["surface"]["state"] = self._parse_state_section(surface_text)
        
        hidden_section = re.search(r'## 里（LLM推演用，隐藏）\s*\n(.*?)(?=\n##|$)', content, re.DOTALL)
        if hidden_section:
            hidden_text = hidden_section.group(1)
            script["hidden"]["events"] = self._parse_events(hidden_text)
            script["hidden"]["monsters"] = self._parse_monsters(hidden_text)
            script["hidden"]["director_guidance"] = self._extract_section(hidden_text, "导演指引")
            script["hidden"]["transition_possibilities"] = self._parse_transition_possibilities(hidden_text)
        
        return script
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """提取指定部分的内容"""
        pattern = f'### {section_name}.*?\n(.*?)(?=\n###|$)'
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def _parse_state_section(self, text: str) -> Dict:
        """解析状态部分"""
        state = {}
        state_section = re.search(r'### 场景状态.*?\n(.*?)(?=\n###|$)', text, re.DOTALL)
        if state_section:
            state_text = state_section.group(1)
            for line in state_text.split('\n'):
                if '：' in line or ':' in line:
                    parts = re.split('[：:]', line, 1)
                    if len(parts) == 2:
                        key = parts[0].strip().replace('-', '').replace('*', '').strip()
                        value = parts[1].strip()
                        state[key] = value
        return state
    
    def _parse_events(self, text: str) -> List[Dict]:
        """解析潜在事件列表"""
        events = []
        events_section = re.search(r'### 潜在事件列表.*?\n(.*?)(?=\n###|$)', text, re.DOTALL)
        if not events_section:
            return events
        
        events_text = events_section.group(1)
        # 匹配每个事件块
        event_blocks = re.split(r'#### 事件\d+：', events_text)
        
        for block in event_blocks[1:]:  # 跳过第一个空块
            event = self._parse_single_event(block)
            if event:
                events.append(event)
        
        return events
    
    def _parse_single_event(self, block: str) -> Dict:
        """解析单个事件"""
        event = {
            "name": "",
            "event_type": "random",  # 默认为随机事件
            "core_event_id": None,  # 如果是核心事件，关联的核心事件ID
            "trigger_conditions": {},
            "description_template": "",
            "effects": {},
            "director_hints": {}
        }
        
        # 提取事件名称（第一行）
        lines = block.split('\n')
        if lines:
            event["name"] = lines[0].strip()
        
        # 解析事件类型
        type_match = re.search(r'- \*\*事件类型\*\*[：:](.*?)(?=\n|$)', block)
        if type_match:
            event_type = type_match.group(1).strip()
            if "核心事件" in event_type:
                event["event_type"] = "core"
            elif "随机事件" in event_type:
                event["event_type"] = "random"
        
        # 解析关联核心事件ID
        core_id_match = re.search(r'- \*\*关联核心事件ID\*\*[：:](.*?)(?=\n|$)', block)
        if core_id_match:
            event["core_event_id"] = core_id_match.group(1).strip()
        
        # 解析触发条件
        conditions_section = re.search(r'- \*\*触发条件.*?\n(.*?)(?=\n- \*\*|$)', block, re.DOTALL)
        if conditions_section:
            conditions_text = conditions_section.group(1)
            event["trigger_conditions"] = self._parse_conditions(conditions_text)
        
        # 解析事件描述模板
        desc_match = re.search(r'- \*\*事件描述模板\*\*[：:](.*?)(?=\n- \*\*|$)', block, re.DOTALL)
        if desc_match:
            event["description_template"] = desc_match.group(1).strip()
        
        # 解析事件影响
        effects_section = re.search(r'- \*\*事件影响.*?\n(.*?)(?=\n- \*\*|$)', block, re.DOTALL)
        if effects_section:
            effects_text = effects_section.group(1)
            event["effects"] = self._parse_effects(effects_text)
        
        # 解析导演提示
        hints_section = re.search(r'- \*\*导演提示\*\*[：:].*?\n(.*?)(?=\n####|$)', block, re.DOTALL)
        if hints_section:
            hints_text = hints_section.group(1)
            event["director_hints"] = self._parse_director_hints(hints_text)
        
        return event
    
    def _parse_conditions(self, text: str) -> Dict:
        """解析触发条件"""
        conditions = {}
        for line in text.split('\n'):
            if '：' in line or ':' in line:
                parts = re.split('[：:]', line, 1)
                if len(parts) == 2:
                    key = parts[0].strip().replace('-', '').replace('*', '').strip()
                    value = parts[1].strip()
                    conditions[key] = value
        return conditions
    
    def _parse_effects(self, text: str) -> Dict:
        """解析事件影响"""
        effects = {
            "scene_changes": {},
            "character_changes": {},
            "possible_transitions": [],
            "unlocked_events": []
        }
        
        # 解析场景状态变化
        scene_match = re.search(r'场景状态变化[：:](.*?)(?=\n|$)', text)
        if scene_match:
            effects["scene_changes"] = {"description": scene_match.group(1).strip()}
        
        # 解析角色状态变化
        char_match = re.search(r'角色状态变化[：:](.*?)(?=\n|$)', text)
        if char_match:
            effects["character_changes"] = {"description": char_match.group(1).strip()}
        
        # 解析可能触发的场景转换
        trans_match = re.search(r'可能触发的场景转换[：:](.*?)(?=\n|$)', text)
        if trans_match:
            trans_text = trans_match.group(1).strip()
            effects["possible_transitions"] = [t.strip() for t in trans_text.split('、') if t.strip()]
        
        # 解析后续事件解锁
        unlock_match = re.search(r'后续事件解锁[：:](.*?)(?=\n|$)', text)
        if unlock_match:
            unlock_text = unlock_match.group(1).strip()
            effects["unlocked_events"] = [e.strip() for e in unlock_text.split('、') if e.strip()]
        
        return effects
    
    def _parse_director_hints(self, text: str) -> Dict:
        """解析导演提示"""
        hints = {}
        for line in text.split('\n'):
            if '：' in line or ':' in line:
                parts = re.split('[：:]', line, 1)
                if len(parts) == 2:
                    key = parts[0].strip().replace('-', '').replace('*', '').strip()
                    value = parts[1].strip()
                    hints[key] = value
        return hints
    
    def _parse_monsters(self, text: str) -> List[Dict]:
        """解析潜在怪物列表"""
        monsters = []
        monsters_section = re.search(r'### 潜在怪物列表.*?\n(.*?)(?=\n###|$)', text, re.DOTALL)
        if not monsters_section:
            return monsters
        
        monsters_text = monsters_section.group(1)
        # 匹配每个怪物块
        monster_blocks = re.split(r'#### 怪物\d+：', monsters_text)
        
        for block in monster_blocks[1:]:  # 跳过第一个空块
            monster = self._parse_single_monster(block)
            if monster:
                monsters.append(monster)
        
        return monsters
    
    def _parse_single_monster(self, block: str) -> Dict:
        """解析单个怪物"""
        monster = {
            "name": "",
            "bind_type": "",
            "bind_target": "",
            "info": {},
            "appearance_conditions": {},
            "battle_description_template": "",
            "battle_effects": {},
            "director_hints": {}
        }
        
        # 提取怪物名称（第一行）
        lines = block.split('\n')
        if lines:
            monster["name"] = lines[0].strip()
        
        # 解析绑定类型和目标
        bind_match = re.search(r'- \*\*绑定类型\*\*[：:](.*?)(?=\n|$)', block)
        if bind_match:
            monster["bind_type"] = bind_match.group(1).strip()
        
        bind_target_match = re.search(r'- \*\*绑定目标\*\*[：:](.*?)(?=\n|$)', block)
        if bind_target_match:
            monster["bind_target"] = bind_target_match.group(1).strip()
        
        # 解析怪物信息
        info_section = re.search(r'- \*\*怪物信息.*?\n(.*?)(?=\n- \*\*|$)', block, re.DOTALL)
        if info_section:
            info_text = info_section.group(1)
            monster["info"] = self._parse_monster_info(info_text)
        
        # 解析出现条件
        conditions_section = re.search(r'- \*\*出现条件.*?\n(.*?)(?=\n- \*\*|$)', block, re.DOTALL)
        if conditions_section:
            conditions_text = conditions_section.group(1)
            monster["appearance_conditions"] = self._parse_conditions(conditions_text)
        
        # 解析战斗描述模板
        battle_desc_match = re.search(r'- \*\*战斗事件描述模板\*\*[：:](.*?)(?=\n- \*\*|$)', block, re.DOTALL)
        if battle_desc_match:
            monster["battle_description_template"] = battle_desc_match.group(1).strip()
        
        # 解析战斗影响
        battle_effects_section = re.search(r'- \*\*战斗影响.*?\n(.*?)(?=\n- \*\*|$)', block, re.DOTALL)
        if battle_effects_section:
            effects_text = battle_effects_section.group(1)
            monster["battle_effects"] = self._parse_battle_effects(effects_text)
        
        # 解析导演提示
        hints_section = re.search(r'- \*\*导演提示\*\*：.*?\n(.*?)(?=\n####|$)', block, re.DOTALL)
        if hints_section:
            hints_text = hints_section.group(1)
            monster["director_hints"] = self._parse_director_hints(hints_text)
        
        return monster
    
    def _parse_monster_info(self, text: str) -> Dict:
        """解析怪物信息"""
        info = {}
        for line in text.split('\n'):
            if '：' in line or ':' in line:
                parts = re.split('[：:]', line, 1)
                if len(parts) == 2:
                    key = parts[0].strip().replace('-', '').replace('*', '').strip()
                    value = parts[1].strip()
                    info[key] = value
        return info
    
    def _parse_battle_effects(self, text: str) -> Dict:
        """解析战斗影响"""
        effects = {
            "on_victory": {},
            "on_defeat": {}
        }
        
        # 解析胜利后
        victory_section = re.search(r'胜利后[：:](.*?)(?=失败后|$)', text, re.DOTALL)
        if victory_section:
            effects["on_victory"] = self._parse_effects(victory_section.group(1))
        
        # 解析失败后
        defeat_section = re.search(r'失败后[：:](.*?)(?=\n|$)', text, re.DOTALL)
        if defeat_section:
            effects["on_defeat"] = self._parse_effects(defeat_section.group(1))
        
        return effects
    
    def _parse_transition_possibilities(self, text: str) -> List[Dict]:
        """解析场景转换可能性"""
        transitions = []
        trans_section = re.search(r'### 场景转换可能性.*?\n(.*?)(?=\n###|$)', text, re.DOTALL)
        if not trans_section:
            return transitions
        
        trans_text = trans_section.group(1)
        # 解析可连接的目标
        for line in trans_text.split('\n'):
            if line.strip().startswith('-'):
                # 格式: - scene_002: {description}（可能由事件X触发）
                match = re.match(r'-\s*(\w+)[：:](.*?)(?:（(.+?)）)?$', line.strip())
                if match:
                    target_id, desc, trigger = match.groups()
                    transitions.append({
                        "target_id": target_id.strip(),
                        "description": desc.strip(),
                        "trigger": trigger.strip() if trigger else ""
                    })
        
        return transitions
    
    def get_scene_pool(self, theme: str) -> List[Dict]:
        """获取场景池（一级场景）"""
        overview = self.load_story_overview(theme)
        return overview.get("scenes", [])
    
    def get_rooms_for_scene(self, theme: str, scene_id: str) -> List[Dict]:
        """获取场景的所有房间"""
        overview = self.load_story_overview(theme)
        rooms = overview.get("rooms", [])
        return [room for room in rooms if room.get("parent_scene") == scene_id]
    
    def get_parent_scene(self, theme: str, room_id: str) -> Optional[str]:
        """获取房间所属的主场景"""
        overview = self.load_story_overview(theme)
        rooms = overview.get("rooms", [])
        for room in rooms:
            if room.get("id") == room_id:
                return room.get("parent_scene")
        return None
    
    def get_connected_scenes(self, theme: str, scene_id: str, room_id: Optional[str] = None) -> List[Dict]:
        """获取可连接的目标（场景或房间）"""
        overview = self.load_story_overview(theme)
        connected = []
        
        if room_id:
            # 如果当前在房间中，从房间网络获取连接
            room_network = overview.get("room_network", {})
            if room_id in room_network:
                connected = room_network[room_id]
        else:
            # 如果在一级场景中，从场景网络获取连接
            scene_network = overview.get("scene_network", {})
            if scene_id in scene_network:
                connected = scene_network[scene_id]
        
        return connected
    
    def check_scene_connection(self, theme: str, from_id: str, to_id: str, 
                              from_type: str = "scene", to_type: str = "scene") -> bool:
        """检查场景/房间是否连接"""
        connected = self.get_connected_scenes(theme, from_id if from_type == "scene" else None, 
                                             from_id if from_type == "room" else None)
        
        for conn in connected:
            if conn.get("target") == to_id and conn.get("type") == to_type:
                return True
        
        return False
    
    def check_connection_conditions(self, theme: str, from_id: str, to_id: str, 
                                    context: Dict, from_type: str = "scene", 
                                    to_type: str = "scene") -> Tuple[bool, str]:
        """检查连接前置条件"""
        connected = self.get_connected_scenes(theme, from_id if from_type == "scene" else None,
                                             from_id if from_type == "room" else None)
        
        for conn in connected:
            if conn.get("target") == to_id and conn.get("type") == to_type:
                prerequisite = conn.get("prerequisite")
                # 这里可以添加前置条件检查逻辑
                # 暂时返回True，表示条件满足
                if prerequisite:
                    # TODO: 实现前置条件检查逻辑
                    # 暂时返回True，后续可以添加具体的条件检查
                    return True, ""
                return True, ""
        
        return False, "目标不在可连接列表中"
    
    def get_starting_scene_id(self, theme: str) -> Optional[str]:
        """
        获取起始场景ID（从故事总览中查找标记为"起始场景"的场景）
        
        Args:
            theme: 主题
            
        Returns:
            起始场景ID，如果不存在返回None
        """
        overview = self.load_story_overview(theme)
        scenes = overview.get("scenes", [])
        
        # 查找标记为"起始场景"的场景
        for scene in scenes:
            desc = scene.get("description", "")
            if "起始场景" in desc or "起始" in desc:
                return scene.get("id")
        
        # 如果没有找到，返回第一个场景
        if scenes:
            return scenes[0].get("id")
        
        return None
    
    def get_potential_events(self, theme: str, scene_id: str, room_id: Optional[str] = None) -> List[Dict]:
        """
        获取潜在事件（从JSON文件加载，关联到当前场景/房间）
        
        Args:
            theme: 主题
            scene_id: 场景ID
            room_id: 房间ID（可选）
            
        Returns:
            事件列表（包含核心事件和随机事件）
        """
        events = []
        
        # 加载故事总览以获取事件列表
        overview = self.load_story_overview(theme)
        core_events = overview.get("core_events", [])
        random_events = overview.get("random_events", [])
        
        # 确定当前场景/房间ID
        current_location = room_id if room_id else scene_id
        
        # 筛选关联到当前场景/房间的核心事件
        for event in core_events:
            associated_scenes = event.get("associated_scenes", [])
            if current_location in associated_scenes or scene_id in associated_scenes:
                events.append(event)
        
        # 筛选关联到当前场景/房间的随机事件
        for event in random_events:
            associated_scenes = event.get("associated_scenes", [])
            if current_location in associated_scenes or scene_id in associated_scenes:
                events.append(event)
        
        return events
    
    def load_monster(self, theme: str, monster_id: str) -> Optional[Dict]:
        """
        加载怪物卡（支持通过文件名或怪物ID查找）
        
        Args:
            theme: 主题
            monster_id: 怪物ID或文件名（不含.json）
            
        Returns:
            怪物卡字典，如果不存在返回None
        """
        cache_key = f"{theme}:{monster_id}"
        if cache_key in self._monster_cache:
            return self._monster_cache[cache_key]
        
        monsters_dir = os.path.join(
            self.base_dir,
            self.config.CHARACTER_CONFIG_DIR,
            theme,
            "monsters"
        )
        
        if not os.path.exists(monsters_dir):
            return None
        
        # 方法1：直接通过文件名查找
        monster_path = os.path.join(monsters_dir, f"{monster_id}.json")
        if os.path.exists(monster_path):
            try:
                with open(monster_path, "r", encoding="utf-8") as f:
                    monster_data = json.load(f)
                    self._monster_cache[cache_key] = monster_data
                    return monster_data
            except Exception as e:
                print(f"加载怪物卡失败: {e}")
                return None
        
        # 方法2：遍历所有文件，通过id字段查找
        for filename in os.listdir(monsters_dir):
            if filename.endswith(".json"):
                try:
                    file_path = os.path.join(monsters_dir, filename)
                    with open(file_path, "r", encoding="utf-8") as f:
                        monster_data = json.load(f)
                        if monster_data.get("id") == monster_id:
                            self._monster_cache[cache_key] = monster_data
                            return monster_data
                except Exception:
                    continue
        
        return None
    
    def list_monsters(self, theme: str) -> List[Dict]:
        """
        列出主题下的所有怪物卡
        
        Args:
            theme: 主题
            
        Returns:
            怪物卡列表
        """
        monsters_dir = os.path.join(
            self.base_dir,
            self.config.CHARACTER_CONFIG_DIR,
            theme,
            "monsters"
        )
        
        if not os.path.exists(monsters_dir):
            return []
        
        monsters = []
        for filename in os.listdir(monsters_dir):
            if filename.endswith(".json"):
                # 先尝试用文件名作为ID
                file_id = filename.replace(".json", "")
                monster = self.load_monster(theme, file_id)
                if monster:
                    monsters.append(monster)
                else:
                    # 如果失败，尝试读取文件，使用文件中的id字段
                    try:
                        monster_path = os.path.join(monsters_dir, filename)
                        with open(monster_path, "r", encoding="utf-8") as f:
                            monster_data = json.load(f)
                            monster_id = monster_data.get("id")
                            if monster_id:
                                # 使用文件中的id加载
                                monster = self.load_monster(theme, monster_id)
                                if monster:
                                    monsters.append(monster)
                    except Exception:
                        pass
        
        return monsters
    
    def load_monster_bindings(self, theme: str) -> Dict:
        """
        加载怪物绑定关系（从JSON文件）
        
        Args:
            theme: 主题
            
        Returns:
            绑定关系字典，包含scene_bindings和room_bindings
        """
        bindings_path = os.path.join(
            self.base_dir,
            self.config.CHARACTER_CONFIG_DIR,
            theme,
            "monster_bindings.json"
        )
        
        if not os.path.exists(bindings_path):
            return {
                "scene_bindings": {},
                "room_bindings": {}
            }
        
        try:
            with open(bindings_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"加载怪物绑定关系失败: {e}")
            return {
                "scene_bindings": {},
                "room_bindings": {}
            }
    
    def get_potential_monsters(self, theme: str, scene_id: str, room_id: Optional[str] = None) -> List[Dict]:
        """
        获取潜在怪物（从怪物卡目录和绑定JSON文件加载）
        
        Args:
            theme: 主题
            scene_id: 场景ID
            room_id: 房间ID（可选）
            
        Returns:
            匹配的怪物列表
        """
        monsters = []
        monster_ids = set()
        
        # 从绑定JSON文件加载绑定关系
        bindings = self.load_monster_bindings(theme)
        
        # 获取场景绑定的怪物ID
        scene_bindings = bindings.get("scene_bindings", {})
        if scene_id in scene_bindings:
            for monster_id in scene_bindings[scene_id]:
                monster_ids.add(monster_id)
        
        # 获取房间绑定的怪物ID
        if room_id:
            room_bindings = bindings.get("room_bindings", {})
            if room_id in room_bindings:
                for monster_id in room_bindings[room_id]:
                    monster_ids.add(monster_id)
        
        # 兼容旧格式：从怪物卡的bindings字段加载
        all_monsters = self.list_monsters(theme)
        for monster in all_monsters:
            bindings_list = monster.get("bindings", [])
            for binding in bindings_list:
                bind_type = binding.get("bind_type", "")
                bind_target = binding.get("bind_target", "")
                
                # 检查场景绑定
                if bind_type == "scene" and bind_target == scene_id:
                    monster_ids.add(monster.get("id"))
                    break
                # 检查房间绑定
                elif bind_type == "room" and room_id and bind_target == room_id:
                    monster_ids.add(monster.get("id"))
                    break
        
        # 加载所有匹配的怪物卡（去重）
        loaded_ids = set()
        for monster_id in monster_ids:
            monster = self.load_monster(theme, monster_id)
            if monster:
                monster_actual_id = monster.get("id")
                # 通过实际ID去重
                if monster_actual_id and monster_actual_id not in loaded_ids:
                    monsters.append(monster)
                    loaded_ids.add(monster_actual_id)
                elif not monster_actual_id:
                    # 如果没有ID，通过名称去重
                    monster_name = monster.get("name", "")
                    if monster_name and not any(m.get("name") == monster_name for m in monsters):
                        monsters.append(monster)
        
        return monsters
    
    def get_scene_network(self, theme: str) -> Dict:
        """获取完整的场景连接网络"""
        overview = self.load_story_overview(theme)
        return {
            "scene_network": overview.get("scene_network", {}),
            "room_network": overview.get("room_network", {})
        }

