import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///agent_platform.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 主题（剧本）配置文件夹
    CHARACTER_CONFIG_DIR = os.getenv('CHARACTER_CONFIG_DIR', 'themes')
    
    # 存档文件夹
    SAVE_DIR = os.getenv('SAVE_DIR', 'save')
    
    # API配置
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    DEEPSEEK_API_BASE = os.getenv('DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1')
    
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_API_BASE = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
    
    AIZEX_API_KEY = os.getenv('AIZEX_API_KEY', '')
    AIZEX_API_BASE = os.getenv('AIZEX_API_BASE', 'https://aizex.top/v1')
    
    # 默认使用的API平台
    DEFAULT_API_PLATFORM = os.getenv('DEFAULT_API_PLATFORM', 'aizex')
    
    # 模型配置（每个平台使用的模型）
    DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat-v3')  # 更新为最新模型
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    AIZEX_MODEL = os.getenv('AIZEX_MODEL', 'deepseek-v3-0324')
    
    # 一致性检测配置
    CONSISTENCY_CHECK_ENABLED = os.getenv('CONSISTENCY_CHECK_ENABLED', 'true').lower() == 'true'
    CONSISTENCY_CHECK_API = os.getenv('CONSISTENCY_CHECK_API', 'deepseek')  # 用于检测的API平台
    
    # 剧本系统配置
    SCRIPT_SYSTEM_ENABLED = os.getenv('SCRIPT_SYSTEM_ENABLED', 'true').lower() == 'true'
    SCENARIOS_DIR = 'scenarios'  # 场景剧本目录名

