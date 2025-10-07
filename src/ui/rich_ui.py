"""
Rich终端UI模块 - 纯UI渲染，无业务逻辑
使用Rich库提供美观的终端界面，包括固定布局、进度条、实时统计和滚动日志
"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.layout import Layout
from rich.live import Live
from collections import deque
from datetime import datetime
import time
from typing import Dict, Any
from .progress import ProgressCallback


class RichUI(ProgressCallback):
    """Rich终端UI - 纯UI渲染，通过回调接收进度信息"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化Rich UI

        Args:
            config: 配置字典
        """
        self.console = Console()
        self.config = config
        self.video_info = {}
        self.stats = {
            'total_frames': 0,
            'processed_frames': 0,
            'frames_with_patterns': 0,
            'total_patterns_detected': 0,
            'ocr_calls': 0,
            'start_time': None,
            'phase_start_time': None,
        }
        self.logs = deque(maxlen=100)
        self.current_phase = "processing"
        self.phase_info = {
            'total_phases': 1,
            'current_phase': 1,
            'phase_name': '处理视频',
            'phase_total': 0,
            'phase_processed': 0
        }
        self.layout = None
        self.live = None

    def start_ui(self):
        """启动UI界面"""
        # 显示标题
        title = "[bold green]视频内容脱敏工具[/bold green]"
        if self.config.get('mode') == 'smart':
            title += " - [bold yellow]智能采样模式[/bold yellow]"

        self.console.print(Panel.fit(title, border_style="green"))
        self.console.print()

        # 创建布局
        self.layout = self._create_layout()

        # 启动Live显示
        self.live = Live(self.layout, console=self.console, refresh_per_second=4, screen=True)
        self.live.start()

    def stop_ui(self):
        """停止UI界面"""
        if self.live:
            self.live.stop()
            self.live = None

    # ========== ProgressCallback 接口实现 ==========

    def on_start(self, total_frames: int, fps: int, width: int, height: int):
        """处理开始"""
        self.video_info = {
            'width': width,
            'height': height,
            'fps': fps,
            'total_frames': total_frames,
            'duration': total_frames / fps if fps > 0 else 0
        }
        self.stats['total_frames'] = total_frames
        self.stats['start_time'] = time.time()
        self.stats['phase_start_time'] = time.time()

        self.phase_info['phase_total'] = total_frames
        self.phase_info['phase_processed'] = 0

        self.add_log(f"视频加载完成: {width}x{height}, {fps}FPS, {total_frames}帧", "success")
        self.add_log("开始处理视频...", "info")

        self._update_layout()

    def on_progress(self, current_frame: int, total_frames: int, phase: str = 'processing'):
        """进度更新"""
        self.stats['processed_frames'] = current_frame
        self.phase_info['phase_processed'] = current_frame
        self.current_phase = phase

        # 更新UI
        if self.layout:
            self._update_layout()

    def on_detected(self, frame_idx: int, text: str, confidence: float):
        """检测到目标内容"""
        self.stats['total_patterns_detected'] += 1
        self.add_log(f"帧 {frame_idx}: 检测到目标内容: {text} (置信度: {confidence:.2f})", "success")

    def on_log(self, message: str, level: str = 'info'):
        """添加日志"""
        self.add_log(message, level)

    def on_phase_change(self, phase: str, phase_num: int, total_phases: int):
        """阶段切换"""
        self.current_phase = phase
        self.phase_info = {
            'total_phases': total_phases,
            'current_phase': phase_num,
            'phase_name': phase,
            'phase_total': self.stats['total_frames'],
            'phase_processed': 0
        }
        self.stats['phase_start_time'] = time.time()
        self.stats['processed_frames'] = 0

        self.add_log(f"阶段 {phase_num}/{total_phases}: {phase}", "info")
        self._update_layout()

    def on_complete(self, stats: Dict[str, Any]):
        """处理完成"""
        elapsed = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        self.add_log(f"处理完成! 耗时: {elapsed:.2f}秒", "success")
        self.add_log(f"输出文件: {stats.get('output_path', '')}", "success")

        # 最后更新一次
        self._update_layout()

        # 停止UI
        self.stop_ui()

        # 显示最终统计
        self.console.print()
        self._show_final_stats(stats)

    def on_error(self, error: Exception):
        """错误处理"""
        self.add_log(f"错误: {str(error)}", "error")
        self.stop_ui()

    def on_ocr_call(self):
        """OCR调用时更新计数"""
        self.stats['ocr_calls'] += 1

    def on_blur(self, frame_idx: int, region_count: int):
        """打码时记录信息"""
        if region_count > 0:
            self.add_log(f"帧 {frame_idx}: 应用打码 ({region_count} 个区域)", "info")

    # ========== UI 渲染方法 ==========

    def add_log(self, message: str, level: str = "info"):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        if level == "success":
            style = "green"
            icon = "✓"
        elif level == "warning":
            style = "yellow"
            icon = "⚠"
        elif level == "error":
            style = "red"
            icon = "✗"
        else:
            style = "white"
            icon = "•"

        log_entry = f"[dim]{timestamp}[/dim] [{style}]{icon}[/{style}] {message}"
        self.logs.append(log_entry)

    def _create_config_panel(self) -> Panel:
        """创建配置信息面板"""
        table = Table.grid(padding=(0, 1))
        table.add_column(style="cyan", justify="right", no_wrap=True)
        table.add_column(style="white")

        table.add_row("输入文件", self.config.get('input_path', 'N/A'))
        table.add_row("输出文件", self.config.get('output_path', 'N/A'))

        # 处理模式
        mode_map = {
            'frame-by-frame': '逐帧处理',
            'smart': '智能采样'
        }
        mode_text = mode_map.get(self.config.get('mode', 'frame-by-frame'), '未知')
        table.add_row("处理模式", mode_text)

        # 打码方式
        blur_method = self.config.get('blur_method', 'gaussian')
        blur_method_map = {
            'gaussian': '高斯模糊',
            'pixelate': '像素化',
            'black': '黑色遮挡'
        }
        blur_text = blur_method_map.get(blur_method, blur_method)

        if blur_method == 'gaussian' and 'blur_strength' in self.config:
            blur_text += f" (强度: {self.config.get('blur_strength', 51)})"

        table.add_row("打码方式", blur_text)

        # 智能采样设置
        if self.config.get('mode') == 'smart':
            table.add_row("采样间隔", f"{self.config.get('sample_interval', 1.0)} 秒")
            buffer = self.config.get('buffer_time')
            if buffer is None:
                table.add_row("缓冲时间", "自动")
            else:
                table.add_row("缓冲时间", f"{buffer} 秒")

        table.add_row("设备", self.config.get('device', 'cpu'))
        table.add_row("精确定位", "✓ 是" if self.config.get('precise_location', False) else "✗ 否")

        return Panel(
            table,
            title="[bold cyan]配置信息[/bold cyan]",
            border_style="cyan",
            padding=(0, 1)
        )

    def _create_video_info_panel(self) -> Panel:
        """创建视频信息面板"""
        if not self.video_info:
            return Panel(
                "[dim]等待加载视频...[/dim]",
                title="[bold blue]视频信息[/bold blue]",
                border_style="blue",
                padding=(0, 1)
            )

        table = Table.grid(padding=(0, 1))
        table.add_column(style="cyan", justify="right", no_wrap=True)
        table.add_column(style="white")

        table.add_row("分辨率", f"{self.video_info['width']}x{self.video_info['height']}")
        table.add_row("帧率", f"{self.video_info['fps']} FPS")
        table.add_row("总帧数", f"{self.video_info['total_frames']:,}")

        duration = self.video_info['duration']
        minutes = int(duration // 60)
        seconds = duration % 60
        table.add_row("视频时长", f"{minutes}:{seconds:05.2f}")

        total_pixels = self.video_info['width'] * self.video_info['height']
        if total_pixels >= 1_000_000:
            pixels_text = f"{total_pixels / 1_000_000:.1f}M"
        else:
            pixels_text = f"{total_pixels / 1000:.1f}K"
        table.add_row("像素/帧", pixels_text)

        return Panel(
            table,
            title="[bold blue]视频信息[/bold blue]",
            border_style="blue",
            padding=(0, 1)
        )

    def _create_stats_panel(self) -> Panel:
        """创建实时统计面板"""
        table = Table.grid(padding=(0, 1))
        table.add_column(style="cyan", justify="right", no_wrap=True)
        table.add_column(style="white")

        processed = self.stats['processed_frames']
        total = self.stats['total_frames']

        # 计算速度和预计剩余时间
        if self.stats['phase_start_time']:
            elapsed = time.time() - self.stats['phase_start_time']
            fps = processed / elapsed if elapsed > 0 else 0

            if self.current_phase == "sampling":
                table.add_row("采样速度", f"{fps:.2f} FPS")
            elif self.current_phase == "blurring":
                table.add_row("打码速度", f"{fps:.2f} FPS")
            else:
                table.add_row("处理速度", f"{fps:.2f} FPS")

            if fps > 0 and total > 0:
                remaining = total - processed
                eta = remaining / fps
                table.add_row("预计剩余", f"{eta:.1f} 秒")

        # 根据阶段显示不同的统计
        if self.current_phase == "sampling":
            table.add_row("已扫描帧", f"{processed}/{total}")
            table.add_row("OCR 调用", str(self.stats['ocr_calls']))
            table.add_row("检测目标", f"{self.stats['total_patterns_detected']} 个")
        elif self.current_phase == "blurring":
            table.add_row("已处理", f"{processed}/{total}")
        else:
            table.add_row("已处理", f"{processed}/{total}")
            table.add_row("含目标内容", f"{self.stats['frames_with_patterns']} 帧")
            table.add_row("检测总数", f"{self.stats['total_patterns_detected']} 个")

        return Panel(
            table,
            title="[bold yellow]统计数据[/bold yellow]",
            border_style="yellow",
            padding=(0, 1)
        )

    def _create_logs_panel(self) -> Panel:
        """创建日志面板"""
        if not self.logs:
            content = Text("等待处理开始...", style="dim", justify="center")
        else:
            # 动态计算可显示的日志行数，根据终端高度自适应
            # 获取终端高度
            terminal_height = self.console.size.height

            # 终端高度 - header(9) - progress(4) - 面板边框和标题(4) - 统计面板最小空间
            available_height = terminal_height - 9 - 4 - 4

            # 确保至少显示5行，最多20行
            max_display_logs = max(5, min(20, available_height))

            display_logs = list(self.logs)[-max_display_logs:]
            content = "\n".join(display_logs)

        return Panel(
            content,
            title="[bold magenta]处理日志[/bold magenta]",
            border_style="magenta",
            padding=(0, 1)
        )

    def _create_progress_panel(self) -> Panel:
        """创建进度条面板"""
        processed = self.phase_info['phase_processed']
        total = self.phase_info['phase_total']

        if total == 0:
            percentage = 0
        else:
            percentage = (processed / total) * 100

        # 创建进度条
        bar_width = 40
        filled = int(bar_width * processed / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_width - filled)

        # 步骤信息
        step_info = ""
        if self.phase_info['total_phases'] > 1:
            step_info = f"步骤 {self.phase_info['current_phase']}/{self.phase_info['total_phases']}: "

        step_info += self.phase_info['phase_name']

        progress_text = f"{step_info}\n{bar} {processed}/{total} ({percentage:.1f}%)"

        if self.stats['start_time']:
            elapsed = time.time() - self.stats['start_time']
            progress_text += f" | 总用时: {elapsed:.1f}s"

        return Panel(
            Align.center(progress_text),
            title="[bold green]处理进度[/bold green]",
            border_style="green",
            padding=(0, 1)
        )

    def _create_layout(self) -> Layout:
        """创建固定窗口布局"""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=9),
            Layout(name="middle"),
            Layout(name="progress", size=4)
        )

        layout["header"].split_row(
            Layout(name="config"),
            Layout(name="video_info")
        )

        layout["middle"].split_row(
            Layout(name="stats", size=30),
            Layout(name="logs")
        )

        return layout

    def _update_layout(self):
        """更新布局内容"""
        if self.layout is None:
            return

        self.layout["config"].update(self._create_config_panel())
        self.layout["video_info"].update(self._create_video_info_panel())
        self.layout["stats"].update(self._create_stats_panel())
        self.layout["logs"].update(self._create_logs_panel())
        self.layout["progress"].update(self._create_progress_panel())

    def _show_final_stats(self, stats: Dict[str, Any]):
        """显示最终统计信息"""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan bold", justify="right")
        table.add_column(style="white")

        elapsed = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        avg_fps = stats.get('processed_frames', 0) / elapsed if elapsed > 0 else 0

        table.add_row("总帧数", str(stats.get('total_frames', 0)))
        table.add_row("扫描帧数", str(stats.get('processed_frames', 0)))
        table.add_row("检测帧数", f"{stats.get('frames_with_detections', 0)} 帧")
        table.add_row("检测总数", f"{stats.get('total_detections', 0)} 个")

        if 'ocr_calls' in stats:
            total_frames = stats.get('total_frames', 0)
            ocr_calls = stats['ocr_calls']
            speedup = total_frames / ocr_calls if ocr_calls > 0 else 0
            table.add_row("OCR调用", f"{ocr_calls} 次")
            table.add_row("节省调用", f"{total_frames - ocr_calls} 次")
            table.add_row("加速比", f"{speedup:.1f}x")

        if 'unique_detections' in stats and stats['unique_detections']:
            table.add_row("不重复目标内容", f"{len(stats['unique_detections'])} 个")
            table.add_row("目标内容列表", ", ".join(sorted(stats['unique_detections'])))

        table.add_row("处理时间", f"{elapsed:.2f} 秒")
        table.add_row("平均速度", f"{avg_fps:.2f} FPS")
        table.add_row("输出文件", stats.get('output_path', ''))

        title = "[bold green]✓ 处理完成[/bold green]"
        if self.config.get('mode') == 'smart':
            title += " [bold yellow](智能采样模式)[/bold yellow]"

        panel = Panel(
            table,
            title=title,
            border_style="green",
            padding=(1, 2)
        )
        self.console.print(panel)
