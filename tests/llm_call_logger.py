"""
LLM调用记录器：记录和显示所有LLM API调用
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime


class LLMCallLogger:
    """LLM调用记录器"""
    
    def __init__(self, log_file: Optional[str] = None):
        self.calls: List[Dict] = []
        self.enabled = True
        self.log_file = log_file or os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "llm_calls.log"
        )
        self.log_file = os.path.abspath(self.log_file)
        self.current_test_module: Optional[str] = None
        self.current_test_name: Optional[str] = None
        self._ensure_log_dir()
    
    def set_test_context(self, test_module: str = None, test_name: str = None):
        """
        设置当前测试上下文
        
        Args:
            test_module: 测试模块名称（如 'test_agent', 'test_multi_agent_coordinator'）
            test_name: 测试方法名称（如 'test_agent_with_logging'）
        """
        self.current_test_module = test_module
        self.current_test_name = test_name
    
    def log_call(self, platform: str, messages: List[Dict], response: str, 
                 model: str = None, temperature: float = None, usage: Dict = None):
        """
        记录一次LLM调用
        
        Args:
            platform: API平台（deepseek/openai）
            messages: 发送的消息列表
            response: LLM返回的响应
            model: 使用的模型
            temperature: 温度参数
            usage: API返回的usage信息（包含真实token数）
        """
        if not self.enabled:
            return
        
        # 优先使用API返回的真实token数，否则估算
        if usage:
            input_tokens = usage.get('prompt_tokens', 0)
            output_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', input_tokens + output_tokens)
        else:
            # 计算token数（简单估算）
            input_tokens = self._estimate_tokens(messages)
            output_tokens = self._estimate_tokens([{"content": response}])
            total_tokens = input_tokens + output_tokens
        
        call_info = {
            "timestamp": datetime.now().isoformat(),
            "platform": platform,
            "model": model or "unknown",
            "temperature": temperature,
            "test_module": self.current_test_module,
            "test_name": self.current_test_name,
            "input": {
                "messages": messages,
                "token_count": input_tokens,
                "is_estimated": usage is None
            },
            "output": {
                "response": response,
                "token_count": output_tokens,
                "is_estimated": usage is None
            },
            "total_tokens": total_tokens,
            "usage": usage
        }
        
        self.calls.append(call_info)
        self._print_call(call_info)
        self._write_to_file(call_info)
    
    def _ensure_log_dir(self):
        """确保日志文件目录存在"""
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    
    def _write_to_file(self, call_info: Dict):
        """将调用信息写入文件"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write("\n" + "="*80 + "\n")
                f.write(f"📞 LLM API 调用 #{len(self.calls)}\n")
                f.write("="*80 + "\n")
                
                # 添加测试信息
                if call_info.get('test_module') or call_info.get('test_name'):
                    f.write(f"🧪 测试模块: {call_info.get('test_module', '未知')}\n")
                    if call_info.get('test_name'):
                        f.write(f"🧪 测试方法: {call_info.get('test_name')}\n")
                    f.write("-"*80 + "\n")
                
                f.write(f"⏰ 时间: {call_info['timestamp']}\n")
                f.write(f"🔧 平台: {call_info['platform']}\n")
                f.write(f"🤖 模型: {call_info['model']}\n")
                if call_info.get('temperature'):
                    f.write(f"🌡️  温度: {call_info['temperature']}\n")
                
                token_info = f"{call_info['input']['token_count']} tokens"
                if call_info['input'].get('is_estimated'):
                    token_info += " (估算)"
                else:
                    token_info += " (API返回)"
                f.write(f"\n📥 输入 ({token_info}):\n")
                f.write("-"*80 + "\n")
                
                for i, msg in enumerate(call_info['input']['messages'], 1):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    f.write(f"\n[{i}] {role.upper()}:\n")
                    f.write(content + "\n")
                
                token_info = f"{call_info['output']['token_count']} tokens"
                if call_info['output'].get('is_estimated'):
                    token_info += " (估算)"
                else:
                    token_info += " (API返回)"
                f.write(f"\n📤 输出 ({token_info}):\n")
                f.write("-"*80 + "\n")
                
                output = call_info['output']['response']
                f.write(output + "\n")
                
                f.write(f"\n📊 总计: {call_info['total_tokens']} tokens\n")
                f.write("="*80 + "\n")
        except Exception as e:
            print(f"⚠️  写入日志文件失败: {e}")
    
    def _estimate_tokens(self, messages: List[Dict]) -> int:
        """
        简单估算token数
        中文约1.5字符=1token，英文约4字符=1token
        """
        total_chars = 0
        for msg in messages:
            content = msg.get("content", "")
            total_chars += len(content)
        
        # 混合估算：假设平均2字符=1token
        return total_chars // 2
    
    def _print_call(self, call_info: Dict):
        """打印调用信息"""
        print("\n" + "="*80)
        print(f"📞 LLM API 调用 #{len(self.calls)}")
        print("="*80)
        
        # 添加测试信息
        if call_info.get('test_module') or call_info.get('test_name'):
            print(f"🧪 测试模块: {call_info.get('test_module', '未知')}")
            if call_info.get('test_name'):
                print(f"🧪 测试方法: {call_info.get('test_name')}")
            print("-"*80)
        
        print(f"⏰ 时间: {call_info['timestamp']}")
        print(f"🔧 平台: {call_info['platform']}")
        print(f"🤖 模型: {call_info['model']}")
        if call_info.get('temperature'):
            print(f"🌡️  温度: {call_info['temperature']}")
        token_info = f"{call_info['input']['token_count']} tokens"
        if call_info['input'].get('is_estimated'):
            token_info += " (估算)"
        else:
            token_info += " (API返回)"
        print(f"\n📥 输入 ({token_info}):")
        print("-"*80)
        
        for i, msg in enumerate(call_info['input']['messages'], 1):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            # 截断过长的内容（在合适的位置截断，避免截断代码块）
            if len(content) > 500:
                # 尝试在换行符后截断，如果没有则直接截断
                truncate_pos = 500
                if truncate_pos < len(content):
                    # 向前查找最近的换行符
                    for pos in range(truncate_pos, max(0, truncate_pos - 50), -1):
                        if content[pos] == '\n':
                            truncate_pos = pos + 1
                            break
                display_content = content[:truncate_pos] + f"\n\n... [内容过长，已截断，共{len(content)}字符]"
            else:
                display_content = content
            print(f"\n[{i}] {role.upper()}:")
            print(display_content)
        
        token_info = f"{call_info['output']['token_count']} tokens"
        if call_info['output'].get('is_estimated'):
            token_info += " (估算)"
        else:
            token_info += " (API返回)"
        print(f"\n📤 输出 ({token_info}):")
        print("-"*80)
        output = call_info['output']['response']
        if len(output) > 500:
            # 尝试在换行符后截断
            truncate_pos = 500
            if truncate_pos < len(output):
                # 向前查找最近的换行符
                for pos in range(truncate_pos, max(0, truncate_pos - 50), -1):
                    if output[pos] == '\n':
                        truncate_pos = pos + 1
                        break
            print(output[:truncate_pos] + f"\n\n... [内容过长，已截断，共{len(output)}字符]")
        else:
            print(output)
        
        print(f"\n📊 总计: {call_info['total_tokens']} tokens")
        print("="*80 + "\n")
    
    def get_summary(self) -> Dict:
        """获取调用摘要"""
        if not self.calls:
            return {
                "total_calls": 0,
                "total_tokens": 0,
                "platforms": {}
            }
        
        total_tokens = sum(call['total_tokens'] for call in self.calls)
        platforms = {}
        for call in self.calls:
            platform = call['platform']
            if platform not in platforms:
                platforms[platform] = {"calls": 0, "tokens": 0}
            platforms[platform]["calls"] += 1
            platforms[platform]["tokens"] += call['total_tokens']
        
        return {
            "total_calls": len(self.calls),
            "total_tokens": total_tokens,
            "platforms": platforms
        }
    
    def print_summary(self):
        """打印调用摘要"""
        summary = self.get_summary()
        summary_text = "\n" + "="*80 + "\n"
        summary_text += "📊 LLM API 调用摘要\n"
        summary_text += "="*80 + "\n"
        summary_text += f"总调用次数: {summary['total_calls']}\n"
        summary_text += f"总Token数: {summary['total_tokens']}\n"
        summary_text += "\n按平台统计:\n"
        for platform, stats in summary['platforms'].items():
            summary_text += f"  {platform}: {stats['calls']} 次调用, {stats['tokens']} tokens\n"
        summary_text += "="*80 + "\n"
        summary_text += f"📄 完整日志已保存到: {self.log_file}\n"
        summary_text += "="*80 + "\n"
        
        print(summary_text)
        
        # 同时写入文件
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(summary_text)
        except Exception as e:
            print(f"⚠️  写入摘要失败: {e}")
    
    def clear(self):
        """清空记录"""
        self.calls.clear()
        self.current_test_module = None
        self.current_test_name = None
        # 清空日志文件（可选，默认追加模式）
        # 如果需要每次测试都清空文件，取消下面的注释
        # try:
        #     if os.path.exists(self.log_file):
        #         os.remove(self.log_file)
        # except Exception:
        #     pass
    
    def disable(self):
        """禁用记录"""
        self.enabled = False
    
    def enable(self):
        """启用记录"""
        self.enabled = True


# 全局记录器实例
logger = LLMCallLogger()

