"""
DND战斗系统测试
测试属性系统、攻击检定和伤害计算
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.numeric_system import AttributeSystem, DiceSystem, ProficiencySystem, EquipmentSystem, CombatSystem
from services.numeric_system.character_helper import CharacterHelper


def test_attribute_system():
    """测试属性系统"""
    print("=" * 60)
    print("测试属性系统")
    print("=" * 60)
    
    attr_system = AttributeSystem()
    
    # 测试属性调整值计算
    assert attr_system.calculate_modifier(10) == 0, "属性值10应该对应调整值0"
    assert attr_system.calculate_modifier(15) == 2, "属性值15应该对应调整值+2"
    assert attr_system.calculate_modifier(8) == -1, "属性值8应该对应调整值-1"
    assert attr_system.calculate_modifier(20) == 5, "属性值20应该对应调整值+5"
    
    print("✅ 属性调整值计算测试通过")
    
    # 测试角色属性
    character = {
        'attributes': {
            'ability_scores': {
                'str': 16,
                'dex': 14,
                'con': 15,
                'int': 10,
                'wis': 12,
                'cha': 8
            }
        }
    }
    
    modifiers = attr_system.get_all_modifiers(character)
    assert modifiers['str'] == 3, "力量16应该对应调整值+3"
    assert modifiers['dex'] == 2, "敏捷14应该对应调整值+2"
    assert modifiers['con'] == 2, "体质15应该对应调整值+2"
    
    print("✅ 角色属性获取测试通过")
    print()


def test_dice_system():
    """测试掷骰系统"""
    print("=" * 60)
    print("测试掷骰系统")
    print("=" * 60)
    
    dice_system = DiceSystem(seed=42)  # 固定种子用于测试
    
    # 测试d20掷骰
    result = dice_system.roll_d20(modifier=5)
    assert 1 <= result['roll'] <= 20, "d20掷骰应该在1-20之间"
    assert result['total'] == result['roll'] + 5, "总结果应该等于掷骰值+调整值"
    
    print(f"✅ d20掷骰测试通过: 掷骰值={result['roll']}, 调整值=+5, 总结果={result['total']}")
    
    # 测试伤害骰
    damage_result = dice_system.roll_weapon_damage("1d8", ability_modifier=3, is_critical=False)
    assert damage_result['total'] >= 4, "伤害应该至少是1+3=4"
    assert damage_result['total'] <= 11, "伤害应该最多是8+3=11"
    
    print(f"✅ 伤害骰测试通过: 伤害={damage_result['total']}")
    
    # 测试暴击伤害
    crit_damage = dice_system.roll_weapon_damage("1d8", ability_modifier=3, is_critical=True)
    assert crit_damage['total'] >= 5, "暴击伤害应该至少是2+3=5"
    assert len(crit_damage['rolls']) == 2, "暴击应该掷两次骰子"
    
    print(f"✅ 暴击伤害测试通过: 暴击伤害={crit_damage['total']}")
    print()


def test_proficiency_system():
    """测试熟练系统"""
    print("=" * 60)
    print("测试熟练系统")
    print("=" * 60)
    
    prof_system = ProficiencySystem()
    
    # 测试熟练加值
    assert prof_system.get_proficiency_bonus(1) == 2, "1级应该+2"
    assert prof_system.get_proficiency_bonus(5) == 3, "5级应该+3"
    assert prof_system.get_proficiency_bonus(9) == 4, "9级应该+4"
    assert prof_system.get_proficiency_bonus(17) == 6, "17级应该+6"
    
    print("✅ 熟练加值测试通过")
    print()


def test_combat_system():
    """测试战斗系统"""
    print("=" * 60)
    print("测试战斗系统 - 战士 vs 魔物")
    print("=" * 60)
    
    # 创建战士角色
    helper = CharacterHelper()
    fighter = {
        'id': 'char_fighter_001',
        'name': '战士',
        'attributes': {
            'weapon': {'main_hand': '长剑', 'off_hand': '盾牌'},
            'equipment': {'armor': '皮甲'}
        }
    }
    
    helper.initialize_dnd_attributes(
        fighter,
        str_score=16,  # 力量+3
        dex_score=14,  # 敏捷+2
        con_score=15,  # 体质+2
        level=1,
        class_name='fighter'
    )
    
    print(f"战士属性: STR={fighter['attributes']['ability_scores']['str']} "
          f"(调整值+{fighter['attributes']['ability_modifiers']['str']})")
    print(f"战士AC: {fighter['attributes']['ac']}")
    print(f"战士HP: {fighter['attributes']['vitals']['current_hp']}/{fighter['attributes']['vitals']['max_hp']}")
    
    # 创建魔物
    monster = {
        'id': 'monster_field_001',
        'name': '田野魔物',
        'attributes': {
            'ability_scores': {
                'str': 18,  # 力量+4
                'dex': 14,  # 敏捷+2
                'con': 16,  # 体质+3
                'int': 6,   # 智力-2
                'wis': 12,  # 感知+1
                'cha': 6    # 魅力-2
            },
            'level': 3,
            'weapon': {'main_hand': '爪击'},
            'equipment': {'armor': 'none'}
        }
    }
    
    # 初始化魔物属性
    attr_system = AttributeSystem()
    monster['attributes']['ability_modifiers'] = attr_system.get_all_modifiers(monster)
    monster['attributes']['proficiency_bonus'] = ProficiencySystem().get_proficiency_bonus(3)
    monster['attributes']['ac'] = 13  # 10 + DEX调整值(2) + 1（天然护甲）
    monster['attributes']['vitals'] = {
        'max_hp': 30,
        'current_hp': 30
    }
    
    print(f"\n魔物属性: STR={monster['attributes']['ability_scores']['str']} "
          f"(调整值+{monster['attributes']['ability_modifiers']['str']})")
    print(f"魔物AC: {monster['attributes']['ac']}")
    print(f"魔物HP: {monster['attributes']['vitals']['current_hp']}/{monster['attributes']['vitals']['max_hp']}")
    
    # 测试战斗
    combat_system = CombatSystem()
    
    print("\n" + "=" * 60)
    print("战斗开始！")
    print("=" * 60)
    
    # 战士攻击魔物
    print("\n【战士攻击魔物】")
    attack_result = combat_system.execute_attack(
        attacker=fighter,
        defender=monster,
        weapon_name='长剑'
    )
    
    print(f"攻击检定: {attack_result['attack_roll']['attack_roll']['roll']} "
          f"+ {attack_result['attack_roll']['attack_modifier']} "
          f"= {attack_result['attack_roll']['total']} vs AC {attack_result['attack_roll']['target_ac']}")
    
    if attack_result['hit']:
        print(f"✅ 命中！")
        if attack_result['attack_roll']['is_critical']:
            print("🎯 暴击！")
        damage = attack_result['damage']['total']
        print(f"造成伤害: {damage}点")
        print(f"魔物HP: {attack_result['defender_hp_before']} → {attack_result['defender_hp_after']}")
    else:
        print("❌ 未命中")
    
    # 魔物攻击战士（使用爪击）
    monster_weapon = {
        'id': 'weapon_claw',
        'name': '爪击',
        'type': 'natural',
        'damage_dice': '1d6',
        'damage_type': 'slashing',
        'properties': []
    }
    
    print("\n【魔物攻击战士】")
    monster_attack = combat_system.make_attack_roll(
        attacker=monster,
        weapon=monster_weapon,
        target_ac=fighter['attributes']['ac']
    )
    
    # 计算魔物攻击调整值（STR + 熟练加值）
    monster_attack_modifier = monster['attributes']['ability_modifiers']['str'] + monster['attributes']['proficiency_bonus']
    
    print(f"攻击检定: {monster_attack['attack_roll']['roll']} "
          f"+ {monster_attack_modifier} "
          f"= {monster_attack['total']} vs AC {monster_attack['target_ac']}")
    
    if monster_attack['hit']:
        print(f"✅ 命中！")
        monster_damage = combat_system.calculate_damage(
            attacker=monster,
            weapon=monster_weapon,
            is_critical=monster_attack['is_critical']
        )
        print(f"造成伤害: {monster_damage['total']}点")
    else:
        print("❌ 未命中")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == '__main__':
    test_attribute_system()
    test_dice_system()
    test_proficiency_system()
    test_combat_system()

