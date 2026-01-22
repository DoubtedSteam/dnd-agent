"""
多智能体协调器：协调所有智能体的工作流程
"""
import os
import re
import time
import logging
import traceback
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from services.agent import Agent, format_agent_response
from services.environment_manager import EnvironmentManager
from services.response_aggregator import ResponseAggregator
from services.response_formatter import ResponseFormatter
from services.state_updater import StateUpdater
from services.save_manager import SaveManager
from services.character_store import CharacterStore
from services.conversation_history import ConversationHistory
from services.script_manager import ScriptManager
from services.director_evaluator import DirectorEvaluator
from services.scene_state_manager import SceneStateManager
from services.time_manager import TimeManager
from config import Config

logger = logging.getLogger(__name__)


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
        self.script_manager = ScriptManager(config)
        self.director_evaluator = DirectorEvaluator(config)
        self.scene_state_manager = SceneStateManager(config)
        self.time_manager = TimeManager(config)
    
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
        import traceback
        try:
            # 记录总开始时间
            total_start_time = time.time()
            step_timings = {}
            
            # 参数验证
            if not instruction:
                logger.error("❌ instruction 参数为空")
                return {'error': '指令不能为空'}
            if not isinstance(instruction, str):
                logger.error(f"❌ instruction 类型错误: {type(instruction)}, 值: {instruction}")
                return {'error': f'指令类型错误: {type(instruction)}'}
            
            logger.info(f"📝 开始处理指令: {instruction[:50]}...")
            logger.info(f"   主题: {theme}, 步骤: {save_step}, 平台: {platform}")
            
            # 1. 加载场景和获取当前场景/房间ID
            step_start = time.time()
            
            # 获取当前场景ID和房间ID
            current_scene_id = self.scene_state_manager.get_current_scene_id(theme, save_step or "0_step")
            current_room_id = self.scene_state_manager.get_current_room_id(theme, save_step or "0_step")
            
            if not current_scene_id:
                logger.error(f"❌ 无法获取当前场景ID: theme={theme}, save_step={save_step}")
                return {'error': '无法获取当前场景ID，请确保存档已初始化'}
            
            logger.info(f"📍 当前场景: {current_scene_id}, 房间: {current_room_id or '无'}")
            
            # 加载场景内容（基于剧本系统）
            scene_content = self.environment_manager.load_scene(theme, save_step)
            if not scene_content:
                logger.error(f"❌ 无法加载场景: theme={theme}, save_step={save_step}")
                return {'error': '无法加载场景'}
            logger.info(f"✅ 场景加载成功，长度: {len(scene_content)}")
            
            # 1.1 加载对话历史
            history_list = self.conversation_history.load_recent_history(theme, save_step or "0_step", limit=5)
            conversation_history_text = self.conversation_history.get_history_text(history_list)
            logger.info(f"✅ 对话历史加载成功，历史记录数: {len(history_list)}")
            
            # 提取玩家角色（如果未提供）
            if not player_role:
                player_role = self._extract_player_role(scene_content)
                logger.info(f"✅ 玩家角色: {player_role}")
            
            # 2. 加载重要角色（只有重要角色需要创建Agent）
            step_timings['load'] = time.time() - step_start
            
            step_start = time.time()
            if character_ids is None:
                # 获取主题下的所有角色
                all_characters = self.character_store.list_characters()
                characters = [c for c in all_characters if c.get('theme') == theme]
                
                # 如果找到了角色，记录日志
                if characters:
                    logger.info(f"✅ 加载主题下重要角色，找到 {len(characters)} 个角色")
                    for char in characters:
                        logger.info(f"   - {char.get('name')} ({char.get('id')})")
                else:
                    # 检查故事总览中是否定义了重要角色
                    story_overview = self.script_manager.load_story_overview(theme)
                    important_chars = story_overview.get("important_characters", [])
                    if important_chars:
                        logger.error(f"❌ 故事总览中定义了 {len(important_chars)} 个重要角色，但未找到对应的角色文件")
                        logger.error(f"   重要角色列表: {[c.get('name') for c in important_chars]}")
                        logger.error(f"   ⚠️  重要提示：所有重要角色（包括玩家角色）都必须创建角色卡（.json文件）！")
                        logger.error(f"   请为以下角色创建角色卡，存放在 themes/{theme}/characters/ 目录下：")
                        for char in important_chars:
                            logger.error(f"      - {char.get('name')}: {char.get('description', '')}")
                        logger.error(f"   环境NPC不需要角色卡，它们的反应由导演评估处理。")
                        return {
                            'error': '缺少重要角色卡',
                            'message': f'主题 "{theme}" 下缺少重要角色的角色卡文件。',
                            'important_characters': important_chars,
                            'hint': f'请为所有重要角色（包括玩家角色）创建角色卡（.json文件），存放在 themes/{theme}/characters/ 目录下。可以通过API创建，或直接创建JSON文件。'
                        }
                    else:
                        logger.error(f"❌ 主题 {theme} 下没有定义重要角色，这是不正常的。")
                        logger.error(f"   每个剧本都应该至少有一个重要角色（玩家角色）。")
                        logger.error(f"   请在 STORY_OVERVIEW.md 的\"重要角色列表\"部分定义重要角色。")
                        return {
                            'error': '缺少重要角色定义',
                            'message': f'主题 "{theme}" 下没有定义重要角色。',
                            'hint': '请在 STORY_OVERVIEW.md 的"重要角色列表"部分定义重要角色（至少包括玩家角色）。'
                        }
            else:
                characters = []
                for char_id in character_ids:
                    char = self.character_store.get_character(char_id)
                    if char:
                        characters.append(char)
                logger.info(f"✅ 加载指定角色，找到 {len(characters)} 个角色")
            
            # 重要：系统要求必须有重要角色（至少包括玩家角色）
            # 如果没有重要角色，系统会返回错误，不允许继续执行
        
            # 3. 创建智能体并并行处理（只有重要角色才创建Agent）
            # 注意：根据文档，统一停止点功能由导演评估承担，不再需要提前进行剧情节奏评估
            # 注意：环境NPC不需要创建Agent，它们的反应由导演评估在环境变化分析中处理
            
            agent_responses = []
            
            if characters:
                logger.info(f"🤖 创建 {len(characters)} 个重要角色的智能体...")
                agents = [Agent(char, self.config) for char in characters]
                
                # 使用线程池并行处理
                logger.info("🚀 开始并行调用智能体...")
                with ThreadPoolExecutor(max_workers=len(agents)) as executor:
                    futures = {
                        executor.submit(
                            agent.process_instruction,
                            instruction,
                            scene_content,
                            platform,
                            save_step,
                            player_role,
                            conversation_history_text,
                            None  # 不再传递预期事件，统一停止点由导演评估决定
                        ): agent for agent in agents
                    }
                    
                    for future in as_completed(futures):
                        try:
                            response = future.result()
                            if response:
                                agent_responses.append(response)
                                logger.info(f"✅ 收到响应: {response.get('character_name', '未知')}")
                            else:
                                agent = futures[future]
                                logger.warning(f"⚠️ 收到空响应: {agent.character_name}")
                                agent_responses.append({
                                    'character_id': agent.character_id,
                                    'character_name': agent.character_name,
                                    'response': {
                                        'dialogue': '响应为空',
                                        'action_intent': ''
                                    },
                                    'hidden': {
                                        'inner_monologue': ''
                                    }
                                })
                        except Exception as e:
                            agent = futures[future]
                            logger.error(f"❌ 智能体处理失败: {agent.character_name}, 错误: {e}")
                            logger.error(traceback.format_exc())
                            agent_responses.append({
                                'character_id': agent.character_id,
                                'character_name': agent.character_name,
                                'response': {
                                    'dialogue': f'处理失败: {str(e)}',
                                    'action_intent': ''
                                },
                                'hidden': {
                                    'inner_monologue': f'处理失败: {str(e)}'
                                }
                            })
                
                logger.info(f"✅ 收到 {len(agent_responses)} 个重要角色的响应")
            else:
                logger.info("ℹ️  没有重要角色，跳过Agent响应生成。环境NPC的反应将由导演评估在环境变化分析中处理。")
            
            step_timings['agents'] = time.time() - step_start
        
            # 5. 聚合响应（原始JSON格式）
            step_start = time.time()
            try:
                logger.info("📊 开始聚合响应...")
                logger.info(f"   agent_responses 类型: {type(agent_responses)}, 长度: {len(agent_responses) if agent_responses else 0}")
                if agent_responses:
                    logger.info(f"   第一个响应类型: {type(agent_responses[0])}, 内容: {str(agent_responses[0])[:100] if agent_responses[0] else 'None'}")
                aggregated = self.response_aggregator.aggregate_responses(
                    agent_responses,
                    scene_content
                )
                logger.info("✅ 响应聚合完成")
                step_timings['aggregate'] = time.time() - step_start
            except Exception as e:
                logger.error(f"❌ 响应聚合失败: {e}")
                logger.error(f"   agent_responses: {agent_responses}")
                logger.error(traceback.format_exc())
                step_timings['aggregate'] = time.time() - step_start
                raise
        
            # 6. 导演评估阶段（LLM调用2，一个LLM调用包含两部分工作）
            step_start = time.time()
            logger.info("🎬 开始导演评估（包含环境变化分析和决策制定两部分）...")
            director_result = self._evaluate_as_director(
                theme, current_scene_id, current_room_id, instruction, save_step, agent_responses, scene_content, platform
            )
            
            # 从返回结果中提取两部分内容
            environment_analysis = director_result.get("environment_analysis", {})
            director_decision = director_result.get("director_decision", {})
            
            logger.info(f"✅ 导演评估完成（环境变化分析+决策制定）")
            logger.info(f"   环境变化: 场景描述已更新, Agent执行结果数={len(environment_analysis.get('agent_execution_results', []))}")
            appear_monster = director_decision.get('appear_monster', [])
            appear_monster_str = ', '.join(appear_monster) if isinstance(appear_monster, list) and appear_monster else (appear_monster if appear_monster else '无')
            logger.info(f"   决策结果: 事件={director_decision.get('trigger_event')}, "
                       f"怪物={appear_monster_str}, "
                       f"转换={director_decision.get('transition_target')}")
            
            # 从环境变化分析中提取环境变化信息（用于后续状态更新）
            updated_scene_description = environment_analysis.get("updated_scene_description", "")
            scene_state_changes = environment_analysis.get("scene_state_changes", {})
            agent_execution_results = environment_analysis.get("agent_execution_results", [])
            
            # 合并事件描述和怪物描述到场景描述中（如果有事件或怪物出现）
            event_description = director_decision.get("event_description", "")
            appear_monster = director_decision.get("appear_monster", [])
            monster_description = director_decision.get("monster_description", "")
            
            # 构建需要追加的描述内容
            additional_descriptions = []
            if director_decision.get("trigger_event") and event_description:
                additional_descriptions.append(event_description)
            if appear_monster and monster_description:
                additional_descriptions.append(monster_description)
            
            # 将所有描述合并到场景描述中
            if additional_descriptions:
                combined_description = "\n\n".join(additional_descriptions)
                if updated_scene_description:
                    updated_scene_description = f"{updated_scene_description}\n\n{combined_description}"
                else:
                    updated_scene_description = combined_description
            
            # 构建environment_changes格式（兼容旧代码）
            # 处理location可能是字符串或字典的情况
            location_data = scene_state_changes.get("location", {})
            if isinstance(location_data, str):
                # 如果是字符串，转换为字典格式
                location_data = {'specific_location': location_data}
            elif not isinstance(location_data, dict):
                location_data = {}
            
            environment_changes = {
                "scene_changes": {
                    "surface": {
                        "location": location_data,
                        "time": scene_state_changes.get("time", ""),
                        "current_narrative": updated_scene_description if updated_scene_description else ""
                    },
                    "hidden": {}
                },
                "agent_execution_results": agent_execution_results
            }
            
            # 处理导演决策
            elapsed_time = director_decision.get("elapsed_time", 1.0)
            logger.info(f"⏱️ 消耗时间: {elapsed_time}分钟（游戏内时间）")
            
            # 更新游戏时间
            elapsed_seconds = elapsed_time * 60  # 转换为秒（1分钟游戏时间 = 60秒）
            self.time_manager.update_game_time(theme, save_step or "0_step", elapsed_seconds)
            
            if director_decision.get("trigger_event"):
                event_id = director_decision.get("trigger_event")
                logger.info(f"🎭 触发事件: {event_id} - {director_decision.get('event_description', '')[:50]}")
                
                # 记录已触发的事件
                if event_id:
                    self.scene_state_manager.add_triggered_event(theme, save_step or "0_step", event_id)
            
            appear_monster = director_decision.get("appear_monster", [])
            if appear_monster and (isinstance(appear_monster, list) and len(appear_monster) > 0 or (isinstance(appear_monster, str) and appear_monster)):
                monster_desc = director_decision.get('monster_description', '')
                if isinstance(appear_monster, list):
                    monster_list = ', '.join(appear_monster)
                    logger.info(f"👹 怪物出现 ({len(appear_monster)}只): {monster_list} - {monster_desc[:50]}")
                else:
                    logger.info(f"👹 怪物出现: {appear_monster} - {monster_desc[:50]}")
            
            # 处理场景/房间转换
            if director_decision.get("transition_target"):
                target_id = director_decision["transition_target"]
                transition_type = director_decision.get("transition_type", "scene")
                logger.info(f"🔄 场景转换: {current_scene_id} -> {target_id} ({transition_type})")
                
                # 执行场景转换
                if transition_type == "room":
                    # 转换到房间，需要确定房间所属的场景
                    parent_scene = self.script_manager.get_parent_scene(theme, target_id)
                    if parent_scene:
                        self.scene_state_manager.transition_scene(theme, save_step, parent_scene, target_id)
                        current_scene_id = parent_scene
                        current_room_id = target_id
                else:
                    # 转换到场景
                    self.scene_state_manager.transition_scene(theme, save_step, target_id, None)
                    current_scene_id = target_id
                    current_room_id = None
                
                # 重新加载场景内容
                scene_content = self.environment_manager.load_scene(theme, save_step)
            
            step_timings['director'] = time.time() - step_start
        
            # 7. 更新状态（如果提供了save_step）
            step_start = time.time()
            new_step = save_step
            if save_step:
                # 6.1 创建新的存档步骤
                new_step = self.save_manager.create_new_step(theme, save_step)
                if not new_step:
                    new_step = save_step  # 如果创建失败，使用原步骤
                
                # 6.5 更新Agent实际状态（依据环境变化分析结果和导演决策带来的变化）
                # 首先，根据导演决策生成对Agent状态的影响
                director_state_changes = self._get_director_state_changes(
                    theme, director_decision, current_scene_id, current_room_id, agent_responses
                )
                
                # 从环境变化分析结果中获取Agent执行结果
                agent_execution_results_dict = {}
                for exec_result in agent_execution_results:
                    char_id = exec_result.get("character_id")
                    if char_id:
                        agent_execution_results_dict[char_id] = exec_result.get("execution_result", {})
                
                for resp in agent_responses:
                    if not resp or not isinstance(resp, dict):
                        continue
                    character_id = resp.get('character_id')
                    if not character_id:
                        continue
                    
                    # 获取环境变化分析确认的实际执行结果
                    execution_result = agent_execution_results_dict.get(character_id, {})
                    
                    # Agent的预期状态变化（从响应中获取）
                    agent_state_changes = resp.get('state_changes', {})
                    agent_attribute_changes = resp.get('attribute_changes', {})
                    
                    # 根据环境变化分析结果确认Agent的实际状态变化
                    # 如果执行失败，可能需要调整状态变化
                    if execution_result.get("success") == False:
                        # 执行失败，可能需要撤销某些状态变化
                        failure_reason = execution_result.get("failure_reason", "")
                        logger.info(f"⚠️ {resp.get('character_name', '未知')} 执行失败: {failure_reason}")
                        # 这里可以根据失败原因调整状态变化
                    
                    # 获取该角色受导演决策影响的状态变化
                    character_director_changes = director_state_changes.get(character_id, {})
                    director_state = character_director_changes.get('state_changes', {})
                    director_attributes = character_director_changes.get('attribute_changes', {})
                    
                    # 合并状态变化（环境变化分析确认的状态变化 + 导演决策带来的变化）
                    merged_state_changes = self._merge_state_changes(agent_state_changes, director_state)
                    merged_attribute_changes = self._merge_attribute_changes(agent_attribute_changes, director_attributes)
                    
                    # 只有当有状态变化时才更新
                    if merged_state_changes or merged_attribute_changes:
                        self.state_updater.update_character_state(
                            theme,
                            new_step,
                            character_id,
                            merged_state_changes,
                            merged_attribute_changes
                        )
                
                # 更新场景状态（从环境变化分析结果中提取）
                major_events = self._extract_major_events(agent_responses)
                # 从environment_analysis中提取场景变化
                scene_changes = environment_changes.get('scene_changes', {})
                surface_changes = scene_changes.get('surface', {})
                location = surface_changes.get('location', {})
                if location:
                    # 处理location可能是字符串或字典的情况
                    if isinstance(location, dict):
                        logger.info(f"📍 准备更新场景位置: region={location.get('region', 'N/A')}, specific_location={location.get('specific_location', 'N/A')}")
                    elif isinstance(location, str):
                        logger.info(f"📍 准备更新场景位置: {location}")
                    else:
                        logger.info(f"📍 准备更新场景位置: {location}")
                else:
                    logger.warning(f"⚠️ 环境变化分析未返回位置更新，场景位置可能不会更新")
                
                # 保存怪物信息到场景状态
                appear_monster = director_decision.get("appear_monster", [])
                if appear_monster:
                    # 确保怪物信息被保存到SCENE_STATE.json
                    monster_state = {
                        "appeared_monsters": appear_monster if isinstance(appear_monster, list) else [appear_monster],
                        "monster_description": director_decision.get("monster_description", "")
                    }
                    self.scene_state_manager.update_scene_state(
                        theme,
                        new_step,
                        {"monsters": monster_state}
                    )
                    logger.info(f"💾 已保存怪物信息到场景状态: {appear_monster}")
                
                self.state_updater.update_scene_state(
                    theme,
                    new_step,
                    scene_changes,
                    major_events
                )
                # 验证位置是否已更新
                updated_scene_check = self.environment_manager.load_scene(theme, new_step)
                if updated_scene_check:
                    location_check = re.search(r'\*\*具体位置\*\*[：:]\s*([^\n]+)', updated_scene_check)
                    if location_check:
                        logger.info(f"✅ 场景位置已更新为: {location_check.group(1).strip()}")
                    else:
                        logger.warning(f"⚠️ 场景位置更新后无法提取位置信息")
                
                # 6.4 加载更新后的场景（用于格式化）
                updated_scene_content = self.environment_manager.load_scene(theme, new_step)
                if updated_scene_content:
                    scene_content = updated_scene_content
                    # 使用更新后的场景内容来生成环境状态摘要
                    environment_changes['updated_scene_content'] = updated_scene_content
            
            step_timings['update'] = time.time() - step_start
            
            # 7. 格式化响应（转换为适合玩家角色的文本）- 在更新状态之后
            step_start = time.time()
            try:
                logger.info("📝 开始格式化响应...")
                logger.info(f"   agent_responses 类型: {type(agent_responses)}, 长度: {len(agent_responses) if agent_responses else 0}")
                
                # 如果导演评估返回了更新的场景描述（包含事件、怪物、环境NPC的反应），
                # 需要确保这些内容被传递给玩家
                # 检查是否有事件或怪物出现
                has_event = director_decision.get("trigger_event") and director_decision.get("event_description")
                has_monster = director_decision.get("appear_monster") and director_decision.get("monster_description")
                
                # 如果有事件或怪物，或者没有Agent响应但有场景描述更新，创建虚拟响应
                if (has_event or has_monster or (not agent_responses and updated_scene_description)):
                    if has_event or has_monster:
                        # 提取事件和怪物描述
                        event_desc = director_decision.get("event_description", "") if has_event else ""
                        monster_desc = director_decision.get("monster_description", "") if has_monster else ""
                        combined_desc = "\n\n".join([d for d in [event_desc, monster_desc] if d])
                        
                        logger.info("ℹ️  导演触发了事件或怪物，将添加到响应中")
                        # 创建虚拟响应，包含事件和怪物描述
                        virtual_response = {
                            'character_id': 'director',
                            'character_name': '环境',
                            'response': combined_desc,
                            'state_changes': {},
                            'attribute_changes': {}
                        }
                        # 如果有Agent响应，将虚拟响应添加到列表开头；否则使用虚拟响应
                        if agent_responses:
                            agent_responses = [virtual_response] + agent_responses
                        else:
                            agent_responses = [virtual_response]
                    elif not agent_responses and updated_scene_description:
                        logger.info("ℹ️  没有重要角色响应，但导演评估返回了场景描述更新（包含环境NPC反应），将用于格式化")
                        # 创建一个虚拟响应，包含环境NPC的反应
                        virtual_response = {
                            'character_id': 'environment_npc',
                            'character_name': '环境',
                            'response': updated_scene_description,
                            'state_changes': {},
                            'attribute_changes': {}
                        }
                        agent_responses = [virtual_response]
                
                formatted = self.response_formatter.format_responses_for_player(
                    agent_responses,
                    player_role or '玩家',
                    scene_content,
                    platform
                )
                logger.info("✅ 响应格式化完成")
                step_timings['format'] = time.time() - step_start
            except Exception as e:
                logger.error(f"❌ 响应格式化失败: {e}")
                logger.error(f"   agent_responses: {agent_responses}")
                logger.error(traceback.format_exc())
                step_timings['format'] = time.time() - step_start
                raise
            
            # 7.1 保存对话历史（如果创建了新步骤）
            if new_step and new_step != save_step:
                try:
                    summary = formatted.get('surface', {}).get('summary', '')
                    self.conversation_history.save_conversation(
                        theme,
                        new_step,
                        instruction,
                        summary
                    )
                    logger.info(f"✅ 对话历史已保存到步骤: {new_step}")
                except Exception as e:
                    logger.warning(f"⚠️ 保存对话历史失败: {e}")
            
            # 8. 返回结果（表/里分离）
            total_time = time.time() - total_start_time
            step_timings['total'] = total_time
                
            # 提取环境状态信息（使用JSON结构化数据，避免文本解析）
            try:
                scene_changes = environment_changes.get('scene_changes', {})
                surface_changes = scene_changes.get('surface', {})
                location = surface_changes.get('location', {})
                
                # 从场景状态JSON中获取信息（如果LLM没有返回，则从场景状态中获取）
                scene_state = self.scene_state_manager.get_scene_state(theme, new_step or save_step or "0_step")
                state_changes = scene_state.get('state_changes', {})
                
                # 优先使用LLM返回的结构化数据，如果没有则从场景状态中获取
                time_info = surface_changes.get('time', '') or state_changes.get('time', '')
                
                # 位置信息：优先使用LLM返回的，如果没有则从场景状态中获取
                # 处理location可能是字符串或字典的情况
                if not isinstance(location, dict):
                    # 如果location是字符串，转换为字典格式
                    if isinstance(location, str):
                        location = {'specific_location': location}
                    else:
                        location = {}
                
                # 如果仍然没有位置信息，从场景状态中获取
                if not location.get('specific_location'):
                    location_from_state = state_changes.get('location', {})
                    if isinstance(location_from_state, dict):
                        location.update(location_from_state)
                    elif isinstance(location_from_state, str):
                        location['specific_location'] = location_from_state
                
                # 如果仍然没有位置信息，从场景剧本的JSON结构中获取
                if not location.get('specific_location'):
                    current_scene_id = self.scene_state_manager.get_current_scene_id(theme, new_step or save_step or "0_step")
                    current_room_id = self.scene_state_manager.get_current_room_id(theme, new_step or save_step or "0_step")
                    
                    if current_room_id:
                        room_script = self.script_manager.load_room_script(theme, current_room_id)
                        if room_script:
                            room_state = room_script.get('surface', {}).get('state', {})
                            # 处理地点字段（可能是字典）
                            location_data = room_state.get('地点', {})
                            if isinstance(location_data, dict):
                                if location_data.get('具体位置'):
                                    location['specific_location'] = location_data.get('具体位置')
                                if location_data.get('区域'):
                                    location['region'] = location_data.get('区域')
                            # 兼容旧格式（直接是字符串）
                            elif isinstance(room_state.get('具体位置'), str):
                                if not isinstance(location, dict):
                                    location = {}
                                location['specific_location'] = room_state.get('具体位置')
                            if room_state.get('区域'):
                                if not isinstance(location, dict):
                                    location = {}
                                location['region'] = room_state.get('区域')
                    elif current_scene_id:
                        scene_script = self.script_manager.load_scene_script(theme, current_scene_id)
                        if scene_script:
                            scene_state = scene_script.get('surface', {}).get('state', {})
                            # 处理地点字段（可能是字典）
                            location_data = scene_state.get('地点', {})
                            if isinstance(location_data, dict):
                                if location_data.get('具体位置'):
                                    location['specific_location'] = location_data.get('具体位置')
                                if location_data.get('区域'):
                                    location['region'] = location_data.get('区域')
                            # 兼容旧格式（直接是字符串）
                            elif isinstance(scene_state.get('具体位置'), str):
                                if not isinstance(location, dict):
                                    location = {}
                                location['specific_location'] = scene_state.get('具体位置')
                            if scene_state.get('区域'):
                                if not isinstance(location, dict):
                                    location = {}
                                location['region'] = scene_state.get('区域')
                            
                            # 如果没有时间信息，从场景剧本中获取
                            if not time_info and scene_state.get('时间'):
                                time_info = scene_state.get('时间')
                
                # 构建环境状态摘要（使用JSON结构化数据）
                environment_status = {
                    'time': time_info,
                    'location': {
                        'region': location.get('region', ''),
                        'specific_location': location.get('specific_location', ''),
                        'coordinates': location.get('coordinates', ''),
                        'environment': location.get('environment', '')
                    },
                    'current_narrative': surface_changes.get('current_narrative', ''),
                    'goal': surface_changes.get('goal', ''),
                    'changes_summary': self._generate_environment_status_from_json(
                        time_info, location, surface_changes, state_changes
                    )
                }
            except Exception as e:
                logger.error(f"❌ 提取环境状态信息失败: {e}")
                logger.error(traceback.format_exc())
                environment_status = {
                    'time': '',
                    'location': {},
                    'current_narrative': '',
                    'goal': '',
                    'changes_summary': '提取失败'
                }
            
            try:
                logger.info("📦 开始构建返回结果...")
                logger.info(f"   formatted 类型: {type(formatted)}, 键: {formatted.keys() if isinstance(formatted, dict) else 'N/A'}")
                logger.info(f"   aggregated 类型: {type(aggregated)}, 键: {aggregated.keys() if isinstance(aggregated, dict) else 'N/A'}")
                logger.info(f"   environment_changes 类型: {type(environment_changes)}, 键: {environment_changes.keys() if isinstance(environment_changes, dict) else 'N/A'}")
                logger.info(f"   agent_responses 类型: {type(agent_responses)}, 长度: {len(agent_responses) if agent_responses else 0}")
                
                result = {
                    'surface': {
                        'responses': formatted.get('surface', {}).get('responses', []),  # 格式化后的文本响应
                        'summary': formatted.get('surface', {}).get('summary', ''),  # 格式化后的摘要
                        'environment_status': environment_status,  # 环境状态信息
                        'status_summary': environment_changes.get('status_summary', {}),  # 状态总结
                        'decision_points': environment_changes.get('decision_points', {'has_decision': False, 'description': '', 'options': []})  # 决策点
                    },
                    'hidden': {
                        'state_changes': aggregated.get('hidden', {}).get('state_changes', {}),
                        'attribute_changes': aggregated.get('hidden', {}).get('attribute_changes', {}),
                        'environment_changes': environment_changes,
                        'raw_responses': formatted.get('hidden', {}).get('raw_responses', agent_responses),  # 保留原始响应（包含execution_result）
                        'execution_results': agent_execution_results  # 从环境变化分析结果中获取
                    },
                    'new_step': new_step,
                    'step_timings': step_timings  # 各步骤的耗时（秒）
                }
                
                logger.info("✅ 返回结果构建完成")
                return result
            except Exception as e:
                logger.error(f"❌ 构建返回结果失败: {e}")
                logger.error(traceback.format_exc())
                raise
        except Exception as e:
            logger.error(f"❌ process_instruction 执行失败: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _generate_environment_status_from_json(self, time_info: str, location: Dict, 
                                               surface_changes: Dict, state_changes: Dict) -> str:
        """
        从JSON结构化数据生成环境状态描述（避免文本解析）
        
        Args:
            time_info: 时间信息（字符串）
            location: 位置信息（字典）
            surface_changes: 表面变化（字典）
            state_changes: 状态变化（字典）
        
        Returns:
            多行格式的环境状态描述
        """
        parts = []
        
        # 时间信息
        if time_info:
            # 清理时间信息，移除多余的括号和说明
            time_info = re.sub(r'\s*（.*?）', '', time_info)  # 移除括号内容
            time_info = time_info.strip()
            if time_info:
                parts.append(f"时间: {time_info}")
        
        # 位置信息（处理location可能是字符串或字典的情况）
        # 不显示技术标识符（如scene_id），只显示可读的位置名称
        if isinstance(location, dict):
            if location.get('specific_location'):
                loc_str = location.get('specific_location', '')
                # 检查是否是技术标识符（scene_xxx或room_xxx格式），如果是则跳过
                if not re.match(r'^scene_\d+$', loc_str) and not re.match(r'^room_\d+_\d+$', loc_str):
                    if location.get('region'):
                        region = location.get('region', '')
                        # 检查region是否也是技术标识符
                        if not re.match(r'^scene_\d+$', region) and not re.match(r'^room_\d+_\d+$', region):
                            loc_str = f"{region} - {loc_str}"
                    parts.append(f"位置: {loc_str}")
            elif location.get('region'):
                region = location.get('region', '')
                # 检查是否是技术标识符
                if not re.match(r'^scene_\d+$', region) and not re.match(r'^room_\d+_\d+$', region):
                    parts.append(f"位置: {region}")
        elif isinstance(location, str) and location:
            # 检查是否是技术标识符
            if not re.match(r'^scene_\d+$', location) and not re.match(r'^room_\d+_\d+$', location):
                parts.append(f"位置: {location}")
        
        # 当前状况（不截断）
        if surface_changes.get('current_narrative'):
            narrative = surface_changes['current_narrative']
            parts.append(f"状况: {narrative}")
        
        # 返回多行格式
        return "\n".join(parts) if parts else ""
    
    def _generate_environment_changes_summary(self, old_scene_content: str, new_changes: Dict) -> str:
        """生成环境状态摘要（即使无明显变化也显示当前状态）"""
        parts = []
        
        # 优先使用新变化中的信息
        time_info = new_changes.get('time', '')
        location = new_changes.get('location', {})
        
        # 如果没有新变化，尝试从场景内容中提取
        # 确保location是字典
        if not isinstance(location, dict):
            if isinstance(location, str):
                location = {'specific_location': location}
            else:
                location = {}
        
        if not time_info or not location.get('specific_location'):
            # 从场景内容中提取时间（支持多种格式）
            if not time_info:
                # 匹配 "- **时间**：黎明（具体时刻：约6:00）" 或 "时间：黎明"
                time_patterns = [
                    r'\*\*时间\*\*[：:]\s*([^\n（]+)',  # 匹配到"（"之前
                    r'时间[：:]\s*([^\n（]+)',  # 简单格式
                ]
                for pattern in time_patterns:
                    time_match = re.search(pattern, old_scene_content)
                    if time_match:
                        time_info = time_match.group(1).strip()
                        # 如果后面有具体时刻，也提取
                        full_match = re.search(r'\*\*时间\*\*[：:]\s*([^\n]+)', old_scene_content)
                        if full_match:
                            time_info = full_match.group(1).strip()
                        break
            
            # 从场景内容中提取位置（支持多种格式）
            if not location.get('specific_location'):
                # 匹配 "- **具体位置**：冒险者公会大厅"
                location_patterns = [
                    r'\*\*具体位置\*\*[：:]\s*([^\n]+)',
                    r'具体位置[：:]\s*([^\n]+)',
                ]
                for pattern in location_patterns:
                    location_match = re.search(pattern, old_scene_content)
                    if location_match:
                        location['specific_location'] = location_match.group(1).strip()
                        break
                
                # 提取区域
                if not location.get('region'):
                    region_patterns = [
                        r'\*\*区域\*\*[：:]\s*([^\n]+)',
                        r'区域[：:]\s*([^\n]+)',
                    ]
                    for pattern in region_patterns:
                        region_match = re.search(pattern, old_scene_content)
                        if region_match:
                            location['region'] = region_match.group(1).strip()
                            break
        
        # 构建当前环境状态描述（确保至少有时间或位置信息）
        if time_info:
            # 清理时间信息，移除多余的括号和说明
            time_info = re.sub(r'\s*（.*?）', '', time_info)  # 移除括号内容
            time_info = time_info.strip()
            parts.append(f"时间: {time_info}")
        
        if location.get('specific_location'):
            loc_str = location.get('specific_location', '')
            if location.get('region'):
                loc_str = f"{location.get('region', '')} - {loc_str}"
            parts.append(f"位置: {loc_str}")
        elif location.get('region'):
            parts.append(f"位置: {location.get('region', '')}")
        
        if new_changes.get('current_narrative'):
            narrative = new_changes['current_narrative']
            parts.append(f"状况: {narrative}")
        
        # 如果没有任何信息，尝试从摘要或其他地方提取
        if not parts:
            # 尝试从场景内容中提取环境描述
            env_match = re.search(r'\*\*环境描述\*\*[：:]\s*([^\n]+)', old_scene_content)
            if env_match:
                env_desc = env_match.group(1).strip()
                if env_desc:
                    parts.append(f"环境: {env_desc}")
        
        # 如果仍然没有任何信息，显示默认信息
        if not parts:
            # 尝试提取目标信息
            goal_match = re.search(r'\*\*目标\*\*[：:]\s*([^\n]+)', old_scene_content)
            if goal_match:
                goal = goal_match.group(1).strip()
                if goal:
                    parts.append(f"目标: {goal}")
        
        # 如果还是没有任何信息，尝试从场景内容中提取基本信息
        if not parts:
            # 尝试从场景内容中提取基本信息作为当前状态描述
            # 提取场景描述的第一句话或第一段
            if old_scene_content:
                # 尝试提取场景描述的第一行或第一段
                lines = old_scene_content.split('\n')
                for line in lines:
                    line = line.strip()
                    # 跳过空行和注释
                    if line and not line.startswith('#') and not line.startswith('<!--'):
                        # 如果这行看起来像描述（不是标题、不是列表项）
                        if not line.startswith('#') and not line.startswith('-') and not line.startswith('*'):
                            # 使用完整内容，不截断
                            parts.append(f"状况: {line}")
                            break
        
        # 返回多行格式（每行一个键值对）
        if parts:
            return "\n".join(parts)
        else:
            # 如果仍然没有任何信息，返回空字符串（不显示"进行中"）
            return ""
    
    def _extract_major_events(self, agent_responses: List[Dict]) -> List[str]:
        """从响应中提取重大事件"""
        # 这里可以扩展为使用LLM分析响应，提取重大事件
        # 暂时返回空列表
        events = []
        for resp in agent_responses:
            if not resp or not isinstance(resp, dict):
                continue
            # 简单提取：如果响应包含某些关键词，认为是重大事件
            response_text = format_agent_response(resp.get('response', ''))
            if not response_text:
                continue
            response_text = response_text.lower()
            if any(keyword in response_text for keyword in ['发现', '获得', '击败', '完成', '触发']):
                character_name = resp.get('character_name', '未知')
                response_preview = response_text[:50] if response_text else ''
                events.append(f"{character_name}: {response_preview}...")
        return events
    
    def _evaluate_as_director(self, theme: str, current_scene_id: str, current_room_id: Optional[str],
                             instruction: str, save_step: Optional[str], agent_responses: List[Dict],
                             scene_content: str, platform: str = None) -> Dict:
        """
        导演评估：LLM作为导演评估当前状态并做出决策（基于Agent实际响应）
        
        Args:
            theme: 主题
            current_scene_id: 当前场景ID
            current_room_id: 当前房间ID（可选）
            instruction: 玩家指令
            save_step: 存档步骤
            agent_responses: Agent响应列表
            
        Returns:
            导演决策字典
        """
        try:
            # 加载场景/房间剧本
            scene_script = self.script_manager.load_scene_script(theme, current_scene_id)
            room_script = None
            if current_room_id:
                room_script = self.script_manager.load_room_script(theme, current_room_id)
            
            # 获取潜在事件和怪物
            potential_events = self.script_manager.get_potential_events(theme, current_scene_id, current_room_id)
            potential_monsters = self.script_manager.get_potential_monsters(theme, current_scene_id, current_room_id)
            
            # 获取可连接目标
            connected_targets = self.script_manager.get_connected_scenes(theme, current_scene_id, current_room_id)
            
            # 获取场景网络
            scene_network = self.script_manager.get_scene_network(theme)
            
            # 获取角色状态
            all_characters = self.character_store.list_characters()
            characters = [c for c in all_characters if c.get('theme') == theme]
            character_states = {}
            for char in characters:
                char_id = char.get('id')
                if char_id:
                    # 加载角色状态（从存档）
                    char_path = os.path.join(
                        self.environment_manager.base_dir,
                        self.config.SAVE_DIR,
                        theme,
                        save_step or "0_step",
                        f"{char_id}.json"
                    )
                    if os.path.exists(char_path):
                        try:
                            import json
                            with open(char_path, "r", encoding="utf-8") as f:
                                char_data = json.load(f)
                                character_states[char_id] = char_data.get("attributes", {})
                        except:
                            pass
            
            # 获取故事总览
            story_overview = self.script_manager.load_story_overview(theme)
            
            # 获取场景状态和已触发事件
            scene_state = self.scene_state_manager.get_scene_state(theme, save_step or "0_step")
            triggered_events = self.scene_state_manager.get_triggered_events(theme, save_step or "0_step")
            
            # 获取游戏时间和进入时间
            game_time = self.time_manager.get_game_time(theme, save_step or "0_step")
            enter_time = self.scene_state_manager.get_enter_time(theme, save_step or "0_step")
            
            # 构建Agent响应摘要（用于导演评估）
            agent_responses_summary = []
            for resp in agent_responses:
                if resp and isinstance(resp, dict):
                    response_text = format_agent_response(resp.get("response", ""))
                    hidden = resp.get("hidden", {})
                    inner_monologue = hidden.get("inner_monologue", "") if isinstance(hidden, dict) else ""
                    agent_responses_summary.append({
                        "character_name": resp.get("character_name", "未知"),
                        "response": response_text,
                        "inner_monologue": inner_monologue if inner_monologue else ""
                    })
            
            # 构建导演上下文
            director_context = {
                "current_scene": current_scene_id,
                "current_room": current_room_id,
                "scene_script": scene_script,
                "room_script": room_script,
                "potential_events": potential_events,
                "potential_monsters": potential_monsters,
                "connected_targets": connected_targets,
                "scene_network": scene_network,
                "character_states": character_states,
                "player_instruction": instruction,
                "story_overview": story_overview,
                "scene_state": scene_state,
                "triggered_events": triggered_events,
                "game_time": game_time,
                "enter_time": enter_time,
                "agent_responses": agent_responses_summary  # 添加Agent响应
            }
            
            # 调用导演评估器
            decision = self.director_evaluator.evaluate_as_director(director_context, platform=platform)
            
            # 验证场景转换
            if decision.get("transition_target"):
                target_id = decision["transition_target"]
                transition_type = decision.get("transition_type", "scene")
                
                from_type = "room" if current_room_id else "scene"
                from_id = current_room_id if current_room_id else current_scene_id
                
                # 验证连接
                if not self.script_manager.check_scene_connection(theme, from_id, target_id, from_type, transition_type):
                    logger.warning(f"⚠️ 场景转换验证失败: {from_id} -> {target_id}")
                    decision["transition_target"] = None
                    decision["blocking_reason"] = "目标不在可连接列表中"
                else:
                    # 检查前置条件
                    can_connect, reason = self.script_manager.check_connection_conditions(
                        theme, from_id, target_id, director_context, from_type, transition_type
                    )
                    if not can_connect:
                        logger.warning(f"⚠️ 场景转换前置条件不满足: {reason}")
                        decision["transition_target"] = None
                        decision["blocking_reason"] = reason
            
            # 验证怪物（支持数组格式）
            appear_monster = decision.get("appear_monster", [])
            if appear_monster:
                # 兼容旧格式（字符串）和新格式（数组）
                if isinstance(appear_monster, str):
                    monster_list = [appear_monster] if appear_monster else []
                elif isinstance(appear_monster, list):
                    monster_list = appear_monster
                else:
                    monster_list = []
                
                # 验证每个怪物是否在潜在怪物列表中
                valid_monsters = []
                potential_monster_names = {m.get("name") for m in potential_monsters}
                potential_monster_ids = {m.get("id") for m in potential_monsters}
                
                for monster_id_or_name in monster_list:
                    # 检查怪物名称或ID是否在潜在怪物列表中
                    if monster_id_or_name in potential_monster_names or monster_id_or_name in potential_monster_ids:
                        valid_monsters.append(monster_id_or_name)
                    else:
                        logger.warning(f"⚠️ 怪物验证失败: {monster_id_or_name} 不在潜在怪物列表中")
                
                # 更新为验证后的怪物列表
                decision["appear_monster"] = valid_monsters if valid_monsters else []
            
            return decision
        except Exception as e:
            logger.error(f"❌ 导演评估失败: {e}")
            logger.error(traceback.format_exc())
            return {
                "trigger_event": None,
                "event_description": "",
                "appear_monster": [],
                "monster_description": "",
                "transition_target": None,
                "transition_type": "scene",
                "elapsed_time": 1.0,
                "reasoning": f"评估失败: {str(e)}"
            }
    
    def _get_director_state_changes(self, theme: str, director_decision: Dict, 
                                    current_scene_id: str, current_room_id: Optional[str],
                                    agent_responses: List[Dict]) -> Dict[str, Dict]:
        """
        从导演决策中提取对各个角色的状态影响
        
        Args:
            theme: 主题
            director_decision: 导演决策结果
            current_scene_id: 当前场景ID
            current_room_id: 当前房间ID
            agent_responses: Agent响应列表
        
        Returns:
            字典，格式为 {character_id: {'state_changes': {...}, 'attribute_changes': {...}}}
        """
        director_state_changes = {}
        
        # 获取所有角色的ID
        character_ids = []
        for resp in agent_responses:
            if resp and isinstance(resp, dict):
                char_id = resp.get('character_id')
                if char_id:
                    character_ids.append(char_id)
                    director_state_changes[char_id] = {
                        'state_changes': {},
                        'attribute_changes': {}
                    }
        
        # 1. 处理事件触发带来的状态变化
        if director_decision.get("trigger_event"):
            event_id = director_decision.get("trigger_event")
            event_effects = self._get_event_effects(theme, event_id)
            
            if event_effects:
                character_changes = event_effects.get("character_changes", "")
                # 解析character_changes文本，提取状态变化
                # 这里简化处理，实际可能需要更复杂的解析
                if character_changes:
                    # 将character_changes应用到所有角色（或根据事件定义指定角色）
                    for char_id in character_ids:
                        # 这里可以根据事件定义更精确地分配状态变化
                        # 目前简化处理，所有角色都获得相同的状态变化
                        if "任务" in character_changes or "目标" in character_changes:
                            director_state_changes[char_id]['state_changes']['current_quest'] = character_changes
                        # 可以添加更多解析逻辑
        
        # 2. 处理怪物出现带来的状态变化（支持多个怪物）
        appear_monster = director_decision.get("appear_monster", [])
        if appear_monster:
            # 兼容旧格式（字符串）和新格式（数组）
            if isinstance(appear_monster, str):
                monster_list = [appear_monster] if appear_monster else []
            elif isinstance(appear_monster, list):
                monster_list = appear_monster
            else:
                monster_list = []
            
            if monster_list:
                # 将怪物列表转换为描述字符串
                if len(monster_list) == 1:
                    monster_desc = monster_list[0]
                else:
                    monster_desc = f"{len(monster_list)}只怪物: {', '.join(monster_list)}"
                
                # 怪物出现可能导致角色进入战斗状态
                for char_id in character_ids:
                    director_state_changes[char_id]['state_changes']['combat_state'] = f"遭遇{monster_desc}"
                    # 可以根据怪物类型添加更多状态变化
        
        # 3. 处理场景转换带来的状态变化
        if director_decision.get("transition_target"):
            target_id = director_decision.get("transition_target")
            transition_type = director_decision.get("transition_type", "scene")
            
            # 获取目标场景/房间的名称
            target_name = None
            if transition_type == "scene":
                # 从场景池中查找场景名称
                scenes = self.script_manager.get_scene_pool(theme)
                for scene in scenes:
                    if scene.get("id") == target_id:
                        target_name = scene.get("name", target_id)
                        break
            else:
                # 从房间脚本中获取房间名称
                room_script = self.script_manager.load_room_script(theme, target_id)
                if room_script:
                    surface = room_script.get("surface", {})
                    # 尝试从场景描述中提取名称，或使用房间ID
                    target_name = surface.get("name", target_id)
            
            if target_name:
                for char_id in character_ids:
                    # 更新位置
                    director_state_changes[char_id]['state_changes']['location'] = target_name
                    # 场景转换可能带来环境适应
                    director_state_changes[char_id]['state_changes']['environment_adaptation'] = f"适应{target_name}环境"
        
        return director_state_changes
    
    def _get_event_effects(self, theme: str, event_id: str) -> Optional[Dict]:
        """获取事件的影响效果"""
        try:
            # 从get_potential_events获取事件列表（包含core和random事件）
            # 这里需要获取当前场景的事件，但为了简化，我们从所有场景中查找
            overview = self.script_manager.load_story_overview(theme)
            
            # 加载core_events.json
            import os
            import json
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            core_events_file = os.path.join(
                base_dir,
                self.config.CHARACTER_CONFIG_DIR,
                theme,
                "core_events.json"
            )
            if os.path.exists(core_events_file):
                with open(core_events_file, "r", encoding="utf-8") as f:
                    core_data = json.load(f)
                    for event in core_data.get("core_events", []):
                        if event.get("id") == event_id:
                            return event.get("effects", {})
            
            # 加载random_events.json
            random_events_file = os.path.join(
                base_dir,
                self.config.CHARACTER_CONFIG_DIR,
                theme,
                "random_events.json"
            )
            if os.path.exists(random_events_file):
                with open(random_events_file, "r", encoding="utf-8") as f:
                    random_data = json.load(f)
                    for event in random_data.get("random_events", []):
                        if event.get("id") == event_id:
                            return event.get("effects", {})
        except Exception as e:
            logger.warning(f"获取事件效果失败: {e}")
        
        return None
    
    def _merge_state_changes(self, agent_changes: Dict, director_changes: Dict) -> Dict:
        """合并Agent的状态变化和导演决策带来的状态变化"""
        merged = agent_changes.copy() if agent_changes else {}
        if director_changes:
            merged.update(director_changes)
        return merged
    
    def _merge_attribute_changes(self, agent_changes: Dict, director_changes: Dict) -> Dict:
        """合并Agent的属性变化和导演决策带来的属性变化"""
        merged = agent_changes.copy() if agent_changes else {}
        if director_changes:
            # 对于数值属性，可能需要累加而不是覆盖
            for key, value in director_changes.items():
                if key in merged and isinstance(merged[key], (int, float)) and isinstance(value, (int, float)):
                    merged[key] = merged[key] + value
                else:
                    merged[key] = value
        return merged

