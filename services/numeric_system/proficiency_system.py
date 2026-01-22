"""
DND熟练系统
管理熟练加值和熟练项
"""
from typing import Dict, List, Optional


class ProficiencySystem:
    """DND熟练系统"""
    
    # 熟练加值表（根据等级）
    PROFICIENCY_BONUS_TABLE = {
        1: 2, 2: 2, 3: 2, 4: 2,
        5: 3, 6: 3, 7: 3, 8: 3,
        9: 4, 10: 4, 11: 4, 12: 4,
        13: 5, 14: 5, 15: 5, 16: 5,
        17: 6, 18: 6, 19: 6, 20: 6
    }
    
    def __init__(self):
        """初始化熟练系统"""
        pass
    
    @staticmethod
    def get_proficiency_bonus(level: int) -> int:
        """
        根据等级获取熟练加值
        
        Args:
            level: 角色等级（1-20）
        
        Returns:
            熟练加值（+2到+6）
        
        Examples:
            >>> ProficiencySystem.get_proficiency_bonus(1)
            2
            >>> ProficiencySystem.get_proficiency_bonus(5)
            3
            >>> ProficiencySystem.get_proficiency_bonus(17)
            6
        """
        if level < 1:
            return 2  # 默认值
        if level > 20:
            return 6  # 20级以上保持+6
        
        return ProficiencySystem.PROFICIENCY_BONUS_TABLE.get(level, 2)
    
    def is_proficient_in_weapon(self, character: Dict, weapon_type: str) -> bool:
        """
        检查角色是否熟练使用某种武器
        
        Args:
            character: 角色数据字典
            weapon_type: 武器类型（如 "simple_melee", "martial_melee", "simple_ranged", "martial_ranged"）
        
        Returns:
            是否熟练
        """
        proficiencies = character.get('attributes', {}).get('proficiencies', {})
        weapon_proficiencies = proficiencies.get('weapons', [])
        return weapon_type in weapon_proficiencies
    
    def is_proficient_in_skill(self, character: Dict, skill: str) -> bool:
        """
        检查角色是否熟练某项技能
        
        Args:
            character: 角色数据字典
            skill: 技能名称（如 "athletics", "perception"）
        
        Returns:
            是否熟练
        """
        proficiencies = character.get('attributes', {}).get('proficiencies', {})
        skill_proficiencies = proficiencies.get('skills', [])
        return skill in skill_proficiencies
    
    def is_proficient_in_saving_throw(self, character: Dict, ability: str) -> bool:
        """
        检查角色是否熟练某项豁免检定
        
        Args:
            character: 角色数据字典
            ability: 属性名称（str, dex, con, int, wis, cha）
        
        Returns:
            是否熟练
        """
        proficiencies = character.get('attributes', {}).get('proficiencies', {})
        saving_throw_proficiencies = proficiencies.get('saving_throws', [])
        return ability in saving_throw_proficiencies
    
    def get_attack_modifier(self, character: Dict, weapon: Dict, 
                           use_dex: bool = False) -> int:
        """
        计算攻击调整值（用于攻击检定）
        
        Args:
            character: 角色数据字典
            weapon: 武器数据字典
            use_dex: 是否使用敏捷（用于远程武器或灵巧武器）
        
        Returns:
            攻击调整值 = 属性调整值 + 熟练加值（如果熟练）
        """
        from .attribute_system import AttributeSystem
        
        attr_system = AttributeSystem()
        level = character.get('attributes', {}).get('level', 1)
        proficiency_bonus = self.get_proficiency_bonus(level)
        
        # 判断使用哪个属性
        weapon_type = weapon.get('type', '')
        is_finesse = 'finesse' in weapon.get('properties', [])
        
        if use_dex or weapon_type in ['simple_ranged', 'martial_ranged'] or is_finesse:
            ability_modifier = attr_system.get_ability_modifier(character, 'dex')
        else:
            ability_modifier = attr_system.get_ability_modifier(character, 'str')
        
        # 检查是否熟练
        weapon_category = self._get_weapon_category(weapon_type)
        is_proficient = self.is_proficient_in_weapon(character, weapon_category)
        
        if is_proficient:
            return ability_modifier + proficiency_bonus
        else:
            return ability_modifier
    
    def _get_weapon_category(self, weapon_type: str) -> str:
        """
        根据武器类型获取武器类别
        
        Args:
            weapon_type: 武器类型
        
        Returns:
            武器类别
        """
        if 'simple' in weapon_type and 'melee' in weapon_type:
            return 'simple_melee'
        elif 'martial' in weapon_type and 'melee' in weapon_type:
            return 'martial_melee'
        elif 'simple' in weapon_type and 'ranged' in weapon_type:
            return 'simple_ranged'
        elif 'martial' in weapon_type and 'ranged' in weapon_type:
            return 'martial_ranged'
        else:
            return 'simple_melee'  # 默认

