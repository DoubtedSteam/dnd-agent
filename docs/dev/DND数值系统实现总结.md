# DND数值系统实现总结

## 已完成功能

### ✅ 1. DND属性系统 (`AttributeSystem`)
- **6大基础属性**：力量(STR)、敏捷(DEX)、体质(CON)、智力(INT)、感知(WIS)、魅力(CHA)
- **属性调整值计算**：`(属性值 - 10) / 2`，向下取整
- **属性验证**：支持1-30的属性值范围
- **属性获取**：提供便捷的属性值和调整值获取方法

**文件位置**：`services/numeric_system/attribute_system.py`

### ✅ 2. 掷骰系统 (`DiceSystem`)
- **d20掷骰**：核心战斗检定骰子
- **多面骰支持**：支持d4, d6, d8, d10, d12, d20, d100
- **优势/劣势系统**：掷两次取较高/较低值
- **武器伤害骰**：支持伤害骰计算，包括暴击时伤害骰翻倍
- **骰子表示法解析**：支持如 "2d6+3" 的格式

**文件位置**：`services/numeric_system/dice_system.py`

### ✅ 3. 熟练系统 (`ProficiencySystem`)
- **熟练加值表**：根据等级提供+2到+6的熟练加值
- **武器熟练**：检查角色是否熟练使用某种武器类型
- **技能熟练**：检查角色是否熟练某项技能
- **豁免熟练**：检查角色是否熟练某项豁免检定
- **攻击调整值计算**：自动计算攻击检定调整值（属性调整值 + 熟练加值）

**文件位置**：`services/numeric_system/proficiency_system.py`

### ✅ 4. 装备系统 (`EquipmentSystem`)
- **AC计算**：根据护甲类型和DEX调整值计算AC
  - 无甲：AC = 10 + DEX调整值
  - 轻甲：AC = 护甲基础AC + DEX调整值（无上限）
  - 中甲：AC = 护甲基础AC + DEX调整值（最高+2）
  - 重甲：AC = 护甲基础AC（不受DEX影响）
  - 盾牌：+2 AC
- **装备数据加载**：从JSON文件加载武器和护甲数据
- **武器数据获取**：根据武器名称获取武器属性（伤害骰、类型等）

**文件位置**：`services/numeric_system/equipment_system.py`

### ✅ 5. 战斗系统 (`CombatSystem`)
- **攻击检定**：
  - 攻击检定 = d20 + 属性调整值 + 熟练加值
  - 命中条件：攻击检定 >= 目标AC
  - 自然20：自动命中并暴击
  - 自然1：自动未命中
- **伤害计算**：
  - 基础伤害 = 武器伤害骰（如1d8）
  - 属性加值 = STR调整值（近战）或DEX调整值（远程/灵巧）
  - 最终伤害 = 基础伤害 + 属性加值
  - 暴击伤害 = 所有伤害骰翻倍 + 属性加值
- **完整攻击流程**：`execute_attack()` 方法执行完整的攻击流程（攻击检定 + 伤害计算 + HP更新）

**文件位置**：`services/numeric_system/combat_system.py`

### ✅ 6. 角色辅助类 (`CharacterHelper`)
- **DND属性初始化**：一键初始化角色的DND属性
- **衍生属性更新**：自动计算AC、熟练加值、先攻等衍生属性
- **HP计算**：根据职业和体质计算最大HP

**文件位置**：`services/numeric_system/character_helper.py`

### ✅ 7. 数据文件更新
- **角色模板**：更新 `themes/village_quest/characters/adventurer.json`，添加DND属性
- **怪物模板**：更新 `themes/village_quest/monsters/field_monster.json`，添加DND属性
- **装备库**：创建 `themes/village_quest/equipment/weapons.json` 和 `armor.json`

## 使用示例

### 基本使用

```python
from services.numeric_system import CombatSystem, AttributeSystem
from services.numeric_system.character_helper import CharacterHelper

# 创建角色辅助类
helper = CharacterHelper()

# 创建并初始化战士
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

# 创建战斗系统
combat_system = CombatSystem(theme='village_quest')

# 执行攻击
attack_result = combat_system.execute_attack(
    attacker=fighter,
    defender=monster,
    weapon_name='长剑'
)

if attack_result['hit']:
    print(f"造成 {attack_result['damage']['total']} 点伤害")
```

### 完整示例

查看 `examples/dnd_combat_example.py` 获取完整的战斗演示。

## 测试

运行测试文件验证功能：

```bash
python tests/test_dnd_combat.py
```

## 数据结构

### 角色属性结构

```json
{
  "attributes": {
    "ability_scores": {
      "str": 16,
      "dex": 14,
      "con": 15,
      "int": 10,
      "wis": 12,
      "cha": 8
    },
    "ability_modifiers": {
      "str": 3,
      "dex": 2,
      "con": 2,
      "int": 0,
      "wis": 1,
      "cha": -1
    },
    "level": 1,
    "class": "fighter",
    "proficiency_bonus": 2,
    "proficiencies": {
      "weapons": ["simple_melee", "martial_melee"],
      "skills": ["athletics", "perception"],
      "saving_throws": ["str", "con"]
    },
    "ac": 13,
    "initiative": 2,
    "vitals": {
      "max_hp": 12,
      "current_hp": 12,
      "hit_dice": "1d10"
    }
  }
}
```

### 武器数据结构

```json
{
  "id": "weapon_longsword",
  "name": "长剑",
  "type": "martial_melee",
  "damage_dice": "1d8",
  "damage_type": "slashing",
  "properties": ["versatile"],
  "versatile_damage": "1d10"
}
```

### 护甲数据结构

```json
{
  "id": "armor_leather",
  "name": "皮甲",
  "type": "light",
  "ac": 11,
  "max_dex_bonus": null,
  "stealth_disadvantage": false
}
```

## 核心规则实现

### 属性调整值表
| 属性值 | 调整值 | 属性值 | 调整值 |
|--------|--------|--------|--------|
| 1      | -5     | 10-11  | 0      |
| 2-3    | -4     | 12-13  | +1     |
| 4-5    | -3     | 14-15  | +2     |
| 6-7    | -2     | 16-17  | +3     |
| 8-9    | -1     | 18-19  | +4     |
|        |        | 20     | +5     |

### 熟练加值表
| 等级 | 熟练加值 | 等级 | 熟练加值 |
|------|----------|------|----------|
| 1-4  | +2       | 13-16| +5       |
| 5-8  | +3       | 17-20| +6       |
| 9-12 | +4       |      |          |

## 下一步工作

### 待实现功能
1. **技能检定系统**：18项技能的检定
2. **豁免检定系统**：6大豁免检定
3. **状态效果系统**：Buff/Debuff管理
4. **法术系统**：法术位管理和法术攻击
5. **成长系统**：经验值和等级提升
6. **集成到导演评估系统**：在战斗判定中使用DND数值系统

### 优化方向
1. **装备数据扩展**：添加更多武器和护甲
2. **职业系统**：实现不同职业的特殊能力
3. **战斗AI**：智能战斗决策
4. **战斗日志**：详细的战斗过程记录

## 文件结构

```
services/numeric_system/
├── __init__.py              # 模块导出
├── attribute_system.py      # 属性系统
├── dice_system.py           # 掷骰系统
├── proficiency_system.py    # 熟练系统
├── equipment_system.py     # 装备系统
├── combat_system.py         # 战斗系统
└── character_helper.py      # 角色辅助类

themes/village_quest/
├── characters/
│   └── adventurer.json      # 角色模板（已更新DND属性）
├── monsters/
│   └── field_monster.json   # 怪物模板（已更新DND属性）
└── equipment/
    ├── weapons.json         # 武器库
    └── armor.json           # 护甲库
```

## 总结

✅ **已完成核心功能**：
- DND属性系统和调整值计算
- d20掷骰系统和伤害计算
- 攻击检定和伤害计算
- AC计算和装备系统
- 武器伤害骰系统

✅ **战士可以正确消灭魔物**：
- 攻击检定使用d20 + 属性调整值 + 熟练加值
- 伤害计算使用武器伤害骰 + 属性调整值
- 暴击时伤害骰翻倍
- HP正确更新

系统已可以用于实际的战斗计算！

