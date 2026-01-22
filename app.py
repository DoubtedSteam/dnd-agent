from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from services.chat_service import ChatService
from services.consistency_checker import ConsistencyChecker
from services.character_store import CharacterStore
from services.conversation_store import ConversationStore
from services.multi_agent_coordinator import MultiAgentCoordinator
from services.question_service import QuestionService
from services.theme_manager import ThemeManager
from services.save_manager import SaveManager
from services.script_manager import ScriptManager
from services.environment_manager import EnvironmentManager
from services.token_tracker import token_tracker
from config import Config

# 配置日志（输出到服务器控制台）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# 初始化服务
chat_service = ChatService()
consistency_checker = ConsistencyChecker()
character_store = CharacterStore(Config())
conversation_store = ConversationStore(Config())
multi_agent_coordinator = MultiAgentCoordinator(Config())
question_service = QuestionService(Config())
theme_manager = ThemeManager(Config())
save_manager = SaveManager(Config())
script_manager = ScriptManager(Config())
environment_manager = EnvironmentManager(Config())

@app.route('/api/characters', methods=['GET'])
def get_characters():
    """获取所有人物卡"""
    characters = character_store.list_characters()
    return jsonify(characters)

@app.route('/api/characters', methods=['POST'])
def create_character():
    """创建新人物卡"""
    data = request.json
    
    if not data.get('name') or not data.get('description'):
        return jsonify({'error': '姓名和描述是必填项'}), 400
    
    character = character_store.create_character(
        name=data['name'],
        description=data['description'],
        attributes=data.get('attributes', {}),
        theme=data.get('theme', 'default')
    )
    return jsonify(character), 201

@app.route('/api/characters/<string:character_id>', methods=['GET'])
def get_character(character_id):
    """获取指定人物卡"""
    character = character_store.get_character(str(character_id))
    if not character:
        return jsonify({'error': '人物卡不存在'}), 404
    return jsonify(character)

@app.route('/api/characters/<string:character_id>', methods=['PUT'])
def update_character(character_id):
    """更新人物卡"""
    data = request.json
    
    character = character_store.update_character(str(character_id), data)
    if not character:
        return jsonify({'error': '人物卡不存在'}), 404
    return jsonify(character)

@app.route('/api/characters/<string:character_id>', methods=['DELETE'])
def delete_character(character_id):
    """删除人物卡"""
    ok = character_store.delete_character(str(character_id))
    if not ok:
        return jsonify({'error': '人物卡不存在'}), 404
    return jsonify({'message': '人物卡已删除'}), 200

@app.route('/api/characters/<string:character_id>/chat', methods=['POST'])
def chat_with_character(character_id):
    """与角色对话"""
    data = request.json
    
    if not data.get('message'):
        return jsonify({'error': '消息内容不能为空'}), 400
    
    user_message = data['message']
    platform = data.get('platform')  # 可选：指定API平台
    save_step = data.get('save_step')  # 可选：存档步骤（如 "0_step"）
    character = character_store.get_character(str(character_id))
    if not character:
        return jsonify({'error': '人物卡不存在'}), 404
    
    try:
        # 生成角色回复（不使用对话历史）
        character_response = chat_service.chat(
            character_description=character['description'],
            character_attributes=character.get('attributes', {}),
            user_message=user_message,
            platform=platform,
            theme=character.get('theme', 'default'),
            save_step=save_step
        )
        
        # 一致性检测
        consistency_score = None
        consistency_feedback = None
        
        if app.config.get('CONSISTENCY_CHECK_ENABLED', True):
            consistency_score, consistency_feedback = consistency_checker.check_consistency(
                character_description=character['description'],
                character_attributes=character.get('attributes', {}),
                user_message=user_message,
                latest_response=character_response,
                platform=platform,
                theme=character.get('theme', 'default'),
                save_step=save_step
            )
        
        # 保存对话记录（JSON文件）
        conversation = conversation_store.save_conversation(
            character_id=str(character_id),
            user_message=user_message,
            character_response=character_response,
            consistency_score=consistency_score,
            consistency_feedback=consistency_feedback
        )
        
        return jsonify({
            'response': character_response,
            'consistency_score': consistency_score,
            'consistency_feedback': consistency_feedback,
            'conversation_id': conversation['id']
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'对话生成失败: {str(e)}'}), 500

@app.route('/api/characters/<string:character_id>/conversations', methods=['GET'])
def get_conversations(character_id):
    """获取角色的对话历史"""
    character = character_store.get_character(str(character_id))
    if not character:
        return jsonify({'error': '人物卡不存在'}), 404
    
    limit = request.args.get('limit', type=int)
    conversations = conversation_store.get_conversations(str(character_id), limit=limit)
    
    return jsonify(conversations)

@app.route('/api/themes/<string:theme>/execute', methods=['POST'])
def execute_instruction(theme):
    """
    多智能体执行指令
    
    流程：
    1. 玩家给出指令
    2. 发送给每一个智能体
    3. 智能体按照自己的设定+环境+玩家指令给出响应
    4. 将响应放置到环境中
    5. 获得所有人物变化+环境变化
    6. 创建新存档步骤
    7. 更新状态
    8. 格式化响应
    9. 返回给玩家
    """
    data = request.json
    
    if not data.get('instruction'):
        return jsonify({'error': '指令内容不能为空'}), 400
    
    instruction = data['instruction']
    save_step = data.get('save_step')  # 可选：存档步骤
    character_ids = data.get('character_ids')  # 可选：指定角色ID列表
    platform = data.get('platform')  # 可选：指定API平台
    player_role = data.get('player_role')  # 可选：玩家扮演的角色
    
    # 开始新的一轮统计
    token_tracker.start_new_round()
    
    try:
        import traceback
        result = multi_agent_coordinator.process_instruction(
            instruction=instruction,
            theme=theme,
            save_step=save_step,
            character_ids=character_ids,
            platform=platform,
            player_role=player_role
        )
        
        if 'error' in result:
            return jsonify(result), 400
        
        # 添加当前轮次和累计统计
        current_round_stats = token_tracker.get_current_round_stats()
        session_stats = token_tracker.get_session_stats()
        
        result['token_stats'] = {
            'current_round': current_round_stats,
            'session_total': {
                'calls': session_stats['total_calls'],
                'tokens': session_stats['total_tokens'],
                'input_tokens': session_stats['total_input_tokens'],
                'output_tokens': session_stats['total_output_tokens']
            }
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        import traceback
        from services.api_failure_handler import APIConfirmationRequired
        
        # 如果是API确认异常，返回特殊状态码
        if isinstance(e, APIConfirmationRequired):
            return jsonify({
                'error': f'API调用已连续失败{e.failure_count}次，需要用户确认',
                'error_type': 'APIConfirmationRequired',
                'failure_count': e.failure_count,
                'error_message': e.error_message,
                'requires_confirmation': True
            }), 428  # 428 Precondition Required
        
        error_detail = traceback.format_exc()
        print(f"\n{'='*80}")
        print(f"❌ 执行失败 - 详细错误信息:")
        print(f"{'='*80}")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误消息: {str(e)}")
        print(f"\n完整堆栈跟踪:")
        print(error_detail)
        print(f"{'='*80}\n")
        return jsonify({
            'error': f'执行失败: {str(e)}',
            'error_type': type(e).__name__,
            'traceback': error_detail
        }), 500

@app.route('/api/themes/<string:theme>/saves', methods=['GET'])
def list_saves(theme):
    """列出主题下的所有存档步骤"""
    try:
        steps = save_manager.list_steps(theme)
        # 获取每个步骤的大小
        steps_info = []
        for step in steps:
            size = save_manager.get_step_size(theme, step)
            steps_info.append({
                'step': step,
                'size': size,
                'size_mb': round(size / (1024 * 1024), 2)
            })
        return jsonify({'steps': steps_info}), 200
    except Exception as e:
        return jsonify({'error': f'获取存档列表失败: {str(e)}'}), 500

@app.route('/api/themes/<string:theme>/saves/<string:step>', methods=['DELETE'])
def delete_save(theme, step):
    """删除指定的存档步骤"""
    try:
        success = save_manager.delete_step(theme, step)
        if success:
            return jsonify({'message': f'存档步骤 {step} 已删除'}), 200
        else:
            return jsonify({'error': f'存档步骤 {step} 不存在或删除失败'}), 404
    except Exception as e:
        return jsonify({'error': f'删除存档失败: {str(e)}'}), 500

@app.route('/api/themes/<string:theme>/saves', methods=['DELETE'])
def delete_all_saves(theme):
    """删除主题下的所有存档步骤（可保留指定步骤）"""
    try:
        data = request.json or {}
        keep_steps = data.get('keep_steps', ['0_step'])  # 默认保留0_step
        
        results = save_manager.delete_all_steps(theme, keep_steps)
        deleted = [step for step, success in results.items() if success]
        failed = [step for step, success in results.items() if not success]
        
        return jsonify({
            'message': f'已删除 {len(deleted)} 个存档步骤',
            'deleted': deleted,
            'failed': failed,
            'kept': keep_steps
        }), 200
    except Exception as e:
        return jsonify({'error': f'删除存档失败: {str(e)}'}), 500

@app.route('/api/themes/<string:theme>', methods=['DELETE'])
def delete_theme_saves(theme):
    """删除整个主题的所有存档"""
    try:
        success = save_manager.delete_theme(theme)
        if success:
            return jsonify({'message': f'主题 {theme} 的所有存档已删除'}), 200
        else:
            return jsonify({'error': f'主题 {theme} 不存在或删除失败'}), 404
    except Exception as e:
        return jsonify({'error': f'删除主题存档失败: {str(e)}'}), 500

@app.route('/api/themes/<string:theme>/question', methods=['POST'])
def ask_question(theme):
    """
    提问功能：回答玩家问题，检查一致性，更新场景
    
    依据：
    - 玩家角色
    - 人物卡信息
    - 环境信息
    
    如果提供了save_step，会：
    - 检查回答与历史的一致性
    - 提取具体化信息
    - 创建新存档步骤（如果一致性检查通过）
    - 更新场景文件
    """
    data = request.json
    
    if not data.get('question'):
        return jsonify({'error': '问题内容不能为空'}), 400
    
    question = data['question']
    save_step = data.get('save_step')  # 可选：存档步骤（如果提供则创建新步骤）
    character_ids = data.get('character_ids')  # 可选：指定角色ID列表
    platform = data.get('platform')  # 可选：指定API平台
    player_role = data.get('player_role')  # 可选：玩家扮演的角色
    
    try:
        result = question_service.answer_question(
            question=question,
            theme=theme,
            save_step=save_step,
            character_ids=character_ids,
            platform=platform,
            player_role=player_role
        )
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': f'回答问题失败: {str(e)}'}), 500

@app.route('/api/themes', methods=['GET'])
def list_themes():
    """列出所有可用的主题（剧本）"""
    try:
        themes = theme_manager.list_themes()
        return jsonify({'themes': themes}), 200
    except Exception as e:
        return jsonify({'error': f'获取主题列表失败: {str(e)}'}), 500

@app.route('/api/themes/<string:theme>/initialize', methods=['POST'])
def initialize_theme(theme):
    """初始化主题（创建0_step并设置初始场景）"""
    try:
        # 初始化0_step
        if save_manager._initialize_0_step(theme):
            # 获取初始场景内容
            scene_content = environment_manager.load_scene(theme, "0_step")
            if scene_content:
                return jsonify({
                    'success': True,
                    'step': '0_step',
                    'scene_content': scene_content
                }), 200
            else:
                return jsonify({
                    'success': True,
                    'step': '0_step',
                    'scene_content': None,
                    'message': '场景已初始化，但无法加载场景内容'
                }), 200
        else:
            return jsonify({'error': '初始化失败'}), 500
    except Exception as e:
        return jsonify({'error': f'初始化主题失败: {str(e)}'}), 500

@app.route('/api/token-stats', methods=['GET'])
def get_token_stats():
    """获取token消耗统计"""
    try:
        stats = token_tracker.get_session_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': f'获取token统计失败: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

