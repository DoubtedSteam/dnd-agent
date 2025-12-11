"""
状态更新器：按照表里区分更新人物卡和环境文件
"""
import os
import json
from typing import Dict, List, Optional
from config import Config


class StateUpdater:
    """状态更新器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    def update_character_state(self, theme: str, save_step: str, 
                              character_id: str, state_changes: Dict, 
                              attribute_changes: Dict) -> bool:
        """
        更新角色状态（存档中的人物卡）
        
        Args:
            theme: 主题
            save_step: 存档步骤
            character_id: 角色ID
            state_changes: 状态变化
            attribute_changes: 属性变化
        
        Returns:
            是否更新成功
        """
        character_path = os.path.join(
            self.base_dir, 
            self.config.SAVE_DIR, 
            theme, 
            save_step, 
            f"{character_id}.json"
        )
        
        if not os.path.exists(character_path):
            return False
        
        try:
            # 读取当前人物卡
            with open(character_path, "r", encoding="utf-8") as f:
                character_data = json.load(f)
            
            # 更新状态
            if 'attributes' not in character_data:
                character_data['attributes'] = {}
            
            if 'state' not in character_data['attributes']:
                character_data['attributes']['state'] = {
                    'surface': {},
                    'hidden': {}
                }
            
            # 更新表信息
            if state_changes.get('surface'):
                character_data['attributes']['state']['surface'].update(
                    state_changes['surface']
                )
            
            # 更新里信息
            if state_changes.get('hidden'):
                character_data['attributes']['state']['hidden'].update(
                    state_changes['hidden']
                )
            
            # 更新其他属性
            if attribute_changes:
                for key, value in attribute_changes.items():
                    character_data['attributes'][key] = value
            
            # 保存更新
            with open(character_path, "w", encoding="utf-8") as f:
                json.dump(character_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"更新角色状态失败: {e}")
            return False
    
    def update_scene_state(self, theme: str, save_step: str, 
                          scene_changes: Dict, major_events: List[str]) -> bool:
        """
        更新场景状态
        
        Args:
            theme: 主题
            save_step: 存档步骤
            scene_changes: 场景变化（包含surface和hidden）
            major_events: 重大事件列表
        
        Returns:
            是否更新成功
        """
        scene_path = os.path.join(
            self.base_dir,
            self.config.SAVE_DIR,
            theme,
            save_step,
            "SCENE.md"
        )
        
        if not os.path.exists(scene_path):
            return False
        
        try:
            # 读取当前场景
            with open(scene_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 更新基础信息（时间、地点）
            surface_changes = scene_changes.get('surface', {})
            if surface_changes:
                # 更新时间
                if 'time' in surface_changes and surface_changes['time']:
                    # 查找并更新时间行
                    import re
                    time_pattern = r'- \*\*时间\*\*：.*'
                    new_time = f"- **时间**：{surface_changes['time']}"
                    content = re.sub(time_pattern, new_time, content)
                
                # 更新地点
                if 'location' in surface_changes and surface_changes['location']:
                    location = surface_changes['location']
                    # 构建新的地点信息
                    location_lines = ["- **地点**："]
                    if isinstance(location, dict):
                        if location.get('region'):
                            location_lines.append(f"  - **区域**：{location['region']}")
                        if location.get('specific_location'):
                            location_lines.append(f"  - **具体位置**：{location['specific_location']}")
                        if location.get('coordinates'):
                            location_lines.append(f"  - **坐标/方位**：{location['coordinates']}")
                        if location.get('environment'):
                            location_lines.append(f"  - **环境描述**：{location['environment']}")
                    else:
                        # 如果location是字符串，直接使用
                        location_lines[0] = f"- **地点**：{location}"
                    
                    new_location = "\n".join(location_lines)
                    
                    # 查找并替换地点部分（可能跨多行）
                    # 匹配从"- **地点**："开始到下一个"- **"或"##"或文件结尾
                    location_pattern = r'- \*\*地点\*\*：.*?(?=\n- \*\*[^：]|##|$)'
                    # 使用更精确的匹配
                    lines = content.split('\n')
                    new_lines = []
                    i = 0
                    while i < len(lines):
                        if lines[i].strip().startswith('- **地点**：'):
                            # 找到地点行，添加新地点信息
                            new_lines.append(new_location)
                            # 跳过旧的地点行及其子行（缩进的）
                            i += 1
                            while i < len(lines) and (lines[i].strip() == '' or lines[i].startswith('  - **')):
                                i += 1
                            continue
                        new_lines.append(lines[i])
                        i += 1
                    content = '\n'.join(new_lines)
                
                # 更新当前叙述
                if 'current_narrative' in surface_changes and surface_changes['current_narrative']:
                    # 在"表（玩家可见）"部分添加或更新当前叙述
                    if "## 表（玩家可见）" in content:
                        table_start = content.find("## 表（玩家可见）")
                        table_end = content.find("##", table_start + 1)
                        if table_end == -1:
                            table_end = len(content)
                        
                        table_section = content[table_start:table_end]
                        # 检查是否已有"当前叙述"
                        if "- **当前叙述**：" in table_section:
                            # 更新现有叙述
                            narrative_pattern = r'- \*\*当前叙述\*\*：.*'
                            new_narrative = f"- **当前叙述**：{surface_changes['current_narrative']}"
                            table_section = re.sub(narrative_pattern, new_narrative, table_section)
                        else:
                            # 添加新叙述（在第一个项目前）
                            first_item = table_section.find("- **")
                            if first_item != -1:
                                new_narrative = f"- **当前叙述**：{surface_changes['current_narrative']}\n"
                                table_section = table_section[:first_item] + new_narrative + table_section[first_item:]
                        
                        content = content[:table_start] + table_section + content[table_end:]
                
                # 更新目标
                if 'goal' in surface_changes and surface_changes['goal']:
                    goal_pattern = r'- \*\*目标\*\*：.*'
                    new_goal = f"- **目标**：{surface_changes['goal']}"
                    content = re.sub(goal_pattern, new_goal, content)
                
                # 更新资源
                if 'resources' in surface_changes and surface_changes['resources']:
                    resources_pattern = r'- \*\*资源\*\*：.*'
                    new_resources = f"- **资源**：{surface_changes['resources']}"
                    content = re.sub(resources_pattern, new_resources, content)
            
            # 更新里信息
            hidden_changes = scene_changes.get('hidden', {})
            if hidden_changes:
                # 更新最终目标
                if 'final_goal' in hidden_changes and hidden_changes['final_goal']:
                    final_goal_pattern = r'- \*\*最终目标\*\*：.*'
                    new_final_goal = f"- **最终目标**：{hidden_changes['final_goal']}"
                    content = re.sub(final_goal_pattern, new_final_goal, content)
                
                # 更新潜在敌人（隐藏情报）
                if 'potential_enemies' in hidden_changes and hidden_changes['potential_enemies']:
                    enemies_pattern = r'- \*\*潜在敌人（隐藏情报）\*\*：.*'
                    new_enemies = f"- **潜在敌人（隐藏情报）**：{hidden_changes['potential_enemies']}"
                    content = re.sub(enemies_pattern, new_enemies, content)
                
                # 更新风险提示
                if 'risk_hints' in hidden_changes and hidden_changes['risk_hints']:
                    risk_pattern = r'- \*\*风险提示\*\*：.*'
                    new_risk = f"- **风险提示**：{hidden_changes['risk_hints']}"
                    content = re.sub(risk_pattern, new_risk, content)
            
            # 更新重大事件
            if major_events:
                # 查找重大事件部分
                if "## 重大事件" in content:
                    # 提取现有事件
                    events_start = content.find("## 重大事件")
                    events_end = content.find("##", events_start + 1)
                    if events_end == -1:
                        events_end = len(content)
                    
                    # 读取现有事件（保留旧的）
                    existing_section = content[events_start:events_end]
                    existing_events = []
                    for line in existing_section.split('\n'):
                        if line.strip().startswith('- '):
                            existing_events.append(line.strip())
                    
                    # 合并新旧事件
                    all_events = existing_events + [f"- {event}" for event in major_events]
                    # 去重（保留顺序）
                    seen = set()
                    unique_events = []
                    for event in all_events:
                        if event not in seen:
                            seen.add(event)
                            unique_events.append(event)
                    
                    new_events = "\n".join(unique_events)
                    
                    # 替换重大事件部分
                    content = content[:events_start] + f"## 重大事件\n{new_events}\n\n" + content[events_end:]
                else:
                    # 如果没有重大事件部分，添加一个
                    new_events = "\n".join([f"- {event}" for event in major_events])
                    if "## 里（LLM推演用，隐藏）" in content:
                        content = content.replace(
                            "## 里（LLM推演用，隐藏）",
                            f"## 重大事件\n{new_events}\n\n## 里（LLM推演用，隐藏）"
                        )
            
            # 保存更新
            with open(scene_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            return True
        except Exception as e:
            print(f"更新场景状态失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def update_character_appearance_and_equipment(self, theme: str, save_step: str,
                                                  character_id: str, updates: Dict) -> bool:
        """
        更新角色的外貌和装备描述
        
        Args:
            theme: 主题
            save_step: 存档步骤
            character_id: 角色ID
            updates: 更新内容，包含appearance和equipment，每个都有objective/subjective/inner三个部分
        
        Returns:
            是否更新成功
        """
        character_path = os.path.join(
            self.base_dir,
            self.config.SAVE_DIR,
            theme,
            save_step,
            f"{character_id}.json"
        )
        
        if not os.path.exists(character_path):
            return False
        
        try:
            # 读取当前人物卡
            with open(character_path, "r", encoding="utf-8") as f:
                character_data = json.load(f)
            
            # 确保attributes和state存在
            if 'attributes' not in character_data:
                character_data['attributes'] = {}
            
            if 'state' not in character_data['attributes']:
                character_data['attributes']['state'] = {
                    'surface': {},
                    'hidden': {}
                }
            
            # 更新外貌描述
            if 'appearance' in updates:
                appearance = updates['appearance']
                
                # 客观描述 -> hidden.observer_state（客观观察状态）
                if 'objective' in appearance and appearance['objective']:
                    if 'observer_state' not in character_data['attributes']['state']['hidden']:
                        character_data['attributes']['state']['hidden']['observer_state'] = ""
                    current = character_data['attributes']['state']['hidden']['observer_state']
                    if appearance['objective'] not in current:
                        character_data['attributes']['state']['hidden']['observer_state'] = \
                            f"{current}\n外貌（客观）: {appearance['objective']}".strip()
                
                # 队友主观 -> surface.perceived_state（队友主观看到的）
                if 'subjective' in appearance and appearance['subjective']:
                    if 'perceived_state' not in character_data['attributes']['state']['surface']:
                        character_data['attributes']['state']['surface']['perceived_state'] = ""
                    current = character_data['attributes']['state']['surface']['perceived_state']
                    if appearance['subjective'] not in current:
                        character_data['attributes']['state']['surface']['perceived_state'] = \
                            f"{current}\n外貌（主观）: {appearance['subjective']}".strip()
                
                # 内心想法 -> hidden.inner_monologue（内心独白）
                if 'inner' in appearance and appearance['inner']:
                    if 'inner_monologue' not in character_data['attributes']['state']['hidden']:
                        character_data['attributes']['state']['hidden']['inner_monologue'] = ""
                    current = character_data['attributes']['state']['hidden']['inner_monologue']
                    if appearance['inner'] not in current:
                        character_data['attributes']['state']['hidden']['inner_monologue'] = \
                            f"{current}\n外貌（内心）: {appearance['inner']}".strip()
            
            # 更新装备描述
            if 'equipment' in updates:
                equipment = updates['equipment']
                
                # 客观描述 -> hidden.observer_state
                if 'objective' in equipment and equipment['objective']:
                    if 'observer_state' not in character_data['attributes']['state']['hidden']:
                        character_data['attributes']['state']['hidden']['observer_state'] = ""
                    current = character_data['attributes']['state']['hidden']['observer_state']
                    if equipment['objective'] not in current:
                        character_data['attributes']['state']['hidden']['observer_state'] = \
                            f"{current}\n装备（客观）: {equipment['objective']}".strip()
                
                # 队友主观 -> surface.perceived_state
                if 'subjective' in equipment and equipment['subjective']:
                    if 'perceived_state' not in character_data['attributes']['state']['surface']:
                        character_data['attributes']['state']['surface']['perceived_state'] = ""
                    current = character_data['attributes']['state']['surface']['perceived_state']
                    if equipment['subjective'] not in current:
                        character_data['attributes']['state']['surface']['perceived_state'] = \
                            f"{current}\n装备（主观）: {equipment['subjective']}".strip()
                
                # 内心想法 -> hidden.inner_monologue
                if 'inner' in equipment and equipment['inner']:
                    if 'inner_monologue' not in character_data['attributes']['state']['hidden']:
                        character_data['attributes']['state']['hidden']['inner_monologue'] = ""
                    current = character_data['attributes']['state']['hidden']['inner_monologue']
                    if equipment['inner'] not in current:
                        character_data['attributes']['state']['hidden']['inner_monologue'] = \
                            f"{current}\n装备（内心）: {equipment['inner']}".strip()
            
            # 保存更新
            with open(character_path, "w", encoding="utf-8") as f:
                json.dump(character_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"更新角色外貌和装备描述失败: {e}")
            return False

