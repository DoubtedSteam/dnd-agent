import os
import requests
import json
from typing import List, Dict, Optional
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


class ChatService:
    """对话服务，支持多个API平台"""
    
    def __init__(self):
        self.config = Config()

    def _load_attr_guide(self, theme: str) -> str:
        """读取属性说明文档，优先主题目录，其次根目录，最后默认文本"""
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
    
    def _call_deepseek_api(self, messages: List[Dict], temperature: float = 0.7, 
                           operation: str = "chat", context: Dict = None) -> str:
        """调用DeepSeek API"""
        url = f"{self.config.DEEPSEEK_API_BASE}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": temperature
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # 记录LLM调用（如果记录器可用）
        usage = result.get('usage', {})
        try:
            from tests.llm_call_logger import logger
            logger.log_call(
                platform='deepseek',
                messages=messages,
                response=content,
                model='deepseek-chat',
                temperature=temperature,
                usage=usage
            )
        except ImportError:
            pass  # 记录器不可用时忽略
        
        # 记录token消耗
        try:
            from services.token_tracker import token_tracker
            token_tracker.record_call(
                platform='deepseek',
                model='deepseek-chat',
                usage=usage,
                operation=operation,
                context=context or {}
            )
        except ImportError:
            pass
        
        return content
    
    def _call_openai_api(self, messages: List[Dict], temperature: float = 0.7,
                        operation: str = "chat", context: Dict = None) -> str:
        """调用OpenAI API"""
        url = f"{self.config.OPENAI_API_BASE}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "temperature": temperature
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # 记录LLM调用（如果记录器可用）
        usage = result.get('usage', {})
        try:
            from tests.llm_call_logger import logger
            logger.log_call(
                platform='openai',
                messages=messages,
                response=content,
                model='gpt-3.5-turbo',
                temperature=temperature,
                usage=usage
            )
        except ImportError:
            pass  # 记录器不可用时忽略
        
        # 记录token消耗
        try:
            from services.token_tracker import token_tracker
            token_tracker.record_call(
                platform='openai',
                model='gpt-3.5-turbo',
                usage=usage,
                operation=operation,
                context=context or {}
            )
        except ImportError:
            pass
        
        return content
    
    def chat(self, character_description: str, character_attributes: Dict,
             user_message: str, platform: str = None, theme: str = "default",
             save_step: Optional[str] = None) -> str:
        """
        生成角色对话回复
        
        Args:
            character_description: 人物描述/人设
            character_attributes: 人物属性（JSON）
            user_message: 用户消息
            platform: API平台（deepseek/openai），默认使用配置的平台
            theme: 主题名称
            save_step: 存档步骤（如 "0_step"），用于加载存档状态
        
        Returns:
            角色回复内容
        """
        platform = platform or self.config.DEFAULT_API_PLATFORM
        theme = theme or "default"
        attr_guide = self._load_attr_guide(theme)
        scene_content = self._load_scene(theme, save_step)
        
        # 构建系统提示词
        system_prompt = f"""你是一个角色扮演助手。请严格按照以下设定进行对话。

【信息来源：人物卡配置】
=== 人物设定 ===
人物描述：
{character_description}

人物属性（结构化设定，仅用于参考，不要机械复述）：
{json.dumps(character_attributes, ensure_ascii=False, indent=2)}

【信息来源：CHARACTER_ATTRIBUTES.md - 属性字段含义说明】
{attr_guide}
"""
        
        if scene_content:
            if save_step:
                scene_source = f"save/{theme}/{save_step}/SCENE.md - 当前场景状态（存档）"
            else:
                scene_source = f"characters/{theme}/SCENE.md - 初始场景设定"
            
            system_prompt += f"""
【信息来源：{scene_source}】
=== 场景设定 ===
{scene_content}
"""
        
        system_prompt += """
=== 重要要求 ===
1. 始终保持角色的一致性，严格遵循人物设定中的性格、背景和说话风格
2. 结合场景设定理解当前情境（时间、地点、背景、目标、重大事件等）
3. 场景设定包含表/里两层信息，表信息是玩家可见的，里信息帮助你理解隐藏的推演信息
4. 注意区分表/里信息：
   - 表信息（surface）：玩家可见的直观状态，角色应该表现出的外在状态
   - 里信息（hidden）：隐藏的推演信息，帮助你理解角色的真实想法、内心独白和客观观察状态
5. 参考场景中的"重大事件"了解当前游戏进展，这些事件会影响角色的行为和对话
6. 在生成对话时，要自然体现角色的内在想法，但不要直接暴露里信息
7. 不要打破角色设定，自然地回应对话，让对话符合当前情境
8. 不需要记忆之前的对话内容，仅根据当前场景状态和人物设定生成回复
"""
        
        # 构建消息列表（不使用对话历史）
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # 根据平台调用不同的API
        if platform.lower() == 'deepseek':
            return self._call_deepseek_api(messages, operation='chat', 
                                           context={'theme': theme, 'save_step': save_step})
        elif platform.lower() == 'openai':
            return self._call_openai_api(messages, operation='chat',
                                        context={'theme': theme, 'save_step': save_step})
        else:
            raise ValueError(f"不支持的API平台: {platform}")

