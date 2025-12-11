"""
LLM日志查看器：方便查看日志文件
"""
import os
import sys
from datetime import datetime


def view_log(log_file: str = None):
    """查看LLM调用日志"""
    if log_file is None:
        log_file = os.path.join(
            os.path.dirname(__file__),
            "..",
            "llm_calls.log"
        )
        log_file = os.path.abspath(log_file)
    
    if not os.path.exists(log_file):
        print(f"❌ 日志文件不存在: {log_file}")
        return
    
    print(f"📄 查看日志文件: {log_file}\n")
    print("="*80)
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    except Exception as e:
        print(f"❌ 读取日志文件失败: {e}")


def get_log_stats(log_file: str = None):
    """获取日志统计信息"""
    if log_file is None:
        log_file = os.path.join(
            os.path.dirname(__file__),
            "..",
            "llm_calls.log"
        )
        log_file = os.path.abspath(log_file)
    
    if not os.path.exists(log_file):
        print(f"❌ 日志文件不存在: {log_file}")
        return
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 统计调用次数
        call_count = content.count("📞 LLM API 调用 #")
        
        # 统计token数（从摘要中提取）
        total_tokens = 0
        if "总Token数:" in content:
            lines = content.split('\n')
            for line in lines:
                if "总Token数:" in line:
                    try:
                        total_tokens = int(line.split("总Token数:")[1].strip())
                    except:
                        pass
                    break
        
        # 获取文件信息
        file_size = os.path.getsize(log_file)
        file_size_mb = file_size / (1024 * 1024)
        mod_time = datetime.fromtimestamp(os.path.getmtime(log_file))
        
        print(f"📊 日志统计信息")
        print("="*80)
        print(f"文件路径: {log_file}")
        print(f"文件大小: {file_size_mb:.2f} MB")
        print(f"最后修改: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"调用次数: {call_count}")
        print(f"总Token数: {total_tokens}")
        print("="*80)
        
    except Exception as e:
        print(f"❌ 读取日志文件失败: {e}")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'stats':
            get_log_stats()
        elif sys.argv[1] == 'view':
            view_log()
        else:
            log_file = sys.argv[1]
            view_log(log_file)
    else:
        view_log()

