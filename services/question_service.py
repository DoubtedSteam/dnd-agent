"""
提问服务：回答玩家问题，检查一致性，更新场景
"""
import json
from typing import Dict, List, Optional, Tuple
from services.chat_service import ChatService
from services.character_store import CharacterStore
from services.environment_manager import EnvironmentManager
from services.question_consistency_checker import QuestionConsistencyChecker
from services.save_manager import SaveManager
from services.state_updater import StateUpdater
from config import Config


class QuestionService:
    """提问服务"""
    
    def __init__(self, config: Config):
        self.config = config
        self.chat_service = ChatService()
        self.character_store = CharacterStore(config)
        self.environment_manager = EnvironmentManager(config)
        self.consistency_checker = QuestionConsistencyChecker(config)
        self.save_manager = SaveManager(config)
        self.state_updater = StateUpdater(config)
    
    def answer_question(self, question: str, theme: str, 
                       save_step: Optional[str] = None,
                       character_ids: Optional[List[str]] = None,
                       platform: str = None, player_role: str = None) -> Dict:
        """
        回答玩家问题，检查一致性，更新场景
        
        Args:
            question: 玩家问题
            theme: 主题
            save_step: 存档步骤（可选，如果提供则创建新步骤）
            character_ids: 指定角色ID列表（可选，如果为None则使用所有角色）
            platform: API平台
            player_role: 玩家扮演的角色
        
        Returns:
            包含回答、一致性检查结果、新步骤等信息的字典
        """
        # 1. 加载场景
        scene_content = self.environment_manager.load_scene(theme, save_step)
        if not scene_content:
            return {
                "error": "无法加载场景信息",
                "answer": "无法加载场景信息"
            }
        
        # 2. 提取玩家角色
        if not player_role:
            player_role = self._extract_player_role(scene_content)
        
        # 3. 加载角色信息
        if character_ids is None:
            all_characters = self.character_store.list_characters()
            characters = [c for c in all_characters if c.get('theme') == theme]
        else:
            characters = []
            for char_id in character_ids:
                char = self.character_store.get_character(char_id)
                if char:
                    characters.append(char)
        
        if not characters:
            return {
                "error": "没有找到角色信息",
                "answer": "没有找到角色信息"
            }
        
        # 4. 构建提示词
        system_prompt = self._build_question_prompt(
            scene_content, 
            characters, 
            player_role
        )
        
        user_message = f"玩家问题：{question}\n\n请根据以上信息回答玩家的问题。"
        
        platform = platform or self.config.DEFAULT_API_PLATFORM
        
        # 5. 调用LLM回答问题
        try:
            if platform.lower() == 'deepseek':
                answer = self.chat_service._call_deepseek_api(
                    [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_message}],
                    operation='question_answer',
                    context={'theme': theme, 'question': question[:50]}
                )
            elif platform.lower() == 'openai':
                answer = self.chat_service._call_openai_api(
                    [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_message}],
                    operation='question_answer',
                    context={'theme': theme, 'question': question[:50]}
                )
            else:
                raise ValueError(f"不支持的API平台: {platform}")
        except Exception as e:
            return {
                "error": f"回答问题失败: {str(e)}",
                "answer": f"回答问题失败: {str(e)}"
            }
        
        # 6. 如果提供了save_step，进行一致性检查和场景更新
        new_step = save_step
        consistency_result = None
        if save_step:
            # 6.1 获取历史步骤列表
            previous_steps = self.save_manager.list_steps(theme)
            
            # 6.2 检查一致性
            consistency_score, consistency_feedback, consistency_data = \
                self.consistency_checker.check_question_consistency(
                    question, answer, theme, save_step, previous_steps, platform
                )
            
            consistency_result = {
                'score': consistency_score,
                'feedback': consistency_feedback,
                'concretized_info': consistency_data.get('concretized_info', {}),
                'scene_updates': consistency_data.get('scene_updates', {}),
                'major_events': consistency_data.get('major_events', []),
                'character_updates': consistency_data.get('character_updates', {})
            }
            
            # 6.3 如果一致性检查通过（评分>=0.7），创建新步骤并更新场景和角色卡
            if consistency_score >= 0.7:
                # 创建新步骤
                new_step = self.save_manager.create_new_step(theme, save_step)
                if new_step:
                    # 更新场景
                    scene_updates = consistency_data.get('scene_updates', {})
                    major_events = consistency_data.get('major_events', [])
                    
                    if scene_updates or major_events:
                        self.state_updater.update_scene_state(
                            theme,
                            new_step,
                            scene_updates,
                            major_events
                        )
                    
                    # 更新角色卡（外貌和装备描述）
                    character_updates = consistency_data.get('character_updates', {})
                    if character_updates:
                        for character_id, updates in character_updates.items():
                            self.state_updater.update_character_appearance_and_equipment(
                                theme,
                                new_step,
                                character_id,
                                updates
                            )
            else:
                # 一致性检查失败，不创建新步骤
                new_step = save_step
                consistency_result['warning'] = "一致性检查未通过，未创建新步骤"
        
        # 7. 返回结果
        result = {
            "answer": answer,
            "question": question,
            "consistency_check": consistency_result
        }
        
        if new_step and new_step != save_step:
            result["new_step"] = new_step
        
        return result
    
    def _extract_player_role(self, scene_content: str) -> Optional[str]:
        """从场景内容中提取玩家角色"""
        if not scene_content:
            return None
        
        lines = scene_content.split('\n')
        for line in lines:
            if "玩家角色" in line or "玩家扮演" in line:
                if '：' in line:
                    role = line.split('：')[-1].strip()
                    if '，' in role:
                        role = role.split('，')[0].strip()
                    return role
                elif ':' in line:
                    role = line.split(':')[-1].strip()
                    if ',' in role:
                        role = role.split(',')[0].strip()
                    return role
        return None
    
    def _build_question_prompt(self, scene_content: str, characters: List[Dict], 
                               player_role: Optional[str]) -> str:
        """构建提问提示词"""
        attr_guide = self.chat_service._load_attr_guide(characters[0].get('theme', 'default') if characters else 'default')
        
        # 构建角色信息
        characters_info = []
        for char in characters:
            char_info = f"""
【{char['name']}】
描述：{char.get('description', '')}
属性：{json.dumps(char.get('attributes', {}), ensure_ascii=False, indent=2)}
"""
            characters_info.append(char_info)
        
        characters_text = "\n".join(characters_info)
        
        player_role_info = ""
        if player_role:
            player_role_info = f"\n【玩家角色】\n玩家扮演的角色：{player_role}\n- 请从玩家角色的视角来回答问题\n- 考虑玩家角色的身份、立场和可能知道的信息\n"
        
        prompt = f"""你是一个游戏助手，负责回答玩家的问题。

【信息来源：SCENE.md - 场景设定】
{scene_content}
{player_role_info}
【信息来源：人物卡配置】
{characters_text}

【信息来源：CHARACTER_ATTRIBUTES.md - 属性字段含义说明】
{attr_guide}

=== 重要要求 ===
1. 根据玩家角色、场景信息和人物卡信息来回答问题
2. 从玩家角色的视角出发，考虑玩家角色应该知道什么信息
3. 区分表/里信息：
   - 表信息（surface）：玩家可见的信息，可以直接回答
   - 里信息（hidden）：隐藏信息，不要直接暴露，但可以帮助你理解背景
4. 回答要准确、有帮助，符合游戏世界的设定
5. 如果问题涉及多个角色，可以综合多个角色的信息
6. 不要推进游戏进度，只是回答问题
"""
        return prompt

