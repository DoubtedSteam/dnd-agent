import os
import requests
import json
from typing import List, Dict, Optional
from config import Config
from services.api_failure_handler import api_failure_handler, APIConfirmationRequired

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
                           operation: str = "chat", context: Dict = None, 
                           max_retries: int = 3) -> str:
        """调用DeepSeek API（带重试机制）"""
        url = f"{self.config.DEEPSEEK_API_BASE}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.config.DEEPSEEK_MODEL,
            "messages": messages,
            "temperature": temperature
        }
        
        # 重试机制
        last_exception = None
        for attempt in range(max_retries):
            try:
                # 超时时间：第一次30秒，重试时增加到60秒
                timeout = 60 if attempt > 0 else 30
                response = requests.post(url, headers=headers, json=data, timeout=timeout)
                response.raise_for_status()
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # 成功，跳出重试循环
                break
            except requests.exceptions.Timeout as e:
                last_exception = e
                if attempt < max_retries - 1:
                    print(f"API调用超时，正在重试 ({attempt + 1}/{max_retries})...")
                    import time
                    time.sleep(2 * (attempt + 1))  # 指数退避
                else:
                    # 记录失败并检查是否需要用户确认
                    error_msg = f"API调用超时，已重试{max_retries}次: {str(e)}"
                    try:
                        should_continue = api_failure_handler.record_failure(error_msg)
                        if not should_continue:
                            raise Exception("用户选择停止API调用")
                    except APIConfirmationRequired as confirm_ex:
                        raise confirm_ex
                    raise Exception(error_msg)
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < max_retries - 1:
                    print(f"API调用失败，正在重试 ({attempt + 1}/{max_retries}): {str(e)}")
                    import time
                    time.sleep(2 * (attempt + 1))
                else:
                    # 记录失败并检查是否需要用户确认
                    error_msg = f"API调用失败，已重试{max_retries}次: {str(e)}"
                    try:
                        should_continue = api_failure_handler.record_failure(error_msg)
                        if not should_continue:
                            raise Exception("用户选择停止API调用")
                    except APIConfirmationRequired as confirm_ex:
                        raise confirm_ex
                    raise Exception(error_msg)
            except APIConfirmationRequired:
                # 重新抛出确认异常
                raise
            except Exception as e:
                # 其他错误直接抛出
                raise
        
        if last_exception and 'content' not in locals():
            error_msg = f"API调用失败: {str(last_exception)}"
            try:
                should_continue = api_failure_handler.record_failure(error_msg)
                if not should_continue:
                    raise Exception("用户选择停止API调用")
            except APIConfirmationRequired as confirm_ex:
                raise confirm_ex
            raise Exception(error_msg)
        
        # API调用成功，重置失败计数
        api_failure_handler.record_success()
        
        # 记录LLM调用（如果记录器可用）
        usage = result.get('usage', {})
        try:
            from tests.llm_call_logger import logger
            logger.log_call(
                platform='deepseek',
                messages=messages,
                response=content,
                model=self.config.DEEPSEEK_MODEL,
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
                model=self.config.DEEPSEEK_MODEL,
                usage=usage,
                operation=operation,
                context=context or {}
            )
        except ImportError:
            pass
        
        return content
    
    def _call_aizex_api(self, messages: List[Dict], temperature: float = 0.7,
                        operation: str = "chat", context: Dict = None,
                        max_retries: int = 3) -> str:
        """调用AIZEX API（带重试机制）"""
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
            "temperature": temperature
        }
        
        # 重试机制
        last_exception = None
        for attempt in range(max_retries):
            try:
                # 超时时间：第一次30秒，重试时增加到60秒
                timeout = 60 if attempt > 0 else 30
                response = requests.post(url, headers=headers, json=data, timeout=timeout)
                response.raise_for_status()
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # 成功，跳出重试循环
                break
            except requests.exceptions.Timeout as e:
                last_exception = e
                if attempt < max_retries - 1:
                    print(f"API调用超时，正在重试 ({attempt + 1}/{max_retries})...")
                    import time
                    time.sleep(2 * (attempt + 1))  # 指数退避
                else:
                    # 记录失败并检查是否需要用户确认
                    error_msg = f"API调用超时，已重试{max_retries}次: {str(e)}"
                    try:
                        should_continue = api_failure_handler.record_failure(error_msg)
                        if not should_continue:
                            raise Exception("用户选择停止API调用")
                    except APIConfirmationRequired as confirm_ex:
                        raise confirm_ex
                    raise Exception(error_msg)
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < max_retries - 1:
                    print(f"API调用失败，正在重试 ({attempt + 1}/{max_retries}): {str(e)}")
                    import time
                    time.sleep(2 * (attempt + 1))
                else:
                    # 记录失败并检查是否需要用户确认
                    error_msg = f"API调用失败，已重试{max_retries}次: {str(e)}"
                    try:
                        should_continue = api_failure_handler.record_failure(error_msg)
                        if not should_continue:
                            raise Exception("用户选择停止API调用")
                    except APIConfirmationRequired as confirm_ex:
                        raise confirm_ex
                    raise Exception(error_msg)
            except APIConfirmationRequired:
                # 重新抛出确认异常
                raise
            except Exception as e:
                # 其他错误直接抛出
                raise
        
        if last_exception and 'content' not in locals():
            error_msg = f"API调用失败: {str(last_exception)}"
            try:
                should_continue = api_failure_handler.record_failure(error_msg)
                if not should_continue:
                    raise Exception("用户选择停止API调用")
            except APIConfirmationRequired as confirm_ex:
                raise confirm_ex
            raise Exception(error_msg)
        
        # API调用成功，重置失败计数
        api_failure_handler.record_success()
        
        # 记录LLM调用（如果记录器可用）
        usage = result.get('usage', {})
        try:
            from tests.llm_call_logger import logger
            if logger:
                logger.log_call(
                    platform='aizex',
                    messages=messages,
                    response=content,
                    model=self.config.AIZEX_MODEL,
                    temperature=temperature,
                    usage=usage
                )
        except (ImportError, AttributeError):
            pass  # 记录器不可用时忽略
        
        # 记录token消耗
        try:
            from services.token_tracker import token_tracker
            token_tracker.record_call(
                platform='aizex',
                model=self.config.AIZEX_MODEL,
                usage=usage,
                operation=operation,
                context=context or {}
            )
        except ImportError:
            pass
        
        return content
    
    def _call_openai_api(self, messages: List[Dict], temperature: float = 0.7,
                        operation: str = "chat", context: Dict = None,
                        max_retries: int = 3) -> str:
        """调用OpenAI API（带重试机制）"""
        url = f"{self.config.OPENAI_API_BASE}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.config.OPENAI_MODEL,
            "messages": messages,
            "temperature": temperature
        }
        
        # 重试机制
        last_exception = None
        for attempt in range(max_retries):
            try:
                # 超时时间：第一次30秒，重试时增加到60秒
                timeout = 60 if attempt > 0 else 30
                response = requests.post(url, headers=headers, json=data, timeout=timeout)
                response.raise_for_status()
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # 成功，跳出重试循环
                break
            except requests.exceptions.Timeout as e:
                last_exception = e
                if attempt < max_retries - 1:
                    print(f"API调用超时，正在重试 ({attempt + 1}/{max_retries})...")
                    import time
                    time.sleep(2 * (attempt + 1))  # 指数退避
                else:
                    # 记录失败并检查是否需要用户确认
                    error_msg = f"API调用超时，已重试{max_retries}次: {str(e)}"
                    try:
                        should_continue = api_failure_handler.record_failure(error_msg)
                        if not should_continue:
                            raise Exception("用户选择停止API调用")
                    except APIConfirmationRequired as confirm_ex:
                        raise confirm_ex
                    raise Exception(error_msg)
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < max_retries - 1:
                    print(f"API调用失败，正在重试 ({attempt + 1}/{max_retries}): {str(e)}")
                    import time
                    time.sleep(2 * (attempt + 1))
                else:
                    # 记录失败并检查是否需要用户确认
                    error_msg = f"API调用失败，已重试{max_retries}次: {str(e)}"
                    try:
                        should_continue = api_failure_handler.record_failure(error_msg)
                        if not should_continue:
                            raise Exception("用户选择停止API调用")
                    except APIConfirmationRequired as confirm_ex:
                        raise confirm_ex
                    raise Exception(error_msg)
            except APIConfirmationRequired:
                # 重新抛出确认异常
                raise
            except Exception as e:
                # 其他错误直接抛出
                raise
        
        if last_exception and 'content' not in locals():
            error_msg = f"API调用失败: {str(last_exception)}"
            try:
                should_continue = api_failure_handler.record_failure(error_msg)
                if not should_continue:
                    raise Exception("用户选择停止API调用")
            except APIConfirmationRequired as confirm_ex:
                raise confirm_ex
            raise Exception(error_msg)
        
        # API调用成功，重置失败计数
        api_failure_handler.record_success()
        
        # 记录LLM调用（如果记录器可用）
        usage = result.get('usage', {})
        try:
            from tests.llm_call_logger import logger
            logger.log_call(
                platform='openai',
                messages=messages,
                response=content,
                model=self.config.OPENAI_MODEL,
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
                model=self.config.OPENAI_MODEL,
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
        system_prompt = f"""# Role: 角色扮演助手 (Role-Play Assistant)

生成角色对话回复。

---

### 1. 角色信息 (Character Information)

**【人物卡】**
- 描述: {character_description}
- 属性: {json.dumps(character_attributes, ensure_ascii=False)}
**【属性说明】**
{attr_guide}
{'\n**【场景】**\n' + scene_content if scene_content else ''}

---

### 2. 回复要求 (Response Requirements)

1. **角色一致性**: 严格遵循角色性格、背景和说话风格
2. **情境理解**: 结合场景理解情境（时间/地点/目标/事件）
3. **表/里区分**: surface=玩家可见，hidden=隐藏推演
4. **自然表达**: 自然体现内在想法，不暴露里信息
5. **简洁性**: 回复1-3句，简洁自然

---

### 3. 输出格式 (Output Format)

直接输出回复文本（自然语言，不需要JSON格式）。
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
        elif platform.lower() == 'aizex':
            return self._call_aizex_api(messages, operation='chat',
                                       context={'theme': theme, 'save_step': save_step})
        else:
            raise ValueError(f"不支持的API平台: {platform}")

