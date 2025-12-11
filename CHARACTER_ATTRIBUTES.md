# 人物属性说明

用于为LLM提供结构化的人设参考，避免遗漏关键信息。

## 字段含义

- `gender`：性别。
- `vitals`：生命与资源数值。
  - `hp`：生命值。
  - `mp`：魔法值/法力。
  - `stamina`：体力/耐力。
- `weapon`：武器栏，细化为多槽位。
  - `main_hand`：主手武器。
  - `off_hand`：副手或盾牌。
  - `backup`：备用武器。
  - `ranged`：远程武器或投掷物。
- `equipment`：装备栏。
  - 可包含 `armor/robe`、`helmet/hat`、`boots`、`mask/hood`、`accessory`(数组) 等。
- `skills`：技能列表（主动/被动皆可，名称或简述）。
- `traits`：性格或特点关键词。
- `background`：背景故事简述。
- `speaking_style`：说话风格与口吻要求。
- `state`：状态信息，分为表/里。
  - `surface.perceived_state`：玩家/外部角色可见的直观状态（主观）。
  - `hidden.observer_state`：第三者客观观察到的状态（LLM用，不必公开）。
  - `hidden.inner_monologue`：人物内心独白或潜在倾向（LLM用，不必公开）。

