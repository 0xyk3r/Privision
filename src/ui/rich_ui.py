"""
Rich终端UI模块
使用Rich库提供终端界面
"""
import time
from collections import deque
from datetime import datetime
from typing import Dict, Any

from rich.align import Align
from rich.box import ROUNDED, DOUBLE, HEAVY
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TaskProgressColumn, TimeRemainingColumn, \
    MofNCompleteColumn
from rich.table import Table
from rich.text import Text

from .progress import ProgressCallback


class RichUI(ProgressCallback):
    """Rich终端UI"""

    # 配色方案
    COLORS = {
        'primary': '#00D9FF',  # 青蓝色（主色）
        'secondary': '#FF6B9D',  # 粉红色（次要）
        'success': '#00FF88',  # 亮绿色
        'warning': '#FFD93D',  # 金黄色
        'error': '#FF5555',  # 红色
        'info': '#8BE9FD',  # 浅蓝色
        'accent': '#BD93F9',  # 紫色
        'muted': '#6272A4',  # 灰蓝色
    }

    # 图标集
    ICONS = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': '💬',
        'rocket': '🚀',
        'star': '⭐',
        'gear': '⚙️',
        'clock': '⏱️',
        'chart': '📊',
        'eye': '👁️',
        'film': '🎬',
        'zap': '⚡',
        'target': '🎯',
        'fire': '🔥',
    }

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
        self.logs = deque(maxlen=150)
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
        self.progress = None
        self.main_task_id = None
        self.phase_task_id = None

    def start_ui(self):
        """启动UI界面"""
        # 清屏
        self.console.clear()

        # 显示启动提示
        self._show_startup_animation()

    def _start_live_display(self):
        """启动Live显示"""
        if self.live is not None:
            return  # 已经启动

        # 清屏准备显示主布局
        self.console.clear()

        # 创建进度条组件
        self.progress = Progress(
            SpinnerColumn(spinner_name="dots12", style=self.COLORS['primary']),
            TextColumn("[bold]{task.description}", style=self.COLORS['primary']),
            BarColumn(
                style=self.COLORS['primary'],
                complete_style=self.COLORS['success'],
                finished_style=self.COLORS['success'],
                pulse_style=self.COLORS['accent'],
                bar_width=None  # 自动宽度
            ),
            TaskProgressColumn(),
            TextColumn("•"),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            expand=True  # 扩展以填充可用空间
        )

        # 创建布局
        self.layout = self._create_layout()

        # 填充初始内容
        self._update_layout()

        # 启动Live显示
        self.live = Live(
            self.layout,
            console=self.console,
            refresh_per_second=10,  # 刷新频率
            screen=True,  # 全屏模式
            redirect_stdout=False,  # 不重定向标准输出
            redirect_stderr=False  # 不重定向标准错误
        )
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

        self.add_log(f"视频加载完成: {width}x{height} @ {fps}FPS, 共 {total_frames:,} 帧", "success")
        self.add_log("开始处理视频...", "info")

        # 启动Live显示
        self._start_live_display()

        # 创建主进度任务
        if self.progress:
            self.main_task_id = self.progress.add_task(
                f"[{self.COLORS['primary']}]总体进度",
                total=total_frames
            )

        self._update_layout()

    def on_progress(self, current_frame: int, total_frames: int, phase: str = 'processing'):
        """进度更新"""
        self.stats['processed_frames'] = current_frame
        self.phase_info['phase_processed'] = current_frame
        self.current_phase = phase

        # 更新进度条
        if self.progress and self.main_task_id is not None:
            self.progress.update(self.main_task_id, completed=current_frame)

        # 更新UI
        if self.layout:
            self._update_layout()

    def on_detected(self, frame_idx: int, text: str, confidence: float):
        """检测到目标内容"""
        self.stats['total_patterns_detected'] += 1
        self.add_log(
            f"帧 {frame_idx:,}: 检测到目标 '{text}' (置信度: {confidence:.2%})",
            "success"
        )

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

        # 更新进度条描述
        if self.progress and self.main_task_id is not None:
            phase_colors = {
                'sampling': self.COLORS['info'],
                'blurring': self.COLORS['warning'],
                'processing': self.COLORS['primary']
            }
            color = phase_colors.get(phase, self.COLORS['primary'])
            self.progress.update(
                self.main_task_id,
                description=f"[{color}]{phase}",
                completed=0
            )

        self._update_layout()

    def on_complete(self, stats: Dict[str, Any]):
        """处理完成"""
        elapsed = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        self.add_log(f"处理完成! 总耗时: {elapsed:.2f} 秒", "success")
        self.add_log(f"输出文件: {stats.get('output_path', '')}", "success")

        # 完成进度条
        if self.progress and self.main_task_id is not None:
            self.progress.update(self.main_task_id, completed=self.stats['total_frames'])

        # 最后更新一次
        self._update_layout()

        # 停止UI
        self.stop_ui()

        # 显示完成动画
        self._show_completion_animation()

        # 显示最终统计
        self.console.print()
        self._show_final_stats(stats)

    def on_error(self, error: Exception):
        """错误处理"""
        self.add_log(f"错误: {str(error)}", "error")
        self.stop_ui()

        # 显示错误面板
        self.console.print()
        error_panel = Panel(
            f"[{self.COLORS['error']}]{self.ICONS['error']} {str(error)}[/]",
            title=f"[bold {self.COLORS['error']}]处理失败[/]",
            border_style=self.COLORS['error'],
            box=HEAVY
        )
        self.console.print(error_panel)

    def on_ocr_call(self):
        """OCR调用时更新计数"""
        self.stats['ocr_calls'] += 1

    def on_blur(self, frame_idx: int, region_count: int):
        """打码时记录信息"""
        if region_count > 0:
            self.add_log(f"帧 {frame_idx:,}: 应用打码 ({region_count} 个区域)", "info")

    # ========== UI 渲染方法 ==========

    def add_log(self, message: str, level: str = "info"):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        level_config = {
            "success": (self.COLORS['success'], self.ICONS['success']),
            "warning": (self.COLORS['warning'], self.ICONS['warning']),
            "error": (self.COLORS['error'], self.ICONS['error']),
            "info": (self.COLORS['info'], self.ICONS['info']),
        }

        color, icon = level_config.get(level, (self.COLORS['muted'], self.ICONS['info']))

        log_entry = f"[dim]{timestamp}[/dim] [{color}]{icon}[/] {message}"
        self.logs.append(log_entry)

    def _show_startup_animation(self):
        """显示启动动画"""
        title_art = """
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   ██████╗ ██████╗ ██╗██╗   ██╗██╗███████╗██╗ ██████╗ ███╗   ██╗   ║
║   ██╔══██╗██╔══██╗██║██║   ██║██║██╔════╝██║██╔═══██╗████╗  ██║   ║
║   ██████╔╝██████╔╝██║██║   ██║██║███████╗██║██║   ██║██╔██╗ ██║   ║
║   ██╔═══╝ ██╔══██╗██║╚██╗ ██╔╝██║╚════██║██║██║   ██║██║╚██╗██║   ║
║   ██║     ██║  ██║██║ ╚████╔╝ ██║███████║██║╚██████╔╝██║ ╚████║   ║
║   ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚═╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ║
║                                                                   ║
║                        视频内容智能脱敏工具                       ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
        """

        # 为标题添加渐变色
        lines = title_art.strip().split('\n')
        styled_title = Text()

        for i, line in enumerate(lines):
            # 渐变从青色到紫色
            if i < len(lines) // 2:
                color = self.COLORS['primary']
            else:
                color = self.COLORS['accent']
            styled_title.append(line + "\n", style=color)

        self.console.print(Align.center(styled_title))

        # 显示模式信息
        mode_text = Text()
        mode_text.append(f"\n{self.ICONS['rocket']} ", style=self.COLORS['warning'])

        if self.config.get('mode') == 'smart':
            mode_text.append("智能采样模式", style=f"bold {self.COLORS['warning']}")
        else:
            mode_text.append("标准处理模式", style=f"bold {self.COLORS['primary']}")

        mode_text.append(f" {self.ICONS['zap']}\n", style=self.COLORS['warning'])
        self.console.print(Align.center(mode_text))
        time.sleep(2.5)

    def _show_completion_animation(self):
        """显示完成动画"""
        completion_text = Text()
        completion_text.append("处理完成", style=f"bold {self.COLORS['success']}")

        self.console.print(Align.center(completion_text))

    def _create_config_panel(self) -> Panel:
        """创建配置信息面板"""
        table = Table.grid(padding=(0, 2), expand=False)
        table.add_column(style=f"{self.COLORS['muted']}", justify="right", no_wrap=True)
        table.add_column(style="white", overflow="fold")

        # 文件路径（截断过长路径）
        input_path = self.config.get('input_path', 'N/A')
        output_path = self.config.get('output_path', 'N/A')

        table.add_row(
            "输入",
            self._truncate_path(input_path, 40)
        )
        table.add_row(
            "输出",
            self._truncate_path(output_path, 40)
        )

        # 处理模式
        mode_map = {
            'frame-by-frame': ('逐帧处理', self.COLORS['primary']),
            'smart': ('智能采样', self.COLORS['warning'])
        }
        mode_text, mode_color = mode_map.get(
            self.config.get('mode', 'frame-by-frame'),
            ('未知', self.COLORS['muted'])
        )
        table.add_row(
            "模式",
            f"[{mode_color}]{mode_text}[/]"
        )

        # 打码方式
        blur_method = self.config.get('blur_method', 'gaussian')
        blur_method_map = {
            'gaussian': '高斯模糊',
            'pixelate': '像素化',
            'black': '黑色遮挡'
        }
        blur_text = blur_method_map.get(blur_method, blur_method)

        if blur_method == 'gaussian' and 'blur_strength' in self.config:
            blur_text += f" [{self.COLORS['muted']}](强度: {self.config.get('blur_strength', 51)})[/]"

        table.add_row("打码", blur_text)

        # 智能采样设置
        if self.config.get('mode') == 'smart':
            buffer = self.config.get('buffer_time')
            buffer_text = "自动" if buffer is None else f"{buffer}s"
            table.add_row(
                "采样/缓冲",
                f"{self.config.get('sample_interval', 1.0)}s / {buffer_text}"
            )

        # 设备和精确定位
        device_text = self.config.get('device', 'cpu').upper()
        device_color = self.COLORS['success'] if 'cuda' in device_text.lower() else self.COLORS['info']
        precise = "✓" if self.config.get('precise_location', False) else "✗"
        table.add_row(
            "设备/精确",
            f"[{device_color}]{device_text}[/] / {precise}"
        )

        return Panel(
            table,
            title=f"[bold {self.COLORS['primary']}]配置信息[/]",
            border_style=self.COLORS['primary'],
            box=ROUNDED,
            padding=(0, 1)
        )

    def _create_video_info_panel(self) -> Panel:
        """创建视频信息面板"""
        if not self.video_info:
            return Panel(
                Align.center(f"[{self.COLORS['muted']}]等待加载视频...[/]"),
                title=f"[bold {self.COLORS['info']}]视频信息[/]",
                border_style=self.COLORS['info'],
                box=ROUNDED,
                padding=(0, 1)
            )

        table = Table.grid(padding=(0, 2), expand=False)
        table.add_column(style=f"{self.COLORS['muted']}", justify="right")
        table.add_column(style="white")

        # 分辨率
        width = self.video_info['width']
        height = self.video_info['height']
        resolution_text = f"{width:,} × {height:,}"

        # 判断分辨率等级
        total_pixels = width * height
        if total_pixels >= 3840 * 2160:  # 4K
            res_tag = f"[{self.COLORS['accent']}]4K+[/]"
        elif total_pixels >= 1920 * 1080:  # FHD
            res_tag = f"[{self.COLORS['success']}]FHD[/]"
        elif total_pixels >= 1280 * 720:  # HD
            res_tag = f"[{self.COLORS['warning']}]HD[/]"
        else:
            res_tag = f"[{self.COLORS['muted']}]SD[/]"

        table.add_row("分辨率", f"{resolution_text} {res_tag}")

        # 帧率
        fps = self.video_info['fps']
        fps_color = self.COLORS['success'] if fps >= 60 else self.COLORS['info']
        table.add_row("帧率", f"[{fps_color}]{fps:.2f} FPS[/]")

        # 总帧数
        table.add_row("总帧数", f"{self.video_info['total_frames']:,}")

        # 视频时长
        duration = self.video_info['duration']
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = duration % 60

        if hours > 0:
            duration_text = f"{hours}:{minutes:02d}:{seconds:05.2f}"
        else:
            duration_text = f"{minutes}:{seconds:05.2f}"

        table.add_row("时长", duration_text)

        # 像素统计
        if total_pixels >= 1_000_000:
            pixels_text = f"{total_pixels / 1_000_000:.1f}M"
        else:
            pixels_text = f"{total_pixels / 1000:.1f}K"
        table.add_row("像素/帧", pixels_text)

        return Panel(
            table,
            title=f"[bold {self.COLORS['info']}]视频信息[/]",
            border_style=self.COLORS['info'],
            box=ROUNDED,
            padding=(0, 1)
        )

    def _create_stats_panel(self) -> Panel:
        """创建实时统计面板"""
        table = Table.grid(padding=(0, 2), expand=False)
        table.add_column(style=f"{self.COLORS['muted']}", justify="right")
        table.add_column(style="white")

        processed = self.stats['processed_frames']
        total = self.stats['total_frames']

        # 计算速度和预计剩余时间
        if self.stats['phase_start_time']:
            elapsed = time.time() - self.stats['phase_start_time']
            fps = processed / elapsed if elapsed > 0 else 0

            # 速度指示器
            if fps > 60:
                speed_color = self.COLORS['success']
            elif fps > 30:
                speed_color = self.COLORS['warning']
            else:
                speed_color = self.COLORS['info']

            phase_names = {
                "sampling": "采样速度",
                "blurring": "打码速度",
                "processing": "处理速度"
            }
            speed_name = phase_names.get(self.current_phase, "处理速度")

            table.add_row(
                speed_name,
                f"[{speed_color}]{fps:.2f} FPS[/]"
            )

            # 预计剩余时间
            if fps > 0 and total > 0:
                remaining = total - processed
                eta = remaining / fps

                if eta > 60:
                    eta_text = f"{int(eta // 60)}分{int(eta % 60)}秒"
                else:
                    eta_text = f"{eta:.1f}秒"

                table.add_row(
                    "预计剩余",
                    f"[{self.COLORS['accent']}]{eta_text}[/]"
                )

        # 根据阶段显示不同的统计
        if self.current_phase == "sampling":
            completion = (processed / total * 100) if total > 0 else 0
            table.add_row(
                "已扫描",
                f"{processed:,} / {total:,} [{self.COLORS['muted']}]({completion:.1f}%)[/]"
            )
            table.add_row(
                "OCR 调用",
                f"[{self.COLORS['warning']}]{self.stats['ocr_calls']:,}[/]"
            )

            # 节省调用次数
            if total > 0 and self.stats['ocr_calls'] > 0:
                saved = processed - self.stats['ocr_calls']
                # 加速比 = 已处理帧数 / 实际OCR调用次数
                speedup = processed / self.stats['ocr_calls']
                table.add_row(
                    "节省调用",
                    f"[{self.COLORS['success']}]{saved:,} ({speedup:.1f}x)[/]"
                )

            table.add_row(
                "检测目标",
                f"[{self.COLORS['success']}]{self.stats['total_patterns_detected']:,}[/]"
            )
        elif self.current_phase == "blurring":
            completion = (processed / total * 100) if total > 0 else 0
            table.add_row(
                "已打码",
                f"{processed:,} / {total:,} [{self.COLORS['muted']}]({completion:.1f}%)[/]"
            )
        else:
            completion = (processed / total * 100) if total > 0 else 0
            table.add_row(
                "已处理",
                f"{processed:,} / {total:,} [{self.COLORS['muted']}]({completion:.1f}%)[/]"
            )
            table.add_row(
                "含目标帧",
                f"[{self.COLORS['warning']}]{self.stats['frames_with_patterns']:,}[/]"
            )
            table.add_row(
                "检测总数",
                f"[{self.COLORS['success']}]{self.stats['total_patterns_detected']:,}[/]"
            )

        return Panel(
            table,
            title=f"[bold {self.COLORS['accent']}]统计数据[/]",
            border_style=self.COLORS['accent'],
            box=ROUNDED,
            padding=(0, 1)
        )

    def _create_logs_panel(self) -> Panel:
        """创建日志面板"""
        if not self.logs:
            content = Align.center(
                f"[{self.COLORS['muted']}]等待处理开始...[/]",
                vertical="middle"
            )
        else:
            # 动态计算可显示的日志行数
            terminal_height = self.console.size.height

            # 计算其他区域占用的高度
            # header区域：9行
            # progress区域：3行
            # 面板边框和间距：约3行
            reserved_height = 9 + 3 + 3

            # 可用于显示日志的高度
            available_height = max(5, terminal_height - reserved_height)

            # 获取最新的日志
            display_logs = list(self.logs)[-available_height:]

            content = "\n".join(display_logs)

        return Panel(
            content,
            title=f"[bold {self.COLORS['secondary']}]处理日志[/]",
            border_style=self.COLORS['secondary'],
            box=ROUNDED,
            padding=(0, 1),
            height=None
        )

    def _create_progress_panel(self) -> Panel:
        """创建进度条面板"""
        if self.progress:
            # 使用 Rich Progress 组件
            content = self.progress
        else:
            # 备用简单进度条
            processed = self.phase_info['phase_processed']
            total = self.phase_info['phase_total']
            percentage = (processed / total * 100) if total > 0 else 0

            # 动态计算进度条宽度（终端宽度 - 边框和边距）
            terminal_width = self.console.size.width
            bar_width = max(20, terminal_width - 30)  # 减去边框、标题、百分比等占用的空间

            filled = int(bar_width * processed / total) if total > 0 else 0
            bar = "█" * filled + "░" * (bar_width - filled)

            content = f"{bar} {percentage:.1f}%"

        return Panel(
            content,
            title=f"[bold {self.COLORS['success']}]处理进度[/]",
            border_style=self.COLORS['success'],
            box=ROUNDED,
            padding=(0, 1)
        )

    def _create_layout(self) -> Layout:
        """创建固定窗口布局"""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=9),  # 头部区域
            Layout(name="middle"),  # 中间区域
            Layout(name="progress", size=3)  # 进度条区域
        )

        layout["header"].split_row(
            Layout(name="config"),
            Layout(name="video_info")
        )

        layout["middle"].split_row(
            Layout(name="stats", ratio=1, minimum_size=15),
            Layout(name="logs", ratio=3, minimum_size=30)
        )

        return layout

    def _update_layout(self):
        """更新布局内容"""
        if self.layout is None:
            return

        try:
            self.layout["config"].update(self._create_config_panel())
            self.layout["video_info"].update(self._create_video_info_panel())
            self.layout["stats"].update(self._create_stats_panel())
            self.layout["logs"].update(self._create_logs_panel())
            self.layout["progress"].update(self._create_progress_panel())
        except Exception:
            # 忽略布局更新错误，避免中断主流程
            pass

    def _show_final_stats(self, stats: Dict[str, Any]):
        """显示最终统计信息"""
        # 创建统计表格
        table = Table(
            show_header=False,
            box=DOUBLE,
            border_style=self.COLORS['success'],
            padding=(0, 2)
        )
        table.add_column(style=f"bold {self.COLORS['muted']}", justify="right")
        table.add_column(style="white")

        elapsed = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        avg_fps = stats.get('processed_frames', 0) / elapsed if elapsed > 0 else 0

        # 基本统计
        table.add_row(
            "总帧数",
            f"{stats.get('total_frames', 0):,}"
        )
        table.add_row(
            "扫描帧数",
            f"{stats.get('processed_frames', 0):,}"
        )
        table.add_row(
            "检测帧数",
            f"[{self.COLORS['warning']}]{stats.get('frames_with_detections', 0):,}[/]"
        )
        table.add_row(
            "检测总数",
            f"[{self.COLORS['success']}]{stats.get('total_detections', 0):,}[/]"
        )

        # 智能采样统计
        if 'ocr_calls' in stats:
            processed_frames = stats.get('processed_frames', 0)
            ocr_calls = stats['ocr_calls']
            speedup = processed_frames / ocr_calls if ocr_calls > 0 else 0
            saved = processed_frames - ocr_calls

            table.add_row(
                "OCR调用",
                f"[{self.COLORS['warning']}]{ocr_calls:,}[/]"
            )
            table.add_row(
                "节省调用",
                f"[{self.COLORS['success']}]{saved:,}[/]"
            )
            table.add_row(
                "加速比",
                f"[bold {self.COLORS['accent']}]{speedup:.1f}x[/]"
            )

        # 不重复目标内容
        if 'unique_detections' in stats and stats['unique_detections']:
            unique_count = len(stats['unique_detections'])
            table.add_row(
                "不重复目标",
                f"[{self.COLORS['info']}]{unique_count}[/]"
            )

            # 显示目标列表（限制长度）
            targets = sorted(stats['unique_detections'])
            targets_text = ", ".join(targets[:5])
            if len(targets) > 5:
                targets_text += f" ... (共{len(targets)}个)"
            table.add_row(
                "目标列表",
                f"[{self.COLORS['muted']}]{targets_text}[/]"
            )

        # 性能统计
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = elapsed % 60

        if hours > 0:
            time_text = f"{hours}:{minutes:02d}:{seconds:05.2f}"
        else:
            time_text = f"{minutes}:{seconds:05.2f}"

        table.add_row(
            "处理时间",
            f"[{self.COLORS['accent']}]{time_text}[/]"
        )

        speed_color = self.COLORS['success'] if avg_fps > 30 else self.COLORS['warning']
        table.add_row(
            "平均速度",
            f"[{speed_color}]{avg_fps:.2f} FPS[/]"
        )

        # 输出文件
        output_path = stats.get('output_path', '')
        table.add_row(
            "输出文件",
            f"[{self.COLORS['info']}]{self._truncate_path(output_path, 50)}[/]"
        )

        # 创建标题
        title = Text()
        title.append(f"{self.ICONS['star']} ", style=self.COLORS['success'])
        title.append("处理完成", style=f"bold {self.COLORS['success']}")
        title.append(f" {self.ICONS['star']}", style=self.COLORS['success'])

        if self.config.get('mode') == 'smart':
            title.append(f"  {self.ICONS['rocket']} ", style=self.COLORS['warning'])
            title.append("智能采样模式", style=f"bold {self.COLORS['warning']}")

        # 显示面板
        panel = Panel(
            table,
            title=title,
            border_style=self.COLORS['success'],
            box=DOUBLE,
            padding=(1, 2)
        )
        self.console.print(panel)

    @staticmethod
    def _truncate_path(path: str, max_length: int) -> str:
        """截断过长的路径"""
        if len(path) <= max_length:
            return path

        # 保留开头和结尾
        if '/' in path or '\\' in path:
            parts = path.replace('\\', '/').split('/')
            filename = parts[-1]

            if len(filename) > max_length - 10:
                return f"...{filename[-(max_length - 10):]}"

            remaining = max_length - len(filename) - 6  # 6 for ".../" and "/"
            prefix = '/'.join(parts[:-1])

            if len(prefix) > remaining:
                prefix = prefix[:remaining]

            return f"{prefix}/.../{filename}"

        # 简单截断
        half = (max_length - 3) // 2
        return f"{path[:half]}...{path[-half:]}"
