"""
使用示例脚本
演示如何使用智能体平台的API
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def create_character_example():
    """创建人物卡示例"""
    print("=== 创建人物卡 ===")
    character_data = {
        "name": "小助手",
        "description": """你是一个友好、乐于助人的AI助手。
性格特点：温和、耐心、专业
说话风格：使用礼貌用语，语气友好，会主动提供帮助
背景：拥有丰富的知识，喜欢解答各种问题""",
        "attributes": {
            "personality": "友好、耐心、专业",
            "style": "温和礼貌",
            "age": "未知",
            "role": "AI助手"
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/characters", json=character_data)
    if response.status_code == 201:
        character = response.json()
        print(f"✓ 人物卡创建成功！ID: {character['id']}")
        print(f"  名称: {character['name']}")
        return character['id']
    else:
        print(f"✗ 创建失败: {response.text}")
        return None

def chat_example(character_id):
    """对话示例"""
    print(f"\n=== 与角色对话 (ID: {character_id}) ===")
    
    messages = [
        "你好，请介绍一下自己",
        "你能帮我解决编程问题吗？",
        "谢谢你的帮助！"
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"\n[对话 {i}]")
        print(f"用户: {message}")
        
        chat_data = {
            "message": message,
            "platform": "deepseek"  # 可选：指定API平台
        }
        
        response = requests.post(
            f"{BASE_URL}/api/characters/{character_id}/chat",
            json=chat_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"角色: {result['response']}")
            if result.get('consistency_score'):
                print(f"一致性评分: {result['consistency_score']:.2f}")
                if result.get('consistency_feedback'):
                    print(f"检测反馈: {result['consistency_feedback'][:100]}...")
        else:
            print(f"✗ 对话失败: {response.text}")

def get_conversations_example(character_id):
    """获取对话历史示例"""
    print(f"\n=== 获取对话历史 (ID: {character_id}) ===")
    
    response = requests.get(f"{BASE_URL}/api/characters/{character_id}/conversations")
    if response.status_code == 200:
        conversations = response.json()
        print(f"共 {len(conversations)} 条对话记录")
        for conv in conversations[:3]:  # 只显示最近3条
            print(f"\n时间: {conv['created_at']}")
            print(f"用户: {conv['user_message']}")
            print(f"角色: {conv['character_response'][:50]}...")
    else:
        print(f"✗ 获取失败: {response.text}")

def main():
    """主函数"""
    print("智能体平台使用示例\n")
    
    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=2)
        if response.status_code != 200:
            print("✗ 服务未正常运行，请先启动 app.py")
            return
    except requests.exceptions.RequestException:
        print("✗ 无法连接到服务，请确保 app.py 正在运行")
        print("  启动命令: python app.py")
        return
    
    # 创建人物卡
    character_id = create_character_example()
    if not character_id:
        return
    
    # 进行对话
    chat_example(character_id)
    
    # 查看对话历史
    get_conversations_example(character_id)
    
    print("\n=== 示例完成 ===")

if __name__ == "__main__":
    main()

