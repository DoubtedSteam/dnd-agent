"""
命令行界面（CLI）：通过终端使用智能体平台
"""
import os
import sys
import json
import requests
import time
import threading
from typing import Optional
from tqdm import tqdm
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.live import Live
from rich.panel import Panel


class AgentCLI:
    """智能体平台命令行界面"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:5000"):
        self.base_url = base_url
        self.current_theme = None  # 启动时不设置默认主题
        self.current_step = "0_step"
        self.player_role = None
        self.console = Console()
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        self.characters_dir = os.path.join(self.base_dir, "characters")
    
    def _make_request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json=data)
            else:
                return {"error": f"不支持的HTTP方法: {method}"}
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            return {"error": "无法连接到服务器，请确保服务器正在运行"}
        except requests.exceptions.HTTPError as e:
            try:
                error_data = response.json()
                return error_data
            except:
                return {"error": f"HTTP错误: {e}"}
        except Exception as e:
            return {"error": f"请求失败: {str(e)}"}
    
    def execute_instruction(self, instruction: str, theme: Optional[str] = None, 
                           save_step: Optional[str] = None) -> dict:
        """执行指令"""
        theme = theme or self.current_theme
        save_step = save_step or self.current_step
        
        data = {
            "instruction": instruction,
            "save_step": save_step,
            "platform": "deepseek"
        }
        
        if self.player_role:
            data["player_role"] = self.player_role
        
        # 显示进度条（显示真实执行步骤）
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            # 创建多个任务，每个任务代表一个执行步骤
            tasks = {
                'load': progress.add_task("[cyan]1. 加载场景和角色...", total=100),
                'agents': progress.add_task("[cyan]2. 调用智能体生成响应...", total=100),
                'analyze': progress.add_task("[cyan]3. 分析环境变化...", total=100),
                'update': progress.add_task("[cyan]4. 更新状态和存档...", total=100),
                'format': progress.add_task("[cyan]5. 格式化响应...", total=100)
            }
            
            # 在后台线程中执行请求
            result = {"error": None}
            exception = None
            start_time = time.time()
            
            def make_request():
                nonlocal result, exception
                try:
                    # 发送请求
                    result = self._make_request("POST", f"/api/themes/{theme}/execute", data)
                    
                except Exception as e:
                    exception = e
            
            thread = threading.Thread(target=make_request)
            thread.start()
            
            # 在等待期间，显示加载步骤（这个步骤很快）
            progress.update(tasks['load'], completed=100)
            
            # 等待API返回
            elapsed = 0
            while thread.is_alive():
                time.sleep(0.2)
                elapsed += 0.2
                # 在等待期间，模拟智能体调用的进度（因为这是最耗时的步骤）
                if tasks['agents'] in progress.tasks:
                    current = progress.tasks[tasks['agents']].completed
                    if current < 95:  # 最多到95%，等待实际完成
                        # 模拟进度：前30秒快速增长，之后缓慢增长
                        if elapsed < 30:
                            progress.update(tasks['agents'], advance=3)
                        else:
                            progress.update(tasks['agents'], advance=1)
            
            thread.join()
            
            # API调用完成，根据返回的耗时信息更新进度
            if "error" not in result and "step_timings" in result:
                timings = result["step_timings"]
                total_time = timings.get('total', 1.0)  # 避免除零
                
                # 根据实际耗时比例更新进度
                # 步骤2：智能体响应
                agents_time = timings.get('agents', 0)
                progress.update(tasks['agents'], completed=100)
                time.sleep(0.1)
                
                # 步骤3：分析环境变化
                analyze_time = timings.get('analyze', 0)
                if analyze_time > 0:
                    # 模拟分析过程的进度
                    steps = max(5, int(analyze_time * 10))  # 根据实际耗时决定步数
                    for i in range(steps):
                        time.sleep(analyze_time / steps)
                        progress.update(tasks['analyze'], completed=int((i + 1) * 100 / steps))
                else:
                    progress.update(tasks['analyze'], completed=100)
                time.sleep(0.1)
                
                # 步骤4：更新状态
                update_time = timings.get('update', 0)
                if update_time > 0:
                    time.sleep(update_time)
                progress.update(tasks['update'], completed=100)
                time.sleep(0.1)
                
                # 步骤5：格式化响应
                format_time = timings.get('format', 0)
                if format_time > 0:
                    # 模拟格式化过程的进度
                    steps = max(5, int(format_time * 10))
                    for i in range(steps):
                        time.sleep(format_time / steps)
                        progress.update(tasks['format'], completed=int((i + 1) * 100 / steps))
                else:
                    progress.update(tasks['format'], completed=100)
            else:
                # 如果没有耗时信息，快速完成所有步骤
                progress.update(tasks['agents'], completed=100)
                time.sleep(0.2)
                progress.update(tasks['analyze'], completed=100)
                time.sleep(0.1)
                progress.update(tasks['update'], completed=100)
                time.sleep(0.1)
                progress.update(tasks['format'], completed=100)
            
            if exception:
                raise exception
        
        # 如果创建了新步骤，更新当前步骤
        if "new_step" in result:
            self.current_step = result["new_step"]
            self.console.print(f"\n[green]✅ 已创建新存档步骤: {result['new_step']}[/green]")
        
        return result
    
    def ask_question(self, question: str, theme: Optional[str] = None,
                    save_step: Optional[str] = None) -> dict:
        """提问"""
        theme = theme or self.current_theme
        save_step = save_step or self.current_step
        
        data = {
            "question": question,
            "save_step": save_step,
            "platform": "deepseek"
        }
        
        if self.player_role:
            data["player_role"] = self.player_role
        
        # 显示进度条
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task(
                "[cyan]正在思考并回答问题...",
                total=100
            )
            
            # 在后台线程中执行请求
            result = {"error": None}
            exception = None
            
            def make_request():
                nonlocal result, exception
                try:
                    result = self._make_request("POST", f"/api/themes/{theme}/question", data)
                except Exception as e:
                    exception = e
            
            thread = threading.Thread(target=make_request)
            thread.start()
            
            # 模拟进度
            elapsed = 0
            while thread.is_alive():
                time.sleep(0.1)
                elapsed += 0.1
                # 提问通常比执行指令快
                if elapsed < 10:
                    progress.update(task, advance=5)
                else:
                    progress.update(task, advance=2)
                if progress.tasks[task].completed >= 100:
                    progress.update(task, completed=99)
            
            thread.join()
            progress.update(task, completed=100)
            
            if exception:
                raise exception
        
        return result
    
    def list_characters(self, theme: Optional[str] = None) -> list:
        """列出所有角色"""
        result = self._make_request("GET", "/api/characters")
        if "error" in result:
            return []
        
        if theme:
            return [c for c in result if c.get('theme') == theme]
        return result
    
    def list_themes(self) -> list:
        """列出所有可用的主题（剧本）"""
        result = self._make_request("GET", "/api/themes")
        if "error" in result:
            return []
        return result.get('themes', [])
    
    def get_character(self, character_id: str) -> dict:
        """获取角色信息"""
        return self._make_request("GET", f"/api/characters/{character_id}")
    
    def health_check(self) -> bool:
        """检查服务器状态"""
        result = self._make_request("GET", "/api/health")
        return result.get("status") == "ok"
    
    def get_token_stats(self) -> dict:
        """获取token消耗统计"""
        return self._make_request("GET", "/api/token-stats")
    
    def get_background_intro(self, theme: str) -> Optional[str]:
        """读取主题的背景介绍"""
        scene_path = os.path.join(self.characters_dir, theme, "SCENE.md")
        if not os.path.exists(scene_path):
            return None
        
        try:
            with open(scene_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 提取背景介绍部分
            # 查找 "## 背景介绍（启动时输出）" 到下一个 "##" 之间的内容
            start_marker = "## 背景介绍（启动时输出）"
            start_idx = content.find(start_marker)
            if start_idx == -1:
                return None
            
            # 找到下一个 "##" 的位置
            next_section_idx = content.find("\n## ", start_idx + len(start_marker))
            if next_section_idx == -1:
                # 如果没有下一个章节，取到文件末尾
                intro = content[start_idx + len(start_marker):].strip()
            else:
                intro = content[start_idx + len(start_marker):next_section_idx].strip()
            
            # 清理多余的换行和空白
            lines = [line.strip() for line in intro.split('\n') if line.strip()]
            return '\n'.join(lines)
        except Exception as e:
            return None
    
    def print_background_intro(self, theme: str):
        """打印主题的背景介绍"""
        intro = self.get_background_intro(theme)
        if intro:
            self.console.print("\n" + "="*80)
            self.console.print("[bold cyan]📖 背景介绍[/bold cyan]")
            self.console.print("="*80)
            self.console.print(f"\n{intro}\n")
            self.console.print("="*80 + "\n")


def print_help():
    """打印帮助信息"""
    help_text = """
=== 智能体平台 CLI 使用指南 ===

基本命令：
  execute <指令>          - 执行指令，推进游戏（简写: e）
  question <问题>         - 提问，不推进游戏（简写: ask）
  list                    - 列出所有角色（简写: ls）
  themes                  - 列出所有可用的主题（剧本）
  char <角色ID>           - 查看角色信息
  theme <主题>            - 切换主题（简写: t）
  step <步骤>             - 切换存档步骤（简写: st）
  role <角色>             - 设置玩家角色（简写: r）
  status                  - 显示当前状态（简写: s）
  tokens                  - 显示token消耗统计
  saves                   - 列出所有存档步骤
  clean <step>            - 删除指定存档步骤
  clean all               - 删除所有存档步骤（保留0_step）
  clean theme             - 删除当前主题的所有存档
  help                    - 显示帮助信息（简写: h）
  exit/quit/q             - 退出程序

示例：
  > execute 我们出发去遗迹
  > question 队伍现在有多少人？
  > list
  > themes                 - 查看所有可用剧本
  > char hero
  > theme adventure_party
  > step 1_step
  > role 冒险者小队队长

提示：
  - 使用 execute 执行指令会推进游戏并创建新存档步骤
  - 使用 question 提问会检查一致性并可能创建新步骤
  - 指令必须执行，但可能因为环境因素而失败（如"爬上去"可能因为墙壁太滑而失败）
  - 执行结果会显示成功/失败状态和实际结果
  - 当前主题和步骤会自动保存，下次启动时使用
"""
    print(help_text)


def print_status(cli: AgentCLI):
    """打印当前状态"""
    console = cli.console
    console.print(f"\n[bold]当前状态：[/bold]")
    if cli.current_theme:
        console.print(f"  [bold]主题:[/bold] {cli.current_theme}")
    else:
        console.print(f"  [bold]主题:[/bold] [dim]（未选择，使用 'theme <主题名>' 选择剧本）[/dim]")
    console.print(f"  [bold]存档步骤:[/bold] {cli.current_step}")
    if cli.player_role:
        console.print(f"  [bold]玩家角色:[/bold] {cli.player_role}")
    else:
        console.print(f"  [bold]玩家角色:[/bold] [dim]（未设置，将从场景中提取）[/dim]")
    
    # 检查服务器状态
    if cli.health_check():
        console.print(f"  [bold]服务器:[/bold] [green]✅ 运行中[/green]")
    else:
        console.print(f"  [bold]服务器:[/bold] [red]❌ 未连接[/red]")
    
    # 显示token统计（简要）
    try:
        stats = cli.get_token_stats()
        if "error" not in stats:
            total_tokens = stats.get('total_tokens', 0)
            total_calls = stats.get('total_calls', 0)
            if total_tokens > 0:
                console.print(f"  [bold]Token消耗:[/bold] {total_tokens:,} tokens ({total_calls} 次调用)")
    except:
        pass


def print_execute_result(result: dict, console: Console):
    """打印执行结果"""
    if "error" in result:
        console.print(f"\n[red]❌ 错误: {result['error']}[/red]")
        return
    
    console.print("\n" + "="*80)
    console.print("[bold cyan]📋 执行结果[/bold cyan]")
    console.print("="*80)
    
    # 显示格式化后的响应
    if "surface" in result and "responses" in result["surface"]:
        console.print("\n[bold]【角色响应】[/bold]")
        for resp in result["surface"]["responses"]:
            char_name = resp.get('character_name', '未知')
            response_text = resp.get('formatted_text', resp.get('response', ''))
            console.print(f"\n[bold yellow]{char_name}:[/bold yellow]")
            console.print(f"  {response_text}")
        
        if result["surface"].get("summary"):
            console.print(f"\n[bold]【摘要】[/bold]")
            console.print(f"  {result['surface']['summary']}")
    
    # 显示执行结果（从hidden中的execution_results获取）
    if "hidden" in result and "execution_results" in result["hidden"]:
        execution_results = result["hidden"]["execution_results"]
        if execution_results:
            console.print(f"\n[bold]【执行结果】[/bold]")
            for exec_res in execution_results:
                char_name = exec_res.get('character_name', '未知')
                exec_result = exec_res.get('execution_result', {})
                success = exec_result.get('success', True)
                outcome = exec_result.get('actual_outcome', '')
                failure_reason = exec_result.get('failure_reason', '')
                
                if success:
                    if outcome:
                        console.print(f"  [green]✅ {char_name}:[/green] {outcome}")
                else:
                    console.print(f"  [red]❌ {char_name}:[/red] {failure_reason or '执行失败'}")
                    if outcome:
                        console.print(f"    [dim]实际结果: {outcome}[/dim]")
    
    # 显示新步骤
    if "new_step" in result:
        console.print(f"\n[green]✅ 新存档步骤: {result['new_step']}[/green]")


def print_question_result(result: dict, console: Console):
    """打印提问结果"""
    if "error" in result:
        console.print(f"\n[red]❌ 错误: {result['error']}[/red]")
        return
    
    console.print("\n" + "="*80)
    console.print("[bold cyan]❓ 问题回答[/bold cyan]")
    console.print("="*80)
    console.print(f"\n[bold]问题:[/bold] {result.get('question', '')}")
    console.print(f"\n[bold]回答:[/bold]\n{result.get('answer', '')}")
    
    # 显示一致性检查结果
    if "consistency_check" in result:
        consistency = result["consistency_check"]
        score = consistency.get('score', 0)
        feedback = consistency.get('feedback', '')
        
        console.print(f"\n[bold]一致性检查:[/bold]")
        if score >= 0.7:
            console.print(f"  [green]✅ 评分: {score:.2f}[/green]")
        else:
            console.print(f"  [red]❌ 评分: {score:.2f} (未通过，未创建新步骤)[/red]")
        if feedback:
            console.print(f"  [dim]{feedback}[/dim]")
    
    # 显示新步骤
    if "new_step" in result:
        console.print(f"\n[green]✅ 新存档步骤: {result['new_step']}[/green]")


def print_characters(characters: list, console: Console):
    """打印角色列表"""
    if not characters:
        console.print("\n[yellow]没有找到角色[/yellow]")
        return
    
    console.print("\n" + "="*80)
    console.print("[bold cyan]📋 角色列表[/bold cyan]")
    console.print("="*80)
    for char in characters:
        console.print(f"\n  [bold]ID:[/bold] {char.get('id', '未知')}")
        console.print(f"  [bold]名称:[/bold] {char.get('name', '未知')}")
        console.print(f"  [bold]主题:[/bold] {char.get('theme', '未知')}")


def print_character_info(char: dict, console: Console):
    """打印角色信息"""
    if "error" in char:
        console.print(f"\n[red]❌ 错误: {char['error']}[/red]")
        return
    
    console.print("\n" + "="*80)
    console.print(f"[bold cyan]📋 角色信息: {char.get('name', '未知')}[/bold cyan]")
    console.print("="*80)
    console.print(f"\n[bold]ID:[/bold] {char.get('id', '未知')}")
    console.print(f"[bold]名称:[/bold] {char.get('name', '未知')}")
    console.print(f"[bold]主题:[/bold] {char.get('theme', '未知')}")
    console.print(f"\n[bold]描述:[/bold]\n{char.get('description', '无')}")
    
    if char.get('attributes'):
        console.print(f"\n[bold]属性:[/bold]")
        attrs = char['attributes']
        if 'vitals' in attrs:
            vitals = attrs['vitals']
            console.print(f"  [green]生命值:[/green] {vitals.get('hp', '?')}")
            console.print(f"  [blue]魔法值:[/blue] {vitals.get('mp', '?')}")
            console.print(f"  [yellow]体力值:[/yellow] {vitals.get('stamina', '?')}")

def print_themes(themes: list, console: Console, current_theme: str):
    """打印主题列表"""
    if not themes:
        console.print("\n[yellow]没有找到可用的主题[/yellow]")
        return
    
    console.print("\n" + "="*80)
    console.print("[bold cyan]📋 可用主题（剧本）列表[/bold cyan]")
    console.print("="*80)
    for theme in themes:
        if theme == current_theme:
            console.print(f"\n  [bold green]✓ {theme}[/bold green] [dim](当前)[/dim]")
        else:
            console.print(f"\n  {theme}")
    console.print(f"\n[dim]使用 'theme <主题名>' 切换主题[/dim]")

def print_saves(saves: dict, console: Console, current_theme: str):
    """打印存档列表"""
    if "error" in saves:
        console.print(f"\n[red]❌ 错误: {saves['error']}[/red]")
        return
    
    steps = saves.get('steps', [])
    if not steps:
        console.print("\n[yellow]没有找到存档步骤[/yellow]")
        return
    
    console.print("\n" + "="*80)
    console.print(f"[bold cyan]💾 存档列表 ({current_theme})[/bold cyan]")
    console.print("="*80)
    
    total_size = 0
    for step_info in steps:
        step = step_info.get('step', '未知')
        size_mb = step_info.get('size_mb', 0)
        total_size += size_mb
        
        # 这里需要从CLI获取当前步骤，暂时不标记
        console.print(f"\n  {step} - {size_mb} MB")
    
    console.print(f"\n[bold]总大小:[/bold] {total_size:.2f} MB")
    console.print(f"\n[dim]使用 'clean <step>' 删除指定步骤[/dim]")
    console.print(f"[dim]使用 'clean all' 删除所有步骤（保留0_step）[/dim]")
    console.print(f"[dim]使用 'clean theme' 删除当前主题的所有存档[/dim]")

def print_token_stats(stats: dict, console: Console):
    """打印token消耗统计"""
    if "error" in stats:
        console.print(f"\n[red]❌ 错误: {stats['error']}[/red]")
        return
    
    console.print("\n" + "="*80)
    console.print("[bold cyan]📊 Token消耗统计[/bold cyan]")
    console.print("="*80)
    
    total_calls = stats.get('total_calls', 0)
    total_tokens = stats.get('total_tokens', 0)
    total_input = stats.get('total_input_tokens', 0)
    total_output = stats.get('total_output_tokens', 0)
    
    console.print(f"\n[bold]总调用次数:[/bold] {total_calls}")
    console.print(f"[bold]总Token数:[/bold] {total_tokens:,}")
    console.print(f"  [dim]输入Token:[/dim] {total_input:,}")
    console.print(f"  [dim]输出Token:[/dim] {total_output:,}")
    
    # 按平台统计
    by_platform = stats.get('by_platform', {})
    if by_platform:
        console.print(f"\n[bold]按平台统计:[/bold]")
        for platform, data in by_platform.items():
            console.print(f"  [cyan]{platform}:[/cyan] {data['calls']} 次调用, {data['tokens']:,} tokens")
    
    # 按操作类型统计
    by_operation = stats.get('by_operation', {})
    if by_operation:
        console.print(f"\n[bold]按操作类型统计:[/bold]")
        operation_names = {
            'chat': '对话',
            'agent_response': '智能体响应',
            'consistency_check': '一致性检查',
            'question_answer': '问题回答',
            'environment_analysis': '环境分析',
            'response_formatting': '响应格式化'
        }
        for operation, data in sorted(by_operation.items(), key=lambda x: x[1]['tokens'], reverse=True):
            name = operation_names.get(operation, operation)
            console.print(f"  [yellow]{name}:[/yellow] {data['calls']} 次调用, {data['tokens']:,} tokens")
    
    # 会话时长
    duration = stats.get('session_duration', 0)
    if duration > 0:
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        console.print(f"\n[dim]会话时长:[/dim] {minutes}分{seconds}秒")


def main():
    """主函数"""
    console = Console()
    console.print("="*80)
    console.print("[bold cyan]🤖 智能体平台 CLI[/bold cyan]")
    console.print("="*80)
    console.print("\n[cyan]正在连接服务器...[/cyan]")
    
    cli = AgentCLI()
    
    # 检查服务器状态
    if not cli.health_check():
        console.print("[red]❌ 无法连接到服务器[/red]")
        console.print(f"[yellow]请确保服务器正在运行: python app.py[/yellow]")
        console.print(f"[dim]服务器地址: {cli.base_url}[/dim]")
        sys.exit(1)
    
    console.print("[green]✅ 服务器连接成功[/green]")
    
    # 列出可用主题，但不自动选择
    themes = cli.list_themes()
    if themes:
        console.print(f"\n[cyan]可用主题（剧本）：[/cyan]")
        for i, theme in enumerate(themes, 1):
            console.print(f"  {i}. {theme}")
        console.print("\n[dim]使用 'theme <主题名>' 选择并进入剧本[/dim]")
    else:
        console.print("\n[yellow]⚠️  没有找到可用的主题（剧本）[/yellow]")
    
    print_help()
    print_status(cli)
    
    # 主循环
    while True:
        try:
            # 获取用户输入
            if cli.current_theme:
                prompt = f"\n[{cli.current_theme}/{cli.current_step}] > "
            else:
                prompt = "\n[未选择剧本] > "
            user_input = input(prompt).strip()
            
            if not user_input:
                continue
            
            # 解析命令
            parts = user_input.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            if command in ["exit", "quit", "q"]:
                print("\n再见！")
                break
            
            elif command == "help" or command == "h":
                print_help()
            
            elif command == "status" or command == "s":
                print_status(cli)
            
            elif command == "tokens" or command == "token":
                stats = cli.get_token_stats()
                print_token_stats(stats, cli.console)
            
            elif command == "saves" or command == "save":
                if not cli.current_theme:
                    cli.console.print("[red]❌ 请先选择剧本，使用 'theme <主题名>' 选择[/red]")
                    continue
                saves = cli.list_saves()
                print_saves(saves, cli.console, cli.current_theme, cli.current_step)
            
            elif command == "clean" or command == "clear":
                if not cli.current_theme:
                    cli.console.print("[red]❌ 请先选择剧本，使用 'theme <主题名>' 选择[/red]")
                    continue
                if not args:
                    cli.console.print("[yellow]请指定要清理的内容[/yellow]")
                    cli.console.print("[dim]用法: clean <step> - 删除指定步骤[/dim]")
                    cli.console.print("[dim]      clean all - 删除所有步骤（保留0_step）[/dim]")
                    cli.console.print("[dim]      clean theme - 删除当前主题的所有存档[/dim]")
                    continue
                
                if args == "all":
                    # 确认删除
                    cli.console.print("[yellow]⚠️  警告：将删除所有存档步骤（保留0_step）[/yellow]")
                    confirm = input("确认删除？(yes/no): ").strip().lower()
                    if confirm == "yes":
                        result = cli.delete_all_saves()
                        if "error" in result:
                            cli.console.print(f"[red]❌ 错误: {result['error']}[/red]")
                        else:
                            cli.console.print(f"[green]✅ {result.get('message', '删除完成')}[/green]")
                            if result.get('deleted'):
                                cli.console.print(f"[dim]已删除: {', '.join(result['deleted'])}[/dim]")
                    else:
                        cli.console.print("[yellow]已取消[/yellow]")
                elif args == "theme":
                    # 确认删除
                    cli.console.print(f"[red]⚠️  警告：将删除主题 '{cli.current_theme}' 的所有存档[/red]")
                    confirm = input("确认删除？(yes/no): ").strip().lower()
                    if confirm == "yes":
                        result = cli.delete_theme_saves()
                        if "error" in result:
                            cli.console.print(f"[red]❌ 错误: {result['error']}[/red]")
                        else:
                            cli.console.print(f"[green]✅ {result.get('message', '删除完成')}[/green]")
                    else:
                        cli.console.print("[yellow]已取消[/yellow]")
                else:
                    # 删除指定步骤
                    step = args
                    result = cli.delete_save(step=step)
                    if "error" in result:
                        cli.console.print(f"[red]❌ 错误: {result['error']}[/red]")
                    else:
                        cli.console.print(f"[green]✅ {result.get('message', '删除完成')}[/green]")
                        if step == cli.current_step:
                            cli.current_step = "0_step"
                            cli.console.print(f"[yellow]当前步骤已重置为: 0_step[/yellow]")
            
            elif command == "execute" or command == "e":
                if not cli.current_theme:
                    cli.console.print("[red]❌ 请先选择剧本，使用 'theme <主题名>' 选择[/red]")
                    continue
                if not args:
                    cli.console.print("[red]❌ 请提供指令，例如: execute 我们出发[/red]")
                    continue
                cli.console.print(f"\n[cyan]⏳ 执行指令: {args}[/cyan]")
                result = cli.execute_instruction(args)
                print_execute_result(result, cli.console)
            
            elif command == "question" or command == "ask":
                if not cli.current_theme:
                    cli.console.print("[red]❌ 请先选择剧本，使用 'theme <主题名>' 选择[/red]")
                    continue
                if not args:
                    cli.console.print("[red]❌ 请提供问题，例如: question 队伍现在有多少人？[/red]")
                    continue
                cli.console.print(f"\n[cyan]⏳ 正在回答问题...[/cyan]")
                result = cli.ask_question(args)
                print_question_result(result, cli.console)
                
                # 如果创建了新步骤，更新当前步骤
                if "new_step" in result:
                    cli.current_step = result["new_step"]
                    cli.console.print(f"\n[green]✅ 已创建新存档步骤: {result['new_step']}[/green]")
                
                # 显示一致性检查结果
                if "consistency_check" in result:
                    consistency = result["consistency_check"]
                    score = consistency.get('score', 0)
                    feedback = consistency.get('feedback', '')
                    cli.console.print(f"\n[bold]一致性检查:[/bold]")
                    if score >= 0.7:
                        cli.console.print(f"  [green]评分: {score:.2f}[/green]")
                    else:
                        cli.console.print(f"  [red]评分: {score:.2f} (未通过)[/red]")
                    if feedback:
                        cli.console.print(f"  [dim]{feedback}[/dim]")
            
            elif command == "list" or command == "ls":
                if not cli.current_theme:
                    cli.console.print("[red]❌ 请先选择剧本，使用 'theme <主题名>' 选择[/red]")
                    continue
                characters = cli.list_characters(cli.current_theme)
                print_characters(characters, cli.console)
            
            elif command == "themes":
                themes = cli.list_themes()
                print_themes(themes, cli.console, cli.current_theme)
            
            elif command == "char" or command == "character":
                if not args:
                    cli.console.print("[red]❌ 请提供角色ID，例如: char hero[/red]")
                    continue
                char = cli.get_character(args)
                print_character_info(char, cli.console)
            
            elif command == "theme" or command == "t":
                if not args:
                    cli.console.print(f"[cyan]当前主题: {cli.current_theme}[/cyan]")
                    themes = cli.list_themes()
                    if themes:
                        cli.console.print(f"\n[cyan]可用主题：[/cyan]")
                        for theme in themes:
                            if theme == cli.current_theme:
                                cli.console.print(f"  [bold green]✓ {theme}[/bold green] [dim](当前)[/dim]")
                            else:
                                cli.console.print(f"  {theme}")
                    continue
                
                # 验证主题是否存在
                themes = cli.list_themes()
                if args not in themes:
                    cli.console.print(f"[red]❌ 主题 '{args}' 不存在[/red]")
                    if themes:
                        cli.console.print(f"[cyan]可用主题：[/cyan]")
                        for theme in themes:
                            cli.console.print(f"  {theme}")
                    continue
                
                cli.current_theme = args
                cli.current_step = "0_step"  # 切换主题时重置到初始步骤
                cli.console.print(f"[green]✅ 已切换到主题: {cli.current_theme}[/green]")
                cli.console.print(f"[dim]存档步骤已重置为: 0_step[/dim]")
                
                # 输出背景介绍
                cli.print_background_intro(cli.current_theme)
            
            elif command == "step" or command == "st":
                if not args:
                    cli.console.print(f"[cyan]当前存档步骤: {cli.current_step}[/cyan]")
                    continue
                cli.current_step = args
                cli.console.print(f"[green]✅ 已切换到存档步骤: {cli.current_step}[/green]")
            
            elif command == "role" or command == "r":
                if not args:
                    if cli.player_role:
                        cli.console.print(f"[cyan]当前玩家角色: {cli.player_role}[/cyan]")
                    else:
                        cli.console.print("[dim]玩家角色: （未设置）[/dim]")
                    continue
                cli.player_role = args
                cli.console.print(f"[green]✅ 已设置玩家角色: {cli.player_role}[/green]")
            
            else:
                cli.console.print(f"[red]❌ 未知命令: {command}[/red]")
                cli.console.print("[dim]输入 'help' 查看帮助[/dim]")
        
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")


if __name__ == "__main__":
    main()

