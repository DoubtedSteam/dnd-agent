"""
环境分析器：使用LLM分析智能体响应，提取环境变化
包含轻量级剧情控制器功能：评估剧情节奏，主动触发事件
"""
import json
import re
import logging
from typing import Dict, List, Optional
from services.chat_service import ChatService
from config import Config

# 配置日志（输出到服务器端）
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class EnvironmentAnalyzer:
    """环境分析器（包含剧情控制功能）"""
    
    def __init__(self, config: Config):
        self.config = config
        self.chat_service = ChatService()
    
    def _extract_preset_events(self, scene_content: str) -> List[str]:
        """从场景内容中提取预设事件"""
        events = []
        
        # 查找"剧本预设事件"或"重大事件"部分
        preset_pattern = r'##\s*剧本预设事件.*?##'
        major_events_pattern = r'##\s*重大事件.*?##'
        
        # 尝试匹配预设事件部分
        preset_match = re.search(preset_pattern, scene_content, re.DOTALL | re.IGNORECASE)
        if preset_match:
            preset_section = preset_match.group(0)
            # 提取所有列表项
            for line in preset_section.split('\n'):
                if re.match(r'^\s*\d+\.', line) or re.match(r'^\s*[-*]', line):
                    event = re.sub(r'^\s*\d+\.\s*', '', line)
                    event = re.sub(r'^\s*[-*]\s*', '', event)
                    event = re.sub(r'\*\*.*?\*\*', '', event)  # 移除粗体标记
                    if event.strip():
                        events.append(event.strip())
        
        # 如果没有预设事件，尝试从重大事件中提取
        if not events:
            major_match = re.search(major_events_pattern, scene_content, re.DOTALL | re.IGNORECASE)
            if major_match:
                major_section = major_match.group(0)
                for line in major_section.split('\n'):
                    if re.match(r'^\s*[-*]', line):
                        event = re.sub(r'^\s*[-*]\s*', '', line)
                        if event.strip() and '暂无' not in event:
                            events.append(event.strip())
        
        return events
    
    def _extract_occurred_events(self, scene_content: str) -> List[str]:
        """从场景内容中提取已发生的事件"""
        events = []
        
        # 查找"重大事件"部分中已发生的事件
        major_events_pattern = r'##\s*重大事件.*?##'
        major_match = re.search(major_events_pattern, scene_content, re.DOTALL | re.IGNORECASE)
        
        if major_match:
            major_section = major_match.group(0)
            for line in major_section.split('\n'):
                if re.match(r'^\s*[-*]', line):
                    event = re.sub(r'^\s*[-*]\s*', '', line)
                    if event.strip() and '暂无' not in event and '初始场景' not in event:
                        # 移除角色名前缀（如果有）
                        event = re.sub(r'^[^：:]+[：:]\s*', '', event)
                        events.append(event.strip())
        
        return events
    
    def _assess_pacing_before_action(self, scene_content: str, instruction: str) -> Dict:
        """
        在执行动作前评估剧情节奏，用于生成预期事件
        
        Args:
            scene_content: 场景内容
            instruction: 玩家指令
        
        Returns:
            剧情节奏评估结果
        """
        # 从场景中提取已发生的事件
        occurred_events = self._extract_occurred_events(scene_content)
        
        # 提取预设事件
        preset_events = self._extract_preset_events(scene_content)
        
        # 判断是否需要触发事件
        should_trigger = False
        trigger_reason = ""
        
        # 规则1：如果连续多个step没有事件，应该触发
        if len(occurred_events) == 0:
            should_trigger = True
            trigger_reason = "剧情刚开始，必须立即触发事件推动情节"
        elif len(occurred_events) < 3:
            should_trigger = True
            trigger_reason = "剧情推进较慢，必须生成事件推动情节发展"
        
        # 规则2：如果指令是移动类，应该触发事件
        if instruction and isinstance(instruction, str):
            if any(keyword in instruction.lower() for keyword in ['前进', '移动', '探索', '前往', '出发', '离开', '继续', '推进', '行进', '去', '到']):
                should_trigger = True
                trigger_reason = "队伍在移动中，应该遇到一些事件或线索"
        
        # 规则3：如果有预设事件且符合条件，应该触发
        if preset_events and len(occurred_events) < len(preset_events):
            should_trigger = True
            trigger_reason = f"场景中有{len(preset_events)}个预设事件，当前只发生了{len(occurred_events)}个，必须触发下一个预设事件"
        
        return {
            'should_trigger': should_trigger,
            'trigger_reason': trigger_reason,
            'preset_events': preset_events,
            'occurred_events': occurred_events,
            'pacing_score': 'slow' if should_trigger else 'normal'
        }
    
    def _assess_pacing(self, scene_content: str, agent_responses: List[Dict], 
                      previous_events: List[str] = None) -> Dict:
        """评估剧情节奏，判断是否需要触发事件"""
        previous_events = previous_events or []
        
        # 从场景中提取已发生的事件
        occurred_events = self._extract_occurred_events(scene_content)
        all_previous_events = previous_events + occurred_events
        
        # 提取预设事件
        preset_events = self._extract_preset_events(scene_content)
        
        # 分析当前状态
        responses_text = "\n\n".join([
            f"【{resp.get('character_name', '未知')}】\n{resp.get('response', '')}"
            for resp in agent_responses
            if resp and isinstance(resp, dict)
        ])
        
        # 确保responses_text不为None
        responses_text = responses_text or ""
        
        # 判断是否需要触发事件
        should_trigger = False
        trigger_reason = ""
        
        # 规则1：如果连续多个step没有事件，应该触发（更严格）
        if len(all_previous_events) == 0:
            should_trigger = True
            trigger_reason = "剧情刚开始，必须立即触发事件推动情节"
        elif len(all_previous_events) < 3:  # 降低阈值，更容易触发
            should_trigger = True
            trigger_reason = "剧情推进较慢，必须生成事件推动情节发展"
        
        # 规则2：如果角色在移动/探索，且没有遇到任何异常，必须触发（更严格）
        if responses_text and any(keyword in responses_text.lower() for keyword in ['前进', '移动', '探索', '前往', '出发', '离开', '继续', '推进', '行进']):
            if not any(keyword in responses_text.lower() for keyword in ['发现', '遭遇', '异常', '可疑', '听到', '看到', '注意到', '察觉', '痕迹', '线索', '声音', '动静']):
                should_trigger = True
                trigger_reason = "队伍在移动中但未遇到任何事件，必须立即生成事件（如发现痕迹、听到声音、环境变化等）"
        
        # 规则3：如果有预设事件且符合条件，应该触发
        if preset_events and len(all_previous_events) < len(preset_events):
            should_trigger = True
            trigger_reason = f"场景中有{len(preset_events)}个预设事件，当前只发生了{len(all_previous_events)}个，必须触发下一个预设事件"
        
        # 规则4：如果已经移动了2步以上，必须触发事件（新增）
        # 通过检查场景内容中的重大事件数量来判断
        if len(all_previous_events) >= 1 and len(all_previous_events) < 3:
            # 如果已经有事件但还不够，继续触发
            if any(keyword in responses_text.lower() for keyword in ['前进', '移动', '探索', '前往', '出发', '离开', '继续', '推进']):
                should_trigger = True
                trigger_reason = "队伍已移动多步，必须生成新事件保持剧情节奏"
        
        return {
            'should_trigger': should_trigger,
            'trigger_reason': trigger_reason,
            'preset_events': preset_events,
            'occurred_events': occurred_events,
            'pacing_score': 'slow' if should_trigger else 'normal'
        }
    
    def analyze_environment_changes(self, scene_content: str, agent_responses: List[Dict], 
                                   platform: str = None) -> Dict:
        """
        分析智能体响应，提取环境变化
        
        Args:
            scene_content: 当前场景内容
            agent_responses: 所有智能体的响应列表
            platform: API平台
        
        Returns:
            包含环境变化的字典
        """
        if not agent_responses:
            return {
                'scene_changes': {
                    'surface': {},
                    'hidden': {}
                },
                'major_events': [],
                'decision_points': {'has_decision': False, 'description': '', 'options': []},
                'status_summary': {'current_location': '', 'current_time': '', 'goal_progress': '', 'next_suggestions': []}
            }
        
        # 收集所有响应文本
        responses_text = "\n\n".join([
            f"【{resp.get('character_name', '未知')}】\n{resp.get('response', '')}"
            for resp in agent_responses
            if resp and isinstance(resp, dict)
        ])
        
        # 评估剧情节奏
        pacing_assessment = self._assess_pacing(scene_content, agent_responses)
        
        # 详细日志输出到服务器端（不省略内容）
        logger.info(f"\n{'='*80}")
        logger.info(f"🎬 剧情控制器评估")
        logger.info(f"{'='*80}")
        logger.info(f"已发生事件数: {len(pacing_assessment.get('occurred_events', []))}")
        if pacing_assessment.get('occurred_events'):
            logger.info(f"已发生事件: {', '.join(pacing_assessment['occurred_events'][:3])}")
        logger.info(f"预设事件数: {len(pacing_assessment.get('preset_events', []))}")
        if pacing_assessment.get('preset_events'):
            logger.info(f"预设事件: {', '.join(pacing_assessment['preset_events'][:3])}")
        logger.info(f"是否需要触发事件: {pacing_assessment.get('should_trigger', False)}")
        logger.info(f"触发原因: {pacing_assessment.get('trigger_reason', '无')}")
        logger.info(f"节奏评分: {pacing_assessment.get('pacing_score', 'unknown')}")
        logger.info(f"{'='*80}\n")
        
        preset_events_text = ""
        if pacing_assessment.get('preset_events'):
            preset_events_text = f"\n【预设事件】场景中包含以下预设事件，请根据当前情况判断是否应该触发：\n" + "\n".join([f"- {e}" for e in pacing_assessment['preset_events'][:10]])  # 增加到10个
        
        pacing_note = ""
        if pacing_assessment.get('should_trigger'):
            pacing_note = f"\n【⚠️ 强制要求 - 剧情节奏评估】{pacing_assessment['trigger_reason']}。\n**你必须生成至少1个重大事件，重大事件列表不能为空。**\n如果队伍在移动中，必须生成具体的事件描述（如发现痕迹、听到声音、环境变化等），不能返回空列表。"
        
        # 使用完整内容，不截断
        scene_preview = scene_content
        responses_preview = responses_text
        
        system_prompt = f"""环境分析：提取场景变化、重大事件、决策点和状态总结

【场景】{scene_preview}{'...' if len(scene_content) > 1500 else ''}
【响应】{responses_preview}{'...' if len(responses_text) > 1500 else ''}{preset_events_text}{pacing_note}

提取内容：
1. 场景变化（表/里）：
   - surface: time, location{{region/specific_location/coordinates/environment}}, current_narrative, goal, resources
   - hidden: final_goal, potential_enemies, risk_hints
   
2. 重大事件列表：
   - {pacing_note.split('。')[0] if pacing_note else '根据当前行动和场景背景主动识别事件'}
   - 如果场景中有预设事件，在适当时候应该触发（优先考虑预设事件）
   - 事件示例：发现可疑痕迹、听到异常声音、环境变化、发现物品、遭遇敌人、发现线索、地形变化、天气变化、到达新地点等
   - 事件应该具体、有画面感（如"发现地面有可疑的爪印"、"听到远处传来奇怪的声响"等）
   
3. 决策点检测：
   - 判断是否需要玩家做出决策（如路线选择、行动方式、是否调查等）
   - 如果发现线索、异常、需要选择的情况，必须标记为决策点
   - 如果有决策点，提供决策描述和选项
   
4. 状态总结：
   - 当前位置和时间（即使没有变化也要显示当前状态）
   - 目标进度
   - 下一步建议（2-3个可选行动，要具体可操作）

关键规则：
- **位置更新（最高优先级，必须与事件地点一致）**：
  * **核心原则**：位置必须反映角色当前实际所在的地点，必须与事件发生地点一致
  * 如果响应提到"抵达X地"、"到达X地"、"来到X地"、"进入X地"、"移动到X地"等，无论是否触发事件，location.specific_location必须更新为X地
  * 如果响应提到"推进至X地并遇到Y事件"、"在X地附近遭遇Y"、"到达X地外围时发现Y"等，位置必须更新为X地（事件发生的地点）
  * **事件与位置的关系**：
    - 如果事件发生在移动过程中（如"推进至遗迹入口外围，雾中遭遇不明魔物"），位置必须更新到事件发生的地点（"遗迹入口外围"）
    - 如果事件发生在起始位置（如"在公会大厅发现异常"），位置保持起始位置
    - **禁止**：事件发生在X地，但位置显示为Y地（X≠Y）
  * **位置信息必须与响应描述完全一致**：
    - 如果响应说"抵达遗迹入口"，location.specific_location必须是"遗迹入口"
    - 如果响应说"推进至遗迹入口外围"，location.specific_location应该是"遗迹入口外围"或"遗迹入口"
    - 如果响应说"从公会出发，到达遗迹入口"，location.specific_location必须是"遗迹入口"（不是"公会大厅"）
  * **禁止**：响应描述移动但位置不更新；位置更新但响应不描述移动；事件发生在A地但位置显示B地
- **事件触发**：如果剧情节奏评估显示需要触发事件，必须生成至少1个事件；如果队伍在移动中，必须生成具体事件，不能总是"无异常"；禁止返回空的事件列表
- **其他**：时间明显流逝需更新time；如果发现线索/异常/需要选择，必须标记为决策点

输出JSON（重要：位置必须与事件发生地点一致）：
{{
    "scene_changes": {{"surface": {{"time": "", "location": {{"region": "", "specific_location": "", "coordinates": "", "environment": ""}}, "current_narrative": "", "goal": "", "resources": ""}}, "hidden": {{"final_goal": "", "potential_enemies": "", "risk_hints": ""}}}},
    "major_events": [],
    "decision_points": {{"has_decision": false, "description": "", "options": []}},
    "status_summary": {{"current_location": "", "current_time": "", "goal_progress": "", "next_suggestions": []}}
}}

**位置更新检查清单**（必须全部满足）：
1. 如果响应提到"抵达/到达/来到/进入/移动到"某个地点，location.specific_location必须更新为该地点
2. 如果事件发生在移动过程中（如"推进至X地并遇到Y"），location.specific_location必须是X地（事件发生地点）
3. location.specific_location必须与响应中描述的实际位置完全一致
4. 禁止：事件发生在A地，但location.specific_location是B地（A≠B）
5. 禁止：响应说"抵达遗迹入口"，但location.specific_location是"公会大厅"（这是严重错误）"""
        
        user_message = "分析响应，提取变化和事件。"
        
        platform = platform or self.config.DEFAULT_API_PLATFORM
        
        # 调用LLM分析
        try:
            if platform.lower() == 'deepseek':
                response_text = self.chat_service._call_deepseek_api(
                    [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_message}],
                    operation='environment_analysis'
                )
            elif platform.lower() == 'openai':
                response_text = self.chat_service._call_openai_api(
                    [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_message}],
                    operation='environment_analysis'
                )
            elif platform.lower() == 'aizex':
                response_text = self.chat_service._call_aizex_api(
                    [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_message}],
                    operation='environment_analysis'
                )
            else:
                raise ValueError(f"不支持的API平台: {platform}")
        except Exception as e:
            # API调用失败，返回空变化
            logger.error(f"\n❌ 环境分析API调用失败: {e}")
            logger.error(f"   场景内容长度: {len(scene_content)}")
            logger.error(f"   响应文本长度: {len(responses_text)}")
            return {
                'scene_changes': {
                    'surface': {},
                    'hidden': {}
                },
                'major_events': [],
                'decision_points': {'has_decision': False, 'description': '', 'options': []},
                'status_summary': {'current_location': '', 'current_time': '', 'goal_progress': '', 'next_suggestions': []}
            }
        
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
            
            # 详细日志输出分析结果到服务器端
            major_events = result.get('major_events', [])
            decision_points = result.get('decision_points', {})
            logger.info(f"\n📊 环境分析结果:")
            logger.info(f"   重大事件数: {len(major_events)}")
            if major_events:
                for i, event in enumerate(major_events, 1):
                    logger.info(f"   {i}. {event[:100]}{'...' if len(event) > 100 else ''}")
            logger.info(f"   是否有决策点: {decision_points.get('has_decision', False)}")
            if decision_points.get('has_decision'):
                logger.info(f"   决策描述: {decision_points.get('description', '')[:100]}")
            logger.info("")
            
            return {
                'scene_changes': result.get('scene_changes', {'surface': {}, 'hidden': {}}),
                'major_events': major_events,
                'decision_points': decision_points,
                'status_summary': result.get('status_summary', {'current_location': '', 'current_time': '', 'goal_progress': '', 'next_suggestions': []})
            }
        except json.JSONDecodeError:
            # 如果解析失败，返回空变化
            return {
                'scene_changes': {
                    'surface': {},
                    'hidden': {}
                },
                'major_events': [],
                'decision_points': {'has_decision': False, 'description': '', 'options': []},
                'status_summary': {'current_location': '', 'current_time': '', 'goal_progress': '', 'next_suggestions': []}
            }
        except Exception as e:
            logger.error(f"环境分析失败: {e}")
            return {
                'scene_changes': {
                    'surface': {},
                    'hidden': {}
                },
                'major_events': [],
                'decision_points': {'has_decision': False, 'description': '', 'options': []},
                'status_summary': {'current_location': '', 'current_time': '', 'goal_progress': '', 'next_suggestions': []}
            }

