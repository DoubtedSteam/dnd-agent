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
        characters_dir = os.path.join(base_dir, "themes", theme, "characters")
        # 如果新格式目录不存在，尝试旧格式（兼容）
        if not os.path.exists(characters_dir):
            characters_dir = os.path.join(base_dir, "themes", theme)
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
        
        check_prompt = f"""# Role: 一致性检查器 (Consistency Checker)

检查回答与历史一致性，提取具体化信息。

---

### 1. 输入信息 (Input)

**【当前场景】**
{current_scene_text}
**【历史场景】**
{history_text}
**【角色】**
{characters_text}

**【问题】**
{question}
**【回答】**
{answer}

---

### 2. 任务要求 (Task Requirements)

1. **一致性检查**: 是否有矛盾/冲突/与历史不符
2. **具体化信息提取**: 抽象→具体，区分表/里
3. **角色外貌/装备提取**: objective/subjective/inner

---

### 3. 输出格式 (Output Format)

输出JSON格式：
{{
    "consistency_score": 0.95,
    "consistency_feedback": "反馈",
    "concretized_info": {{
        "surface": {{}},
        "hidden": {{}}
    }},
    "scene_updates": {{
        "surface": {{}},
        "hidden": {{}}
    }},
    "major_events": [],
    "character_updates": {{
        "character_id": {{
            "appearance": {{
                "objective": "",
                "subjective": "",
                "inner": ""
            }},
            "equipment": {{
                "objective": "",
                "subjective": "",
                "inner": ""
            }}
        }}
    }}
}}
"""
        
        platform = platform or self.config.DEFAULT_API_PLATFORM
        
        try:
            # 记录token消耗
            try:
                from services.token_tracker import token_tracker
                operation = 'consistency_check'
            except ImportError:
                token_tracker = None
                operation = 'consistency_check'
            
            try:
                if platform.lower() == 'deepseek':
                    response_text = self.chat_service._call_deepseek_api(
                        [{"role": "system", "content": check_prompt},
                         {"role": "user", "content": "检查一致性并提取信息。"}],
                        operation='consistency_check',
                        context={'theme': theme, 'question': question[:50]}
                    )
                elif platform.lower() == 'openai':
                    response_text = self.chat_service._call_openai_api(
                        [{"role": "system", "content": check_prompt},
                         {"role": "user", "content": "检查一致性并提取信息。"}],
                        operation='consistency_check',
                        context={'theme': theme, 'question': question[:50]}
                    )
                elif platform.lower() == 'aizex':
                    response_text = self.chat_service._call_aizex_api(
                        [{"role": "system", "content": check_prompt},
                         {"role": "user", "content": "检查一致性并提取信息。"}],
                        operation='consistency_check',
                        context={'theme': theme, 'question': question[:50]}
                    )
                else:
                    raise ValueError(f"不支持的API平台: {platform}")
            except Exception as e:
                # API调用失败，返回默认值
                print(f"一致性检查API调用失败: {e}")
                return 0.5, f"一致性检查失败: {str(e)}", {
                    'concretized_info': {'surface': {}, 'hidden': {}},
                    'scene_updates': {'surface': {}, 'hidden': {}},
                    'major_events': [],
                    'character_updates': {}
                }
            
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

