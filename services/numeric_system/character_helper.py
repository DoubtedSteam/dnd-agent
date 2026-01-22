"""
角色DND属性辅助函数
用于初始化和更新角色的DND属性
"""
from typing import Dict, Optional
from .attribute_system import AttributeSystem
from .proficiency_system import ProficiencySystem
from .equipment_system import EquipmentSystem


class CharacterHelper:
    """角色DND属性辅助类"""
    
    def __init__(self):
        """初始化辅助类"""
        self.attr_system = AttributeSystem()
        self.prof_system = ProficiencySystem()
        self.equip_system = EquipmentSystem()
    
    def initialize_dnd_attributes(self, character: Dict,
                                  str_score: int = 10,
                                  dex_score: int = 10,
                                  con_score: int = 10,
                                  int_score: int = 10,
                                  wis_score: int = 10,
                                  cha_score: int = 10,
                                  level: int = 1,
                                  class_name: str = 'fighter',
                                  background: str = 'soldier') -> Dict:
        """
        初始化角色的DND属性
        
        Args:
            character: 角色数据字典
            str_score: 力量值
            dex_score: 敏捷值
            con_score: 体质值
            int_score: 智力值
            wis_score: 感知值
            cha_score: 魅力值
            level: 等级
            class_name: 职业名称
            background: 背景名称
        
        Returns:
            更新后的角色数据字典
        """
        # 初始化属性值
        self.attr_system.initialize_ability_scores(
            character,
            str_score=str_score,
            dex_score=dex_score,
            con_score=con_score,
            int_score=int_score,
            wis_score=wis_score,
            cha_score=cha_score
        )
        
        # 设置等级和职业
        if 'attributes' not in character:
            character['attributes'] = {}
        
        character['attributes']['level'] = level
        character['attributes']['class'] = class_name
        character['attributes']['background'] = background
        
        # 计算熟练加值
        character['attributes']['proficiency_bonus'] = self.prof_system.get_proficiency_bonus(level)
        
        # 初始化熟练项（默认战士熟练项）
        if 'proficiencies' not in character['attributes']:
            character['attributes']['proficiencies'] = {
                'weapons': ['simple_melee', 'simple_ranged', 'martial_melee', 'martial_ranged'],
                'skills': ['athletics', 'perception'],
                'saving_throws': ['str', 'con']
            }
        
        # 计算AC
        character['attributes']['ac'] = self.equip_system.calculate_ac(character)
        
        # 计算HP（基于职业和体质）
        if 'vitals' not in character['attributes']:
            character['attributes']['vitals'] = {}
        
        # 计算最大HP（1级战士：10 + CON调整值）
        con_modifier = self.attr_system.get_ability_modifier(character, 'con')
        if class_name == 'fighter':
            hit_dice = 10
        elif class_name == 'rogue':
            hit_dice = 8
        elif class_name == 'wizard':
            hit_dice = 6
        else:
            hit_dice = 8  # 默认
        
        max_hp = hit_dice + con_modifier
        max_hp = max(1, max_hp)  # 至少1点HP
        
        # 如果已有HP，保持当前HP，否则设为最大HP
        if 'current_hp' not in character['attributes']['vitals']:
            character['attributes']['vitals']['current_hp'] = max_hp
        
        character['attributes']['vitals']['max_hp'] = max_hp
        character['attributes']['vitals']['hit_dice'] = f"1d{hit_dice}"
        character['attributes']['vitals']['hit_dice_remaining'] = 1
        
        # 计算先攻
        dex_modifier = self.attr_system.get_ability_modifier(character, 'dex')
        character['attributes']['initiative'] = dex_modifier
        
        return character
    
    def update_derived_attributes(self, character: Dict) -> Dict:
        """
        更新角色的衍生属性（AC、调整值等）
        
        Args:
            character: 角色数据字典
        
        Returns:
            更新后的角色数据字典
        """
        # 更新属性调整值
        character['attributes']['ability_modifiers'] = self.attr_system.get_all_modifiers(character)
        
        # 更新AC
        character['attributes']['ac'] = self.equip_system.calculate_ac(character)
        
        # 更新熟练加值
        level = character.get('attributes', {}).get('level', 1)
        character['attributes']['proficiency_bonus'] = self.prof_system.get_proficiency_bonus(level)
        
        # 更新先攻
        dex_modifier = self.attr_system.get_ability_modifier(character, 'dex')
        character['attributes']['initiative'] = dex_modifier
        
        return character

