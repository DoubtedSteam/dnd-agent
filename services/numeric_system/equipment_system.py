"""
DND装备系统
管理武器和护甲，计算AC和武器属性
"""
import json
import os
from typing import Dict, Optional
from .attribute_system import AttributeSystem


class EquipmentSystem:
    """DND装备系统"""
    
    def __init__(self, theme: str = 'village_quest'):
        """
        初始化装备系统
        
        Args:
            theme: 主题名称，用于加载对应主题的装备数据
        """
        self.attr_system = AttributeSystem()
        self.theme = theme
        self._weapon_cache = {}
        self._armor_cache = {}
        self._load_equipment_data()
    
    def _load_equipment_data(self):
        """从JSON文件加载装备数据"""
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        equipment_dir = os.path.join(base_dir, 'themes', self.theme, 'equipment')
        
        # 加载武器数据
        weapons_file = os.path.join(equipment_dir, 'weapons.json')
        if os.path.exists(weapons_file):
            try:
                with open(weapons_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for weapon in data.get('weapons', []):
                        self._weapon_cache[weapon['name']] = weapon
                        self._weapon_cache[weapon['id']] = weapon
            except Exception as e:
                print(f"加载武器数据失败: {e}")
        
        # 加载护甲数据
        armor_file = os.path.join(equipment_dir, 'armor.json')
        if os.path.exists(armor_file):
            try:
                with open(armor_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for armor in data.get('armor', []):
                        self._armor_cache[armor['name']] = armor
                        self._armor_cache[armor['id']] = armor
            except Exception as e:
                print(f"加载护甲数据失败: {e}")
    
    def calculate_ac(self, character: Dict) -> int:
        """
        计算AC（护甲等级）
        
        DND规则：
        - 无甲：AC = 10 + DEX调整值
        - 轻甲：AC = 护甲基础AC + DEX调整值（无上限）
        - 中甲：AC = 护甲基础AC + DEX调整值（最高+2）
        - 重甲：AC = 护甲基础AC（不受DEX影响）
        - 盾牌：+2 AC
        
        Args:
            character: 角色数据字典
        
        Returns:
            AC值
        """
        dex_modifier = self.attr_system.get_ability_modifier(character, 'dex')
        
        # 获取装备信息
        equipment = character.get('attributes', {}).get('equipment', {})
        armor = equipment.get('armor')
        
        # 如果没有护甲，使用基础AC
        if not armor or armor == 'none':
            base_ac = 10 + dex_modifier
        else:
            # 这里需要从装备库加载护甲数据
            # 暂时使用默认值
            armor_data = self._get_armor_data(armor)
            if not armor_data:
                base_ac = 10 + dex_modifier
            else:
                armor_type = armor_data.get('type', 'light')
                armor_ac = armor_data.get('ac', 11)
                
                if armor_type == 'light':
                    # 轻甲：无DEX上限
                    base_ac = armor_ac + dex_modifier
                elif armor_type == 'medium':
                    # 中甲：DEX最高+2
                    base_ac = armor_ac + min(dex_modifier, 2)
                elif armor_type == 'heavy':
                    # 重甲：不受DEX影响
                    base_ac = armor_ac
                else:
                    base_ac = 10 + dex_modifier
        
        # 检查是否有盾牌
        weapon = character.get('attributes', {}).get('weapon', {})
        if weapon.get('off_hand') and 'shield' in str(weapon.get('off_hand', '')).lower():
            base_ac += 2
        
        return base_ac
    
    def _get_armor_data(self, armor_name: str) -> Optional[Dict]:
        """
        获取护甲数据
        
        Args:
            armor_name: 护甲名称或ID
        
        Returns:
            护甲数据字典
        """
        # 先从缓存查找
        if armor_name in self._armor_cache:
            return self._armor_cache[armor_name]
        
        # 如果没有找到，返回默认值（无甲）
        return None
    
    def get_weapon_data(self, weapon_name: str) -> Optional[Dict]:
        """
        获取武器数据
        
        Args:
            weapon_name: 武器名称或ID
        
        Returns:
            武器数据字典
        """
        # 先从缓存查找
        if weapon_name in self._weapon_cache:
            return self._weapon_cache[weapon_name]
        
        # 如果没有找到，返回None
        return None

