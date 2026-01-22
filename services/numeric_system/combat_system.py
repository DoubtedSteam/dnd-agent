"""
DND战斗系统
实现攻击检定和伤害计算
"""
from typing import Dict, Optional
from .attribute_system import AttributeSystem
from .dice_system import DiceSystem
from .proficiency_system import ProficiencySystem
from .equipment_system import EquipmentSystem


class CombatSystem:
    """DND战斗系统"""
    
    def __init__(self, theme: str = 'village_quest'):
        """
        初始化战斗系统
        
        Args:
            theme: 主题名称，用于加载装备数据
        """
        self.attr_system = AttributeSystem()
        self.dice_system = DiceSystem()
        self.prof_system = ProficiencySystem()
        self.equip_system = EquipmentSystem(theme=theme)
    
    def make_attack_roll(self, attacker: Dict, weapon: Dict, 
                        target_ac: int, advantage: bool = False,
                        disadvantage: bool = False) -> Dict:
        """
        进行攻击检定
        
        DND规则：
        攻击检定 = d20 + 属性调整值（STR或DEX）+ 熟练加值（如果熟练）
        命中条件：攻击检定 >= 目标AC
        自然20：自动命中并暴击
        自然1：自动未命中
        
        Args:
            attacker: 攻击者角色数据字典
            weapon: 武器数据字典
            target_ac: 目标AC
            advantage: 是否优势
            disadvantage: 是否劣势
        
        Returns:
            攻击检定结果字典：
            {
                'attack_roll': d20掷骰结果,
                'attack_modifier': 攻击调整值,
                'total': 最终攻击检定值,
                'target_ac': 目标AC,
                'hit': 是否命中,
                'is_critical': 是否暴击,
                'is_fumble': 是否大失败
            }
        """
        # 计算攻击调整值
        weapon_type = weapon.get('type', '')
        is_finesse = 'finesse' in weapon.get('properties', [])
        use_dex = weapon_type in ['simple_ranged', 'martial_ranged'] or is_finesse
        
        attack_modifier = self.prof_system.get_attack_modifier(attacker, weapon, use_dex)
        
        # 掷d20
        roll_result = self.dice_system.roll_d20(
            modifier=attack_modifier,
            advantage=advantage,
            disadvantage=disadvantage
        )
        
        # 判定命中
        hit = roll_result['total'] >= target_ac
        
        # 自然20自动命中并暴击
        if roll_result['is_critical']:
            hit = True
            roll_result['is_critical'] = True
        
        # 自然1自动未命中
        if roll_result['is_fumble']:
            hit = False
        
        result = {
            'attack_roll': roll_result,
            'attack_modifier': attack_modifier,
            'total': roll_result['total'],
            'target_ac': target_ac,
            'hit': hit,
            'is_critical': roll_result['is_critical'],
            'is_fumble': roll_result['is_fumble']
        }
        
        return result
    
    def calculate_damage(self, attacker: Dict, weapon: Dict, 
                        is_critical: bool = False) -> Dict:
        """
        计算伤害
        
        DND规则：
        基础伤害 = 武器伤害骰（如1d8）
        属性加值 = STR调整值（近战）或DEX调整值（远程/灵巧）
        最终伤害 = 基础伤害 + 属性加值
        暴击伤害 = 所有伤害骰翻倍 + 属性加值
        
        Args:
            attacker: 攻击者角色数据字典
            weapon: 武器数据字典
            is_critical: 是否暴击
        
        Returns:
            伤害结果字典：
            {
                'damage_dice': 伤害骰表示法,
                'damage_rolls': 伤害骰掷骰结果,
                'ability_modifier': 属性调整值,
                'is_critical': 是否暴击,
                'total': 最终伤害
            }
        """
        # 获取伤害骰
        damage_dice = weapon.get('damage_dice', '1d4')
        
        # 判断使用哪个属性
        weapon_type = weapon.get('type', '')
        is_finesse = 'finesse' in weapon.get('properties', [])
        
        if weapon_type in ['simple_ranged', 'martial_ranged'] or is_finesse:
            ability_modifier = self.attr_system.get_ability_modifier(attacker, 'dex')
        else:
            ability_modifier = self.attr_system.get_ability_modifier(attacker, 'str')
        
        # 掷伤害骰
        damage_result = self.dice_system.roll_weapon_damage(
            damage_dice=damage_dice,
            ability_modifier=ability_modifier,
            is_critical=is_critical
        )
        
        return damage_result
    
    def execute_attack(self, attacker: Dict, defender: Dict, 
                      weapon_name: Optional[str] = None,
                      advantage: bool = False,
                      disadvantage: bool = False) -> Dict:
        """
        执行完整的攻击流程（攻击检定 + 伤害计算）
        
        Args:
            attacker: 攻击者角色数据字典
            defender: 防御者角色数据字典
            weapon_name: 武器名称（如果为None，使用角色的主手武器）
            advantage: 是否优势
            disadvantage: 是否劣势
        
        Returns:
            完整攻击结果字典：
            {
                'attack_roll': 攻击检定结果,
                'hit': 是否命中,
                'damage': 伤害结果（如果命中）,
                'defender_hp_before': 防御者HP（攻击前）,
                'defender_hp_after': 防御者HP（攻击后）
            }
        """
        # 获取武器
        if weapon_name is None:
            weapon_name = attacker.get('attributes', {}).get('weapon', {}).get('main_hand', '长剑')
        
        weapon = self.equip_system.get_weapon_data(weapon_name)
        if not weapon:
            raise ValueError(f"未找到武器: {weapon_name}")
        
        # 获取防御者AC
        defender_ac = self.equip_system.calculate_ac(defender)
        
        # 攻击检定
        attack_result = self.make_attack_roll(
            attacker=attacker,
            weapon=weapon,
            target_ac=defender_ac,
            advantage=advantage,
            disadvantage=disadvantage
        )
        
        # 获取防御者当前HP
        defender_vitals = defender.get('attributes', {}).get('vitals', {})
        defender_hp_before = defender_vitals.get('current_hp', defender_vitals.get('hp', 0))
        
        result = {
            'attack_roll': attack_result,
            'hit': attack_result['hit'],
            'defender_hp_before': defender_hp_before,
            'defender_hp_after': defender_hp_before
        }
        
        # 如果命中，计算伤害
        if attack_result['hit']:
            damage_result = self.calculate_damage(
                attacker=attacker,
                weapon=weapon,
                is_critical=attack_result['is_critical']
            )
            result['damage'] = damage_result
            
            # 应用伤害
            damage_total = damage_result['total']
            defender_hp_after = max(0, defender_hp_before - damage_total)
            result['defender_hp_after'] = defender_hp_after
            
            # 更新防御者HP
            if 'vitals' not in defender.get('attributes', {}):
                defender['attributes']['vitals'] = {}
            defender['attributes']['vitals']['current_hp'] = defender_hp_after
        
        return result

