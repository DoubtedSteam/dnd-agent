# 从提问中更新角色卡

## 概述

当玩家提问时，如果回答中明确化了角色的外貌或装备描述，系统会自动提取这些信息并更新到对应角色的人物卡中。

## 功能特性

### 1. 自动提取

系统会从提问的回答中提取：
- **外貌描述**：客观描述、队友主观看到的、角色内心想法
- **装备描述**：客观描述、队友主观看到的、角色内心想法

### 2. 分类存储

提取的信息会按照三个部分存储到角色卡的 `state` 字段中：

| 部分 | 存储位置 | 说明 |
|------|---------|------|
| **客观描述** | `state.hidden.observer_state` | 客观的外貌/装备描述 |
| **队友主观** | `state.surface.perceived_state` | 队友主观看到的外貌/装备 |
| **内心想法** | `state.hidden.inner_monologue` | 角色内心关于外貌/装备的想法 |

## 工作流程

1. **玩家提问**：例如 "勇者看起来怎么样？"
2. **LLM回答**：回答中可能包含外貌描述
3. **一致性检查**：检查回答与历史信息的一致性
4. **提取信息**：从回答中提取外貌/装备描述
5. **更新角色卡**：如果一致性检查通过（评分>=0.7），更新角色卡

## 更新条件

角色卡更新需要满足以下条件：

1. **一致性检查通过**：评分 >= 0.7
2. **创建新步骤**：会创建新的存档步骤
3. **提取到信息**：回答中确实包含外貌或装备描述

## 示例

### 提问示例

```
> ask 勇者看起来怎么样？
```

### LLM回答示例

```
勇者艾伦看起来高大强壮，身高约180cm，肌肉结实。他穿着闪亮的骑士胸甲，手持精钢长剑，给人一种可靠的感觉。他对自己装备的维护很在意。
```

### 提取的信息

系统会提取：

```json
{
  "character_updates": {
    "hero": {
      "appearance": {
        "objective": "身高约180cm，肌肉结实",
        "subjective": "高大强壮，给人一种可靠的感觉",
        "inner": "对自己装备的维护很在意"
      },
      "equipment": {
        "objective": "闪亮的骑士胸甲，精钢长剑",
        "subjective": "装备看起来很专业",
        "inner": "很在意装备的维护"
      }
    }
  }
}
```

### 更新后的角色卡

角色卡的 `state` 字段会被更新：

```json
{
  "attributes": {
    "state": {
      "surface": {
        "perceived_state": "高大强壮，给人一种可靠的感觉\n装备（主观）: 装备看起来很专业"
      },
      "hidden": {
        "observer_state": "身高约180cm，肌肉结实\n装备（客观）: 闪亮的骑士胸甲，精钢长剑",
        "inner_monologue": "对自己装备的维护很在意\n装备（内心）: 很在意装备的维护"
      }
    }
  }
}
```

## 技术实现

### QuestionConsistencyChecker

`services/question_consistency_checker.py` 负责：
1. 检查一致性
2. 提取具体化信息（包括角色外貌和装备描述）

### StateUpdater

`services/state_updater.py` 的 `update_character_appearance_and_equipment()` 方法负责：
1. 读取角色卡
2. 更新 `state` 字段的三个部分
3. 保存更新后的角色卡

### QuestionService

`services/question_service.py` 负责：
1. 调用一致性检查
2. 如果检查通过，调用状态更新器更新角色卡

## 注意事项

1. **角色ID识别**：系统需要正确识别角色ID，如果提问中提到的角色名称无法匹配到角色ID，更新会失败
2. **信息合并**：新信息会追加到现有信息后，不会覆盖
3. **存档步骤**：更新会创建新的存档步骤，不会修改现有步骤
4. **一致性要求**：只有一致性检查通过（评分>=0.7）才会更新

## 角色卡结构

角色卡的 `state` 字段结构：

```json
{
  "attributes": {
    "state": {
      "surface": {
        "perceived_state": "队友主观看到的状态（包括外貌和装备的主观描述）"
      },
      "hidden": {
        "observer_state": "客观观察状态（包括外貌和装备的客观描述）",
        "inner_monologue": "内心独白（包括角色关于外貌和装备的内心想法）"
      }
    }
  }
}
```

## 相关文件

- `services/question_consistency_checker.py` - 一致性检查和信息提取
- `services/question_service.py` - 提问服务
- `services/state_updater.py` - 状态更新器
- `characters/{theme}/{character_id}.json` - 角色卡文件

