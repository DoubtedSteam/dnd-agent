"""
DND战斗系统使用示例
展示如何使用DND数值系统进行战斗
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.numeric_system import CombatSystem, AttributeSystem, ProficiencySystem
from services.numeric_system.character_helper import CharacterHelper


def main():
    """主函数：演示战士与魔物的战斗"""
    print("=" * 70)
    print("DND战斗系统演示：战士 vs 田野魔物")
    print("=" * 70)
    print()
    
    # 创建角色辅助类
    helper = CharacterHelper()
    
    # 创建战士角色
    fighter = {
        'id': 'char_adventurer_001',
        'name': '冒险者',
        'attributes': {
            'weapon': {'main_hand': '长剑', 'off_hand': '盾牌'},
            'equipment': {'armor': '皮甲'}
        }
    }
    
    # 初始化战士DND属性（1级战士，力量16，敏捷14，体质15）
    helper.initialize_dnd_attributes(
        fighter,
        str_score=16,  # 力量+3
        dex_score=14,  # 敏捷+2
        con_score=15,  # 体质+2
        int_score=10,
        wis_score=12,
        cha_score=8,
        level=1,
        class_name='fighter'
    )
    
    print("【战士属性】")
    print(f"  力量: {fighter['attributes']['ability_scores']['str']} "
          f"(调整值+{fighter['attributes']['ability_modifiers']['str']})")
    print(f"  敏捷: {fighter['attributes']['ability_scores']['dex']} "
          f"(调整值+{fighter['attributes']['ability_modifiers']['dex']})")
    print(f"  体质: {fighter['attributes']['ability_scores']['con']} "
          f"(调整值+{fighter['attributes']['ability_modifiers']['con']})")
    print(f"  AC: {fighter['attributes']['ac']}")
    print(f"  HP: {fighter['attributes']['vitals']['current_hp']}/"
          f"{fighter['attributes']['vitals']['max_hp']}")
    print(f"  熟练加值: +{fighter['attributes']['proficiency_bonus']}")
    print()
    
    # 创建魔物
    attr_system = AttributeSystem()
    prof_system = ProficiencySystem()
    
    monster = {
        'id': 'monster_field_001',
        'name': '田野魔物',
        'attributes': {
            'ability_scores': {
                'str': 18,  # 力量+4
                'dex': 14,  # 敏捷+2
                'con': 16,  # 体质+3
                'int': 6,
                'wis': 12,
                'cha': 6
            },
            'level': 3,
            'weapon': {'main_hand': '爪击'},
            'equipment': {'armor': 'none'}
        }
    }
    
    # 初始化魔物属性
    monster['attributes']['ability_modifiers'] = attr_system.get_all_modifiers(monster)
    monster['attributes']['proficiency_bonus'] = prof_system.get_proficiency_bonus(3)
    monster['attributes']['ac'] = 13  # 10 + DEX(2) + 1（天然护甲）
    monster['attributes']['vitals'] = {
        'max_hp': 30,
        'current_hp': 30
    }
    monster['attributes']['proficiencies'] = {
        'weapons': ['natural'],
        'skills': ['perception', 'stealth'],
        'saving_throws': ['dex', 'con']
    }
    
    print("【魔物属性】")
    print(f"  力量: {monster['attributes']['ability_scores']['str']} "
          f"(调整值+{monster['attributes']['ability_modifiers']['str']})")
    print(f"  敏捷: {monster['attributes']['ability_scores']['dex']} "
          f"(调整值+{monster['attributes']['ability_modifiers']['dex']})")
    print(f"  AC: {monster['attributes']['ac']}")
    print(f"  HP: {monster['attributes']['vitals']['current_hp']}/"
          f"{monster['attributes']['vitals']['max_hp']}")
    print(f"  熟练加值: +{monster['attributes']['proficiency_bonus']}")
    print()
    
    # 创建战斗系统
    combat_system = CombatSystem(theme='village_quest')
    
    print("=" * 70)
    print("战斗开始！")
    print("=" * 70)
    print()
    
    # 进行3轮战斗
    for round_num in range(1, 4):
        print(f"【第 {round_num} 轮】")
        print("-" * 70)
        
        # 战士攻击魔物
        print(f"\n{fighter['name']} 攻击 {monster['name']}...")
        attack_result = combat_system.execute_attack(
            attacker=fighter,
            defender=monster,
            weapon_name='长剑'
        )
        
        roll = attack_result['attack_roll']['attack_roll']['roll']
        modifier = attack_result['attack_roll']['attack_modifier']
        total = attack_result['attack_roll']['total']
        target_ac = attack_result['attack_roll']['target_ac']
        
        print(f"  攻击检定: d20({roll}) + {modifier} = {total} vs AC {target_ac}")
        
        if attack_result['hit']:
            if attack_result['attack_roll']['is_critical']:
                print("  🎯 暴击！")
            damage = attack_result['damage']['total']
            print(f"  ✅ 命中！造成 {damage} 点伤害")
            print(f"  {monster['name']} HP: {attack_result['defender_hp_before']} → "
                  f"{attack_result['defender_hp_after']}")
            
            # 更新魔物HP
            monster['attributes']['vitals']['current_hp'] = attack_result['defender_hp_after']
            
            # 检查魔物是否被击败
            if attack_result['defender_hp_after'] <= 0:
                print(f"\n🎉 {monster['name']} 被击败了！")
                break
        else:
            print("  ❌ 未命中")
        
        # 魔物攻击战士
        print(f"\n{monster['name']} 攻击 {fighter['name']}...")
        monster_weapon = combat_system.equip_system.get_weapon_data('爪击')
        if monster_weapon:
            monster_attack = combat_system.make_attack_roll(
                attacker=monster,
                weapon=monster_weapon,
                target_ac=fighter['attributes']['ac']
            )
            
            # 计算魔物攻击调整值
            monster_attack_modifier = (monster['attributes']['ability_modifiers']['str'] + 
                                      monster['attributes']['proficiency_bonus'])
            
            roll = monster_attack['attack_roll']['roll']
            total = monster_attack['total']
            target_ac = monster_attack['target_ac']
            
            print(f"  攻击检定: d20({roll}) + {monster_attack_modifier} = {total} vs AC {target_ac}")
            
            if monster_attack['hit']:
                if monster_attack['is_critical']:
                    print("  🎯 暴击！")
                monster_damage = combat_system.calculate_damage(
                    attacker=monster,
                    weapon=monster_weapon,
                    is_critical=monster_attack['is_critical']
                )
                print(f"  ✅ 命中！造成 {monster_damage['total']} 点伤害")
                
                # 更新战士HP
                fighter_hp = fighter['attributes']['vitals']['current_hp']
                fighter_hp_after = max(0, fighter_hp - monster_damage['total'])
                fighter['attributes']['vitals']['current_hp'] = fighter_hp_after
                print(f"  {fighter['name']} HP: {fighter_hp} → {fighter_hp_after}")
                
                # 检查战士是否被击败
                if fighter_hp_after <= 0:
                    print(f"\n💀 {fighter['name']} 被击败了！")
                    break
            else:
                print("  ❌ 未命中")
        
        print()
    
    print("=" * 70)
    print("战斗结束")
    print("=" * 70)
    print(f"\n最终状态：")
    print(f"  {fighter['name']} HP: {fighter['attributes']['vitals']['current_hp']}/"
          f"{fighter['attributes']['vitals']['max_hp']}")
    print(f"  {monster['name']} HP: {monster['attributes']['vitals']['current_hp']}/"
          f"{monster['attributes']['vitals']['max_hp']}")


if __name__ == '__main__':
    main()

