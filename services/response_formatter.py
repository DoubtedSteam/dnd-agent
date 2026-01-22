"""
响应格式化器：将Agent的JSON响应转换为适合玩家角色的文本
"""
import json
import re
from typing import Dict, List, Optional
from services.chat_service import ChatService
from services.agent import format_agent_response
from config import Config


class ResponseFormatter:
    """响应格式化器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.chat_service = ChatService()
    
    def _clean_reasoning_tags(self, text: str) -> str:
        """清理文本中的推理标记"""
        if not text:
            return text
        
        # 移除 <think>...</think> 标记（成对出现）
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        # 移除 <think>...</think> 标记（成对出现）
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        # 移除单独的未闭合标记（如果没有闭合标签，匹配到行尾或文档末尾）
        text = re.sub(r'<(think|redacted_reasoning)>.*?$', '', text, flags=re.DOTALL | re.IGNORECASE | re.MULTILINE)
        # 移除 **Thinking about...** 这样的标记及其后续内容
        text = re.sub(r'\*\*Thinking about.*?\*\*.*?(?=\n\n|\*\*|$)', '', text, flags=re.DOTALL | re.IGNORECASE)
        # 移除 **理解请求** 这样的标记及其后续内容（直到下一个段落或标记）
        text = re.sub(r'\*\*理解请求\*\*.*?(?=\n\n|\*\*|$)', '', text, flags=re.DOTALL | re.IGNORECASE)
        # 移除 **Thinking about the user's request** 这样的标记及其后续内容
        text = re.sub(r'\*\*Thinking about the user\'s request\*\*.*?(?=\n\n|\*\*|$)', '', text, flags=re.DOTALL | re.IGNORECASE)
        # 移除以 **理解请求** 开头的行及其后续内容
        text = re.sub(r'^\*\*理解请求\*\*.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        # 移除包含 "理解请求" 或 "Thinking about" 的整行
        lines = text.split('\n')
        cleaned_lines = []
        skip_next = False
        for line in lines:
            if re.search(r'(理解请求|Thinking about)', line, re.IGNORECASE):
                skip_next = True
                continue
            if skip_next and line.strip() == '':
                skip_next = False
                continue
            if skip_next:
                continue
            cleaned_lines.append(line)
        text = '\n'.join(cleaned_lines)
        
        return text.strip()
    
    def format_responses_for_player(self, agent_responses: List[Dict], player_role: str,
                                   scene_content: str, platform: str = None) -> Dict:
        """
        将智能体响应格式化为适合玩家角色的文本
        
        Args:
            agent_responses: 所有智能体的响应列表（包含JSON格式的response）
            player_role: 玩家扮演的角色
            scene_content: 场景内容
            platform: API平台
        
        Returns:
            格式化后的响应，包含表/里信息
        """
        if not agent_responses:
            return {
                'surface': {
                    'responses': [],
                    'summary': '暂无响应'
                },
                'hidden': {}
            }
        
        # 收集所有响应文本
        responses_text = "\n\n".join([
            f"【{resp.get('character_name', '未知')}】\n{format_agent_response(resp.get('response', ''))}"
            for resp in agent_responses
            if resp and isinstance(resp, dict)
        ])
        
        # 提取每个角色的说话风格信息（从原始响应中）
        character_styles = {}
        for resp in agent_responses:
            if not resp or not isinstance(resp, dict):
                continue
            char_name = resp.get('character_name', '')
            if not char_name:
                continue
            # 尝试从响应中提取角色信息，但主要依赖原始响应中的语气
            character_styles[char_name] = {
                'original_response': format_agent_response(resp.get('response', '')),
                'character_id': resp.get('character_id', '')
            }
        
        system_prompt = f"""# Role: 响应格式化助手 (Response Formatter)

将智能体响应转换为玩家视角的流畅文本。

---

### 1. 输入信息 (Input)

**【玩家角色】**
{player_role}

**【场景】**
{scene_content}

**【角色响应】**
{responses_text}

---

### 2. 格式化要求 (Formatting Requirements)

#### 2.1 角色响应格式化
1. **角色一致性（最高优先级）**: 严格保持每个角色的说话风格和语气
2. **玩家视角**: 自然融入对话和行动，每个角色1-2句
3. **环境描述**: 可适当添加环境描述，增强沉浸感

#### 2.2 摘要生成要求（必须严格遵守）
- **视角**: 第三人称视角，禁止使用"我"、"我们"、"咱们"等第一人称
- **叙事风格**: 
  * ❌ 错误示例: "艾伦做了X，莉娅做了Y"（逐条列举）
  * ✅ 正确示例: "黎明的薄雾尚未散去，冒险者小队整装待发。凯·盗贼率先踏出公会大门..."
  * 将多个角色行动融合成连贯叙事，禁止"角色名：行动内容"格式
- **文学性**: 语言生动优美，有画面感，可描写环境氛围，包含动作细节和心理暗示，叙述流畅自然

---

### 3. 输出格式 (Output Format)

输出JSON格式：
{{
    "formatted_responses": [
        {{
            "character_name": "角色名",
            "formatted_text": "格式化文本（保持角色语气）"
        }}
    ],
    "summary": "摘要（第三人称视角，小说风格，以叙事为主，不要重复人物行动）"
}}
"""
        
        user_message = f"格式化响应为玩家视角文本。"
        
        platform = platform or self.config.DEFAULT_API_PLATFORM
        
        # 调用LLM格式化
        try:
            if platform.lower() == 'deepseek':
                response_text = self.chat_service._call_deepseek_api(
                    [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_message}],
                    operation='response_formatting'
                )
            elif platform.lower() == 'openai':
                response_text = self.chat_service._call_openai_api(
                    [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_message}],
                    operation='response_formatting'
                )
            elif platform.lower() == 'aizex':
                response_text = self.chat_service._call_aizex_api(
                    [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_message}],
                    operation='response_formatting'
                )
            else:
                raise ValueError(f"不支持的API平台: {platform}")
        except Exception as e:
            # API调用失败，使用简单格式化
            print(f"⚠️ 响应格式化API调用失败: {e}")
            print(f"   将使用fallback格式化方法")
            return self._simple_format(agent_responses, scene_content)
        
        # 解析响应
        try:
            # 尝试提取JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            result = json.loads(response_text)
            formatted_responses = result.get('formatted_responses', [])
            summary = result.get('summary', '')
            
            # 清理摘要中的推理标记
            summary = self._clean_reasoning_tags(summary)
            
            # 验证摘要是否符合要求（第三人称、小说风格）
            if summary and not any(word in summary for word in ['我', '我们', '咱们']) and len(summary) > 20:
                return {
                    'surface': {
                        'responses': formatted_responses,
                        'summary': summary
                    },
                    'hidden': {
                        'raw_responses': agent_responses  # 保留原始响应供内部使用
                    }
                }
            else:
                # 摘要不符合要求，使用fallback
                print(f"⚠️ LLM返回的摘要不符合要求，使用fallback方法")
                return self._simple_format(agent_responses, scene_content)
        except json.JSONDecodeError as e:
            # 如果解析失败，使用简单格式化
            print(f"⚠️ JSON解析失败: {e}")
            print(f"   LLM返回内容: {response_text[:200]}...")
            return self._simple_format(agent_responses, scene_content)
        except Exception as e:
            print(f"⚠️ 响应格式化失败: {e}")
            return self._simple_format(agent_responses, scene_content)
    
    def _simple_format(self, agent_responses: List[Dict], scene_content: str = "") -> Dict:
        """简单格式化（fallback）- 尝试生成第三人称、小说风格的摘要"""
        formatted = []
        for resp in agent_responses:
            if not resp or not isinstance(resp, dict):
                continue
            char_name = resp.get('character_name', '未知')
            if not char_name:
                continue
            formatted.append({
                'character_name': char_name,
                'formatted_text': format_agent_response(resp.get('response', ''))
            })
        
        # 尝试使用LLM仅生成摘要（不格式化响应）
        summary = self._generate_summary_only(agent_responses, scene_content)
        
        # 如果LLM调用失败，使用简单格式化
        if not summary:
            summary_parts = []
            for resp in agent_responses:
                if not resp or not isinstance(resp, dict):
                    continue
                char_name = resp.get('character_name', '未知')
                response = format_agent_response(resp.get('response', ''))
                if not response:
                    continue
                
                # 将第一人称转换为第三人称
                response_3rd = response.replace('我', char_name).replace('我们', '他们').replace('咱们', '他们')
                
                # 提取关键动作和描述
                if len(response_3rd) > 30:
                    summary_parts.append(f"{char_name}：{response_3rd[:80]}...")
                else:
                    summary_parts.append(f"{char_name}：{response_3rd}")
            
            # 组合成小说风格的叙述
            if len(summary_parts) > 1:
                summary = "。".join(summary_parts) + "。"
            else:
                summary = summary_parts[0] if summary_parts else "暂无响应"
        
        return {
            'surface': {
                'responses': formatted,
                'summary': summary
            },
            'hidden': {
                'raw_responses': agent_responses
            }
        }
    
    def _generate_summary_only(self, agent_responses: List[Dict], scene_content: str = "") -> str:
        """仅生成摘要（不格式化响应）- 用于fallback时"""
        try:
            # 收集所有响应文本
            responses_text = "\n\n".join([
                f"【{resp.get('character_name', '未知')}】\n{resp.get('response', '')}"
                for resp in agent_responses
                if resp and isinstance(resp, dict)
            ])
            
            system_prompt = f"""# Role: 小说叙述助手 (Narrative Assistant)

生成第三人称、小说风格的摘要。

---

### 1. 输入信息 (Input)

**【场景】**
{scene_content}

**【角色响应】**
{responses_text}

---

### 2. 摘要要求 (Summary Requirements)

- **视角**: 第三人称视角，禁止使用"我"、"我们"、"咱们"等第一人称
- **叙事风格**: 以叙事为主，不要逐条列举角色行动，用流畅叙事描述整体场景
- **文学性**: 语言生动优美，有画面感，可描写环境氛围，包含动作细节
- **流畅度**: 叙述流畅自然，如小说章节般的文学性描述
- **长度**: 100-200字

---

### 3. 输出格式 (Output Format)

直接输出摘要文本（不需要JSON格式）。

直接输出摘要文本，不要使用JSON格式，不要包含任何标记。"""
            
            user_message = "请生成第三人称、小说风格的摘要。"
            
            platform = self.config.DEFAULT_API_PLATFORM
            
            # 调用LLM生成摘要
            if platform.lower() == 'deepseek':
                summary = self.chat_service._call_deepseek_api(
                    [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_message}],
                    operation='summary_generation'
                )
            elif platform.lower() == 'openai':
                summary = self.chat_service._call_openai_api(
                    [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_message}],
                    operation='summary_generation'
                )
            elif platform.lower() == 'aizex':
                summary = self.chat_service._call_aizex_api(
                    [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_message}],
                    operation='summary_generation'
                )
            else:
                return ""
            
            # 清理摘要（移除可能的markdown标记和推理标记）
            summary = summary.strip()
            if summary.startswith("```"):
                # 移除代码块标记
                lines = summary.split('\n')
                summary = '\n'.join([line for line in lines if not line.strip().startswith('```')])
            summary = summary.strip()
            
            # 清理推理标记
            summary = self._clean_reasoning_tags(summary)
            
            # 验证摘要是否符合要求
            if summary and len(summary) > 20 and not any(word in summary for word in ['我', '我们', '咱们']):
                return summary
            else:
                return ""
        except Exception as e:
            # 静默失败，返回空字符串，让调用者使用简单格式化
            return ""

