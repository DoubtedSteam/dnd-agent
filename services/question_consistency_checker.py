"""
提问一致性检查器：检查提问回答与历史信息的一致性
"""
import json
import os
from typing import Dict, List, Optional, Tuple
from services.chat_service import ChatService
from config import Config


class QuestionConsistencyChecker:
    """提问一致性检查器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.chat_service = ChatService()
    
    def check_question_consistency(self, question: str, answer: str, theme: str,
                                  save_step: Optional[str], 
                                  previous_steps: List[str],
                                  platform: str = None) -> Tuple[float, str, Dict]:
        """
        检查提问回答与历史信息的一致性
        
        Args:
            question: 玩家问题
            answer: LLM的回答
            theme: 主题
            save_step: 当前存档步骤
            previous_steps: 之前的存档步骤列表（用于加载历史信息）
            platform: API平台
        
        Returns:
            (一致性评分 0-1, 反馈文本, 具体化信息字典)
        """
        # 加载历史场景信息
        history_scenes = []
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
        # 加载当前场景
        current_scene = None
        if save_step:
            scene_path = os.path.join(base_dir, self.config.SAVE_DIR, theme, save_step, "SCENE.md")
            if os.path.exists(scene_path):
                try:
                    with open(scene_path, "r", encoding="utf-8") as f:
                        current_scene = f.read()
                except:
                    pass
        
        # 加载历史场景（最多加载最近5个步骤）
        for step in reversed(previous_steps[-5:]):
            if step == save_step:
                continue
            scene_path = os.path.join(base_dir, self.config.SAVE_DIR, theme, step, "SCENE.md")
            if os.path.exists(scene_path):
                try:
                    with open(scene_path, "r", encoding="utf-8") as f:
                        history_scenes.append({
                            'step': step,
                            'content': f.read()
                        })
                except:
                    pass
        
        # 加载角色信息（用于识别角色ID）
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        characters_info = []
        characters_dir = os.path.join(base_dir, "characters", theme)
        if os.path.exists(characters_dir):
            for filename in os.listdir(characters_dir):
                if filename.endswith(".json"):
                    try:
                        char_path = os.path.join(characters_dir, filename)
                        with open(char_path, "r", encoding="utf-8") as f:
                            char_data = json.load(f)
                            characters_info.append({
                                'id': char_data.get('id', filename.replace('.json', '')),
                                'name': char_data.get('name', '')
                            })
                    except:
                        pass
        
        characters_text = ""
        if characters_info:
            characters_text = "\n\n【角色信息（用于识别角色ID）】\n"
            for char in characters_info:
                characters_text += f"- ID: {char['id']}, 名称: {char['name']}\n"
        
        # 构建一致性检查提示词
        history_text = ""
        if history_scenes:
            history_text = "\n\n【历史场景信息】\n"
            for hist in history_scenes:
                history_text += f"\n--- {hist['step']} ---\n{hist['content']}\n"
        
        current_scene_text = current_scene or "无当前场景信息"
        
        check_prompt = f"""你是一个一致性检查专家。请检查提问回答是否与历史信息一致，并提取具体化的信息。

【当前场景信息】
{current_scene_text}
{history_text}
{characters_text}

【提问和回答】
问题：{question}
回答：{answer}

请完成以下任务：

1. **一致性检查**：检查回答是否与历史场景信息一致
   - 是否有矛盾或冲突
   - 是否与之前的事件、状态、设定冲突
   - 是否引入了新的、与历史不符的信息

2. **具体化信息提取**：从回答中提取具体化的信息
   - 哪些抽象信息被具体化了
   - 这些信息应该如何更新到场景中
   - 区分表/里信息

3. **角色外貌和装备描述提取**：如果回答中明确化了角色的外貌或装备描述
   - 提取外貌描述（客观描述、队友主观看到的、角色内心想法）
   - 提取装备描述（客观描述、队友主观看到的、角色内心想法）
   - 这些信息应该更新到对应角色的人物卡中

请以JSON格式回复：
{{
    "consistency_score": 0.95,  // 一致性评分，0-1之间
    "consistency_feedback": "回答与历史信息一致，没有发现矛盾...",  // 一致性反馈
    "concretized_info": {{
        "surface": {{
            // 玩家可见的具体化信息，如：当前叙述、目标、资源等
        }},
        "hidden": {{
            // 隐藏的具体化信息，如：潜在风险、隐藏目标等
        }}
    }},
    "scene_updates": {{
        // 建议的场景更新内容
        "surface": {{}},
        "hidden": {{}}
    }},
    "major_events": [
        // 如果有新的事件，列出事件列表
    ],
    "character_updates": {{
        // 角色外貌和装备描述的具体化信息
        "character_id": {{
            "appearance": {{
                "objective": "客观的外貌描述（如身高、体型、肤色等）",
                "subjective": "队友主观看到的外貌（如看起来如何、给人的感觉等）",
                "inner": "角色内心关于外貌的想法（如对自己的外貌的感受等）"
            }},
            "equipment": {{
                "objective": "客观的装备描述（如装备的具体外观、材质等）",
                "subjective": "队友主观看到的装备（如装备给人的感觉、是否显眼等）",
                "inner": "角色内心关于装备的想法（如对装备的重视程度、使用感受等）"
            }}
        }}
    }}
}}"""
        
        platform = platform or self.config.DEFAULT_API_PLATFORM
        
        try:
            # 记录token消耗
            try:
                from services.token_tracker import token_tracker
                operation = 'consistency_check'
            except ImportError:
                token_tracker = None
                operation = 'consistency_check'
            
            if platform.lower() == 'deepseek':
                response_text = self.chat_service._call_deepseek_api(
                    [{"role": "system", "content": check_prompt},
                     {"role": "user", "content": "请检查一致性并提取具体化信息。"}],
                    operation='consistency_check',
                    context={'theme': theme, 'question': question[:50]}
                )
            elif platform.lower() == 'openai':
                response_text = self.chat_service._call_openai_api(
                    [{"role": "system", "content": check_prompt},
                     {"role": "user", "content": "请检查一致性并提取具体化信息。"}],
                    operation='consistency_check',
                    context={'theme': theme, 'question': question[:50]}
                )
            else:
                raise ValueError(f"不支持的API平台: {platform}")
            
            # 解析响应
            try:
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                result = json.loads(response_text)
                score = float(result.get('consistency_score', 0.5))
                feedback = result.get('consistency_feedback', '')
                concretized_info = result.get('concretized_info', {'surface': {}, 'hidden': {}})
                scene_updates = result.get('scene_updates', {'surface': {}, 'hidden': {}})
                major_events = result.get('major_events', [])
                character_updates = result.get('character_updates', {})
                
                # 确保评分在0-1范围内
                score = max(0.0, min(1.0, score))
                
                return score, feedback, {
                    'concretized_info': concretized_info,
                    'scene_updates': scene_updates,
                    'major_events': major_events,
                    'character_updates': character_updates
                }
            except json.JSONDecodeError:
                # 如果解析失败，返回默认值
                return 0.5, "解析一致性检查结果失败", {
                    'concretized_info': {'surface': {}, 'hidden': {}},
                    'scene_updates': {'surface': {}, 'hidden': {}},
                    'major_events': [],
                    'character_updates': {}
                }
        except Exception as e:
            return 0.5, f"一致性检查失败: {str(e)}", {
                'concretized_info': {'surface': {}, 'hidden': {}},
                'scene_updates': {'surface': {}, 'hidden': {}},
                'major_events': [],
                'character_updates': {}
            }

