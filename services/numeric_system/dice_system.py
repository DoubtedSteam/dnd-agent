"""
DND掷骰系统
支持d20、多面骰、优势/劣势掷骰
"""
import random
import re
from typing import Dict, Tuple, Optional


class DiceSystem:
    """DND掷骰系统"""
    
    def __init__(self, seed: Optional[int] = None):
        """
        初始化掷骰系统
        
        Args:
            seed: 随机数种子（用于测试）
        """
        if seed is not None:
            random.seed(seed)
    
    def roll_d20(self, modifier: int = 0, advantage: bool = False, 
                  disadvantage: bool = False) -> Dict:
        """
        掷d20骰子（DND核心掷骰）
        
        Args:
            modifier: 调整值（属性调整值 + 熟练加值等）
            advantage: 是否优势（掷两次取较高值）
            disadvantage: 是否劣势（掷两次取较低值）
        
        Returns:
            包含掷骰结果的字典：
            {
                'roll': 原始掷骰值（1-20），
                'rolls': [第一次掷骰, 第二次掷骰]（如果有优势/劣势），
                'modifier': 调整值,
                'total': 最终结果,
                'is_critical': 是否自然20（暴击）,
                'is_fumble': 是否自然1（大失败）
            }
        """
        if advantage and disadvantage:
            # 优势+劣势 = 普通掷骰
            advantage = False
            disadvantage = False
        
        if advantage:
            roll1 = random.randint(1, 20)
            roll2 = random.randint(1, 20)
            roll = max(roll1, roll2)
            rolls = [roll1, roll2]
        elif disadvantage:
            roll1 = random.randint(1, 20)
            roll2 = random.randint(1, 20)
            roll = min(roll1, roll2)
            rolls = [roll1, roll2]
        else:
            roll = random.randint(1, 20)
            rolls = [roll]
        
        total = roll + modifier
        
        result = {
            'roll': roll,
            'rolls': rolls,
            'modifier': modifier,
            'total': total,
            'is_critical': roll == 20,
            'is_fumble': roll == 1
        }
        
        return result
    
    def roll_dice(self, dice_notation: str) -> Dict:
        """
        解析并掷骰子（支持如 "1d20", "2d6+3", "1d8-1" 等格式）
        
        Args:
            dice_notation: 骰子表示法，如 "1d20", "2d6+3", "1d8-1"
        
        Returns:
            包含掷骰结果的字典：
            {
                'notation': 原始表示法,
                'rolls': [各次掷骰结果],
                'modifier': 调整值,
                'total': 最终结果
            }
        
        Examples:
            >>> dice = DiceSystem()
            >>> result = dice.roll_dice("2d6+3")
            >>> 'total' in result
            True
        """
        # 解析骰子表示法：如 "2d6+3" -> (2, 6, 3)
        pattern = r'(\d+)d(\d+)([+-]\d+)?'
        match = re.match(pattern, dice_notation.lower().replace(' ', ''))
        
        if not match:
            raise ValueError(f"无效的骰子表示法: {dice_notation}")
        
        num_dice = int(match.group(1))
        dice_size = int(match.group(2))
        modifier_str = match.group(3)
        modifier = int(modifier_str) if modifier_str else 0
        
        # 掷骰子
        rolls = [random.randint(1, dice_size) for _ in range(num_dice)]
        total = sum(rolls) + modifier
        
        return {
            'notation': dice_notation,
            'num_dice': num_dice,
            'dice_size': dice_size,
            'rolls': rolls,
            'modifier': modifier,
            'total': total
        }
    
    def roll_weapon_damage(self, damage_dice: str, ability_modifier: int = 0, 
                          is_critical: bool = False) -> Dict:
        """
        掷武器伤害骰
        
        Args:
            damage_dice: 伤害骰表示法，如 "1d8", "2d6"
            ability_modifier: 属性调整值（STR或DEX）
            is_critical: 是否暴击（暴击时伤害骰翻倍）
        
        Returns:
            包含伤害结果的字典：
            {
                'damage_dice': 伤害骰表示法,
                'rolls': [各次掷骰结果],
                'ability_modifier': 属性调整值,
                'is_critical': 是否暴击,
                'total': 最终伤害
            }
        """
        # 解析伤害骰
        pattern = r'(\d+)d(\d+)'
        match = re.match(pattern, damage_dice.lower().replace(' ', ''))
        
        if not match:
            raise ValueError(f"无效的伤害骰表示法: {damage_dice}")
        
        num_dice = int(match.group(1))
        dice_size = int(match.group(2))
        
        # 暴击时伤害骰翻倍
        if is_critical:
            num_dice *= 2
        
        # 掷伤害骰
        rolls = [random.randint(1, dice_size) for _ in range(num_dice)]
        damage_total = sum(rolls) + ability_modifier
        
        # 至少造成1点伤害
        damage_total = max(1, damage_total)
        
        return {
            'damage_dice': damage_dice,
            'rolls': rolls,
            'ability_modifier': ability_modifier,
            'is_critical': is_critical,
            'total': damage_total
        }

