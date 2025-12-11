"""
多智能体协调器：协调所有智能体的工作流程
"""
import time
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from services.agent import Agent
from services.environment_manager import EnvironmentManager
from services.response_aggregator import ResponseAggregator
from services.response_formatter import ResponseFormatter
from services.state_updater import StateUpdater
from services.save_manager import SaveManager
from services.character_store import CharacterStore
from services.conversation_history import ConversationHistory
from config import Config


class MultiAgentCoordinator:
    """多智能体协调器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.character_store = CharacterStore(config)
        self.environment_manager = EnvironmentManager(config)
        self.response_aggregator = ResponseAggregator(config)
        self.response_formatter = ResponseFormatter(config)
        self.state_updater = StateUpdater(config)
        self.save_manager = SaveManager(config)
        self.conversation_history = ConversationHistory(config)
    
    def _extract_player_role(self, scene_content: str) -> Optional[str]:
        """从场景内容中提取玩家角色"""
        if not scene_content:
            return None
        
        lines = scene_content.split('\n')
        for line in lines:
            if "玩家角色" in line or "玩家扮演" in line:
                # 提取玩家角色信息
                if '：' in line:
                    role = line.split('：')[-1].strip()
                    # 移除可能的描述部分
                    if '，' in role:
                        role = role.split('，')[0].strip()
                    return role
                elif ':' in line:
                    role = line.split(':')[-1].strip()
                    if ',' in role:
                        role = role.split(',')[0].strip()
                    return role
        return None
    
    def process_instruction(self, instruction: str, theme: str, 
                           save_step: Optional[str] = None,
                           character_ids: Optional[List[str]] = None,
                           platform: str = None, player_role: str = None) -> Dict:
        """
        处理玩家指令，协调所有智能体
        
        流程：
        1. 加载场景
        2. 加载所有角色（或指定角色）
        3. 并行发送指令给所有智能体
        4. 收集所有响应
        5. 聚合响应，分析变化
        6. 更新状态
        
        Args:
            instruction: 玩家指令
            theme: 主题
            save_step: 存档步骤
            character_ids: 指定的角色ID列表（如果为None，则使用所有角色）
            platform: API平台
        
        Returns:
            处理结果，包含表/里信息和步骤耗时
        """
        # 记录总开始时间
        total_start_time = time.time()
        step_timings = {}
        
        # 1. 加载场景
        step_start = time.time()
        scene_content = self.environment_manager.load_scene(theme, save_step)
        if not scene_content:
            return {'error': '无法加载场景'}
        
        # 1.1 加载对话历史
        history_list = self.conversation_history.load_recent_history(theme, save_step or "0_step", limit=5)
        conversation_history_text = self.conversation_history.get_history_text(history_list)
        
        # 提取玩家角色（如果未提供）
        if not player_role:
            player_role = self._extract_player_role(scene_content)
        
        # 2. 加载所有角色
        step_timings['load'] = time.time() - step_start
        
        step_start = time.time()
        if character_ids is None:
            # 获取主题下的所有角色
            all_characters = self.character_store.list_characters()
            characters = [c for c in all_characters if c.get('theme') == theme]
        else:
            characters = []
            for char_id in character_ids:
                char = self.character_store.get_character(char_id)
                if char:
                    characters.append(char)
        
        if not characters:
            return {'error': '没有找到角色'}
        
        # 3. 创建智能体并并行处理
        agents = [Agent(char, self.config) for char in characters]
        agent_responses = []
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=len(agents)) as executor:
            futures = {
                executor.submit(
                    agent.process_instruction,
                    instruction,
                    scene_content,
                    platform,
                    save_step,
                    player_role,
                    conversation_history_text
                ): agent for agent in agents
            }
            
            for future in as_completed(futures):
                try:
                    response = future.result()
                    agent_responses.append(response)
                except Exception as e:
                    agent = futures[future]
                    agent_responses.append({
                        'character_id': agent.character_id,
                        'character_name': agent.character_name,
                        'response': f'处理失败: {str(e)}',
                        'state_changes': {},
                        'attribute_changes': {}
                    })
        
        step_timings['agents'] = time.time() - step_start
        
        # 4. 聚合响应（原始JSON格式）
        step_start = time.time()
        aggregated = self.response_aggregator.aggregate_responses(
            agent_responses,
            scene_content
        )
        step_timings['aggregate'] = time.time() - step_start
        
        # 5. 分析环境变化（使用LLM分析所有响应）
        step_start = time.time()
        environment_changes = self.environment_manager.apply_responses_to_environment(
            scene_content,
            agent_responses,
            platform
        )
        step_timings['analyze'] = time.time() - step_start
        
        # 6. 更新状态（如果提供了save_step）
        step_start = time.time()
        new_step = save_step
        if save_step:
            # 6.1 创建新的存档步骤
            new_step = self.save_manager.create_new_step(theme, save_step)
            if not new_step:
                new_step = save_step  # 如果创建失败，使用原步骤
            
            # 6.2 更新角色状态（在新步骤中）
            for resp in agent_responses:
                if resp.get('state_changes') or resp.get('attribute_changes'):
                    self.state_updater.update_character_state(
                        theme,
                        new_step,
                        resp['character_id'],
                        resp.get('state_changes', {}),
                        resp.get('attribute_changes', {})
                    )
            
            # 6.3 更新场景状态（在新步骤中）
            major_events = self._extract_major_events(agent_responses)
            # 无论是否有major_events，都要更新场景（因为可能有位置变化等）
            self.state_updater.update_scene_state(
                theme,
                new_step,
                environment_changes.get('scene_changes', {}),
                major_events
            )
            
            # 6.4 加载更新后的场景（用于格式化）
            updated_scene_content = self.environment_manager.load_scene(theme, new_step)
            if updated_scene_content:
                scene_content = updated_scene_content
        
        step_timings['update'] = time.time() - step_start
        
        # 7. 格式化响应（转换为适合玩家角色的文本）- 在更新状态之后
        step_start = time.time()
        formatted = self.response_formatter.format_responses_for_player(
            agent_responses,
            player_role or '玩家',
            scene_content,
            platform
        )
        step_timings['format'] = time.time() - step_start
        
        # 7.1 保存对话历史（如果创建了新步骤）
        if new_step and new_step != save_step:
            summary = formatted['surface'].get('summary', '')
            self.conversation_history.save_conversation(
                theme,
                new_step,
                instruction,
                summary
            )
        
        # 8. 返回结果（表/里分离）
        total_time = time.time() - total_start_time
        step_timings['total'] = total_time
        
        result = {
            'surface': {
                'responses': formatted['surface']['responses'],  # 格式化后的文本响应
                'summary': formatted['surface']['summary']  # 格式化后的摘要
            },
            'hidden': {
                'state_changes': aggregated['hidden']['state_changes'],
                'attribute_changes': aggregated['hidden']['attribute_changes'],
                'environment_changes': environment_changes,
                'raw_responses': formatted['hidden'].get('raw_responses', agent_responses),  # 保留原始响应（包含execution_result）
                'execution_results': [
                    {
                        'character_id': resp.get('character_id'),
                        'character_name': resp.get('character_name'),
                        'execution_result': resp.get('execution_result', {})
                    }
                    for resp in agent_responses
                    if resp.get('execution_result')
                ]
            },
            'new_step': new_step,
            'step_timings': step_timings  # 各步骤的耗时（秒）
        }
        
        return result
        if save_step and new_step != save_step:
            result['new_step'] = new_step
        
        return result
    
    def _extract_major_events(self, agent_responses: List[Dict]) -> List[str]:
        """从响应中提取重大事件"""
        # 这里可以扩展为使用LLM分析响应，提取重大事件
        # 暂时返回空列表
        events = []
        for resp in agent_responses:
            # 简单提取：如果响应包含某些关键词，认为是重大事件
            response_text = resp.get('response', '').lower()
            if any(keyword in response_text for keyword in ['发现', '获得', '击败', '完成', '触发']):
                events.append(f"{resp['character_name']}: {resp['response'][:50]}...")
        return events

