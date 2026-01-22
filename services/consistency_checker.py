import os
import requests
import json
from typing import List, Dict, Optional, Tuple
from config import Config

DEFAULT_ATTR_GUIDE = """
属性说明（用于参考，不要逐字复述）：
- gender: 性别
- vitals: { hp, mp, stamina } 生命/魔法/体力
- weapon: { main_hand, off_hand, backup, ranged } 武器与备用武器
- equipment: 盔甲/法袍、头盔/帽子、靴子、饰品等
- skills: 技能列表，可包含主动与被动
- traits: 性格或特点
- background: 背景
- speaking_style: 说话风格
"""


class ConsistencyChecker:
    """一致性检测服务"""
    
    def __init__(self):
        self.config = Config()

    def _load_attr_guide(self, theme: str) -> str:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        candidates = [
            os.path.join(base_dir, self.config.CHARACTER_CONFIG_DIR, theme, "CHARACTER_ATTRIBUTES.md"),
            os.path.join(base_dir, "CHARACTER_ATTRIBUTES.md"),
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return f.read()
                except Exception:
                    continue
        return DEFAULT_ATTR_GUIDE
    
    def _load_scene(self, theme: str, save_step: Optional[str] = None) -> Optional[str]:
        """读取场景设定文件，优先读取存档场景，其次初始场景"""
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
        # 优先读取存档场景
        if save_step:
            scene_path = os.path.join(base_dir, self.config.SAVE_DIR, theme, save_step, "SCENE.md")
            if os.path.exists(scene_path):
                try:
                    with open(scene_path, "r", encoding="utf-8") as f:
                        return f.read()
                except Exception:
                    pass
        
        # 其次读取初始场景
        scene_path = os.path.join(base_dir, self.config.CHARACTER_CONFIG_DIR, theme, "SCENE.md")
        if os.path.exists(scene_path):
            try:
                with open(scene_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
        return None
    
    def _call_api(self, messages: List[Dict], platform: str = None) -> str:
        """调用API进行检测"""
        platform = platform or self.config.CONSISTENCY_CHECK_API
        
        if platform.lower() == 'deepseek':
            url = f"{self.config.DEEPSEEK_API_BASE}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.config.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.config.DEEPSEEK_MODEL,
                "messages": messages,
                "temperature": 0.3  # 使用较低温度以获得更稳定的评估
            }
        elif platform.lower() == 'openai':
            url = f"{self.config.OPENAI_API_BASE}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.config.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.config.OPENAI_MODEL,
                "messages": messages,
                "temperature": 0.3
            }
        elif platform.lower() == 'aizex':
            # 处理URL，避免重复路径
            base_url = self.config.AIZEX_API_BASE.rstrip('/')
            if base_url.endswith('/chat/completions'):
                url = base_url
            else:
                url = f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.config.AIZEX_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.config.AIZEX_MODEL,
                "messages": messages,
                "temperature": 0.3
            }
        else:
            raise ValueError(f"不支持的API平台: {platform}")
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    
    def check_consistency(self, character_description: str, 
                         character_attributes: Dict,
                         user_message: str,
                         latest_response: str,
                         platform: str = None,
                         theme: str = "default",
                         save_step: Optional[str] = None) -> Tuple[float, str]:
        """
        检测对话的一致性
        
        Args:
            character_description: 人物描述/人设
            character_attributes: 人物属性（JSON）
            user_message: 用户消息
            latest_response: 最新的角色回复
            platform: API平台
            theme: 主题名称
            save_step: 存档步骤（如 "0_step"），用于加载存档状态
        
        Returns:
            (一致性评分 0-1, 反馈文本)
        """
        if not self.config.CONSISTENCY_CHECK_ENABLED:
            return None, None
        theme = theme or "default"
        attr_guide = self._load_attr_guide(theme)
        scene_content = self._load_scene(theme, save_step)
        
        # 构建检测提示词
        check_prompt = f"""# Role: 一致性检测器 (Consistency Checker)

评估角色回复是否符合设定。

---

### 1. 输入信息 (Input)

**【人物卡】**
- 描述: {character_description}
- 属性: {json.dumps(character_attributes, ensure_ascii=False)}
**【属性说明】**
{attr_guide}
{'\n**【场景】**\n' + scene_content if scene_content else ''}

**【对话】**
- 用户: {user_message}
- 角色: {latest_response}

---

### 2. 评估要求 (Evaluation Requirements)

评估以下方面：
1. **性格设定**: 是否符合角色性格特点
2. **场景状态**: 是否符合当前场景状态
3. **违和感**: 是否有违和感或不一致的地方

---

### 3. 输出格式 (Output Format)

输出JSON格式：
{{
    "score": 0.95,
    "feedback": "反馈内容"
}}
"""
        
        messages = [{"role": "user", "content": check_prompt}]
        
        try:
            result_text = self._call_api(messages, platform)
            
            # 尝试解析JSON结果
            # 如果结果包含代码块，提取JSON部分
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            elif "```" in result_text:
                json_start = result_text.find("```") + 3
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            
            result = json.loads(result_text)
            score = float(result.get('score', 0.5))
            feedback = result.get('feedback', '')
            
            # 确保评分在0-1范围内
            score = max(0.0, min(1.0, score))
            
            return score, feedback
        except Exception as e:
            # 如果解析失败，返回默认值
            return 0.5, f"检测过程中出现错误: {str(e)}"

