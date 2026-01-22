"""
DND属性系统
管理6大基础属性和属性调整值
"""
from typing import Dict, Optional
import math


class AttributeSystem:
    """DND属性系统"""
    
    # DND 6大基础属性
    ABILITY_NAMES = {
        'str': '力量',
        'dex': '敏捷',
        'con': '体质',
        'int': '智力',
        'wis': '感知',
        'cha': '魅力'
    }
    
    # 属性英文全称
    ABILITY_FULL_NAMES = {
        'str': 'Strength',
        'dex': 'Dexterity',
        'con': 'Constitution',
        'int': 'Intelligence',
        'wis': 'Wisdom',
        'cha': 'Charisma'
    }
    
    def __init__(self):
        """初始化属性系统"""
        pass
    
    @staticmethod
    def calculate_modifier(ability_score: int) -> int:
        """
        计算属性调整值（Modifier）
        
        DND规则：调整值 = floor((属性值 - 10) / 2)
        
        Args:
            ability_score: 属性值（1-30）
        
        Returns:
            属性调整值（-5到+10）
        
        Examples:
            >>> AttributeSystem.calculate_modifier(10)
            0
            >>> AttributeSystem.calculate_modifier(15)
            2
            >>> AttributeSystem.calculate_modifier(8)
            -1
            >>> AttributeSystem.calculate_modifier(20)
            5
        """
        if not isinstance(ability_score, int):
            raise ValueError(f"属性值必须是整数，得到: {type(ability_score)}")
        
        # DND规则：向下取整
        return (ability_score - 10) // 2
    
    @staticmethod
    def validate_ability_score(score: int, max_score: int = 30) -> bool:
        """
        验证属性值是否在有效范围内
        
        Args:
            score: 属性值
            max_score: 最大属性值（默认30，传奇角色）
        
        Returns:
            是否有效
        """
        return 1 <= score <= max_score
    
    def get_all_modifiers(self, character: Dict) -> Dict[str, int]:
        """
        获取角色的所有属性调整值
        
        Args:
            character: 角色数据字典，应包含 ability_scores 字段
        
        Returns:
            包含所有属性调整值的字典
        """
        ability_scores = character.get('attributes', {}).get('ability_scores', {})
        
        modifiers = {}
        for ability in self.ABILITY_NAMES.keys():
            score = ability_scores.get(ability, 10)  # 默认10
            if not self.validate_ability_score(score):
                score = 10  # 无效值默认设为10
            modifiers[ability] = self.calculate_modifier(score)
        
        return modifiers
    
    def get_ability_score(self, character: Dict, ability: str) -> int:
        """
        获取角色的属性值
        
        Args:
            character: 角色数据字典
            ability: 属性名称（str, dex, con, int, wis, cha）
        
        Returns:
            属性值（默认10）
        """
        if ability not in self.ABILITY_NAMES:
            raise ValueError(f"无效的属性名称: {ability}")
        
        ability_scores = character.get('attributes', {}).get('ability_scores', {})
        return ability_scores.get(ability, 10)
    
    def get_ability_modifier(self, character: Dict, ability: str) -> int:
        """
        获取角色的属性调整值
        
        Args:
            character: 角色数据字典
            ability: 属性名称
        
        Returns:
            属性调整值
        """
        score = self.get_ability_score(character, ability)
        return self.calculate_modifier(score)
    
    def initialize_ability_scores(self, character: Dict, 
                                   str_score: int = 10,
                                   dex_score: int = 10,
                                   con_score: int = 10,
                                   int_score: int = 10,
                                   wis_score: int = 10,
                                   cha_score: int = 10) -> Dict:
        """
        初始化角色的属性值
        
        Args:
            character: 角色数据字典
            str_score: 力量值
            dex_score: 敏捷值
            con_score: 体质值
            int_score: 智力值
            wis_score: 感知值
            cha_score: 魅力值
        
        Returns:
            更新后的角色数据字典
        """
        # 验证所有属性值
        scores = {
            'str': str_score,
            'dex': dex_score,
            'con': con_score,
            'int': int_score,
            'wis': wis_score,
            'cha': cha_score
        }
        
        for ability, score in scores.items():
            if not self.validate_ability_score(score):
                raise ValueError(f"{ability}属性值无效: {score}，应在1-30之间")
        
        # 初始化attributes结构
        if 'attributes' not in character:
            character['attributes'] = {}
        
        character['attributes']['ability_scores'] = scores
        
        # 计算并存储调整值
        character['attributes']['ability_modifiers'] = self.get_all_modifiers(character)
        
        return character

