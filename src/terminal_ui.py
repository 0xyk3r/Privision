"""
终端UI模块
使用Rich库提供美观的终端界面，包括固定布局、进度条、实时统计和滚动日志
"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TimeElapsedColumn
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from collections import deque
from datetime import datetime
import time


class VideoProcessorUI:
    """视频处理器终端UI - 提供固定布局和实时进度显示"""

    def __init__(self):
        """初始化UI组件"""
        self.console = Console()
        self.config = {}
        self.video_info = {}
        self.stats = {
            'total_frames': 0,
            'processed_frames': 0,
            'frames_with_phones': 0,
            'total_phones_detected': 0,
            'ocr_calls': 0,
            'start_time': None,
            'phase_start_time': None,
        }
        self.logs = deque(maxlen=100)  # 最多保留100条日志
        self.progress_text = ""
        self.current_phase = "processing"  # processing, sampling, blurring
        self.phase_info = {
            'total_phases': 1,
            'current_phase': 1,
            'phase_name': '处理视频',
            'phase_total': 0,
            'phase_processed': 0
        }

    def set_config(self, config: dict):
        """设置配置信息"""
        self.config = config

    def set_video_info(self, width: int, height: int, fps: int, total_frames: int):
        """设置视频信息"""
        self.video_info = {
            'width': width,
            'height': height,
            'fps': fps,
            'total_frames': total_frames,
            'duration': total_frames / fps if fps > 0 else 0
        }
        self.stats['total_frames'] = total_frames

    def add_log(self, message: str, level: str = "info"):
        """
        添加日志消息

        Args:
            message: 日志内容
            level: 日志级别 (info, success, warning, error)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 根据级别选择样式
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

    def create_config_panel(self) -> Panel:
        """创建配置信息面板（左上角）"""
        table = Table.grid(padding=(0, 1))
        table.add_column(style="cyan", justify="right", no_wrap=True)
        table.add_column(style="white")

        table.add_row("输入文件", self.config.get('input', 'N/A'))
        table.add_row("输出文件", self.config.get('output', 'N/A'))

        # 打码方式（合并模糊强度）
        blur_method = self.config.get('blur_method', 'gaussian')
        blur_method_map = {
            'gaussian': '高斯模糊',
            'pixelate': '像素化',
            'black': '黑色遮挡'
        }
        blur_text = blur_method_map.get(blur_method, blur_method)

        # 只有高斯模糊才显示强度
        if blur_method == 'gaussian' and 'blur_strength' in self.config:
            blur_text += f" (强度: {self.config.get('blur_strength', 51)})"

        table.add_row("打码方式", blur_text)

        if 'sample_interval' in self.config:
            table.add_row("采样间隔", f"{self.config.get('sample_interval', 1.0)} 秒")

        if 'buffer_time' in self.config:
            buffer = self.config.get('buffer_time')
            if buffer is None:
                table.add_row("缓冲时间", "自动")
            else:
                table.add_row("缓冲时间", f"{buffer} 秒")

        table.add_row("GPU 加速", "✓ 是" if self.config.get('use_gpu', False) else "✗ 否")

        return Panel(
            table,
            title="[bold cyan]配置信息[/bold cyan]",
            border_style="cyan",
            padding=(0, 1)
        )

    def create_video_info_panel(self) -> Panel:
        """创建视频信息面板（右上角）"""
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

        # 基本信息
        table.add_row("分辨率", f"{self.video_info['width']}x{self.video_info['height']}")
        table.add_row("帧率", f"{self.video_info['fps']} FPS")
        table.add_row("总帧数", f"{self.video_info['total_frames']:,}")

        # 时长信息（格式化为 分:秒）
        duration = self.video_info['duration']
        minutes = int(duration // 60)
        seconds = duration % 60
        table.add_row("视频时长", f"{minutes}:{seconds:05.2f}")

        # 计算像素总数
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

    def create_stats_panel(self) -> Panel:
        """创建实时统计面板"""
        table = Table.grid(padding=(0, 1))
        table.add_column(style="cyan", justify="right", no_wrap=True)
        table.add_column(style="white")

        # 根据当前阶段显示不同的统计信息
        if self.current_phase == "sampling":
            # 采样阶段
            processed = self.stats['processed_frames']
            total = self.stats['total_frames']

            if self.stats['phase_start_time']:
                elapsed = time.time() - self.stats['phase_start_time']
                fps = processed / elapsed if elapsed > 0 else 0
                table.add_row("采样速度", f"{fps:.2f} FPS")

                if fps > 0:
                    remaining = total - processed
                    eta = remaining / fps
                    table.add_row("预计剩余", f"{eta:.1f} 秒")

            table.add_row("已扫描帧", f"{processed}/{total}")
            table.add_row("OCR调用", str(self.stats['ocr_calls']))
            table.add_row("发现手机号", f"{self.stats['total_phones_detected']} 个")

        elif self.current_phase == "blurring":
            # 打码阶段
            processed = self.stats['processed_frames']
            total = self.stats['total_frames']

            if self.stats['phase_start_time']:
                elapsed = time.time() - self.stats['phase_start_time']
                fps = processed / elapsed if elapsed > 0 else 0
                table.add_row("打码速度", f"{fps:.2f} FPS")

                if fps > 0:
                    remaining = total - processed
                    eta = remaining / fps
                    table.add_row("预计剩余", f"{eta:.1f} 秒")

            table.add_row("已处理", f"{processed}/{total}")
            table.add_row("已打码", f"{self.stats['frames_with_phones']} 帧")

        else:
            # 普通处理阶段
            processed = self.stats['processed_frames']
            total = self.stats['total_frames']

            if self.stats['start_time']:
                elapsed = time.time() - self.stats['start_time']
                fps = processed / elapsed if elapsed > 0 else 0
                table.add_row("处理速度", f"{fps:.2f} FPS")

                if fps > 0:
                    remaining = total - processed
                    eta = remaining / fps
                    table.add_row("预计剩余", f"{eta:.1f} 秒")

            table.add_row("已处理", f"{processed}/{total}")
            table.add_row("含手机号", f"{self.stats['frames_with_phones']} 帧")
            table.add_row("检测总数", f"{self.stats['total_phones_detected']} 个")

        return Panel(
            table,
            title="[bold yellow]统计数据[/bold yellow]",
            border_style="yellow",
            padding=(0, 1)
        )

    def create_logs_panel(self) -> Panel:
        """创建日志面板（中间可滚动区域）"""
        if not self.logs:
            content = Text("等待处理开始...", style="dim", justify="center")
        else:
            # 只显示最后N条日志，以实现滚动效果
            # 根据面板大小，通常显示最后15-20条即可
            max_display_logs = 20
            display_logs = list(self.logs)[-max_display_logs:]
            content = "\n".join(display_logs)

        return Panel(
            content,
            title="[bold magenta]处理日志[/bold magenta]",
            border_style="magenta",
            padding=(0, 1)
        )

    def create_progress_panel(self) -> Panel:
        """创建进度条面板（底部）"""
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

    def create_layout(self) -> Layout:
        """创建固定窗口布局"""
        # 主布局
        layout = Layout()

        # 顶部分为左右两部分
        layout.split_column(
            Layout(name="header", size=8),    # 顶部信息区
            Layout(name="middle"),             # 中间区域（统计+日志）
            Layout(name="progress", size=4)   # 底部进度条
        )

        # 顶部左右分割
        layout["header"].split_row(
            Layout(name="config"),     # 左：配置信息
            Layout(name="video_info")  # 右：视频信息
        )

        # 中间区域分为统计和日志
        layout["middle"].split_row(
            Layout(name="stats", size=30),  # 左：统计信息
            Layout(name="logs")              # 右：日志列表
        )

        return layout

    def update_layout(self, layout: Layout):
        """更新布局内容"""
        layout["config"].update(self.create_config_panel())
        layout["video_info"].update(self.create_video_info_panel())
        layout["stats"].update(self.create_stats_panel())
        layout["logs"].update(self.create_logs_panel())
        layout["progress"].update(self.create_progress_panel())

    def process_video_with_ui(
        self,
        video_processor,
        input_path: str,
        output_path: str
    ) -> dict:
        """
        使用UI界面处理视频

        Args:
            video_processor: VideoProcessor实例
            input_path: 输入视频路径
            output_path: 输出视频路径

        Returns:
            处理统计信息字典
        """
        import cv2
        from pathlib import Path

        # 显示标题
        self.console.print(Panel.fit(
            "[bold green]视频手机号脱敏工具[/bold green]",
            border_style="green"
        ))
        self.console.print()

        # 打开输入视频
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {input_path}")

        # 获取视频属性
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # 设置视频信息
        self.set_video_info(width, height, fps, total_frames)
        self.add_log(f"视频加载完成: {width}x{height}, {fps}FPS, {total_frames}帧", "success")

        # 创建输出目录
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 创建视频写入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        if not out.isOpened():
            cap.release()
            raise ValueError(f"无法创建输出视频文件: {output_path}")

        self.add_log("开始处理视频...", "info")

        # 初始化统计和阶段信息
        self.stats['start_time'] = time.time()
        self.current_phase = "processing"
        self.phase_info = {
            'total_phases': 1,
            'current_phase': 1,
            'phase_name': '处理视频',
            'phase_total': total_frames,
            'phase_processed': 0
        }

        # 创建布局
        layout = self.create_layout()

        # 检测回调函数
        def on_detection(text: str, confidence: float):
            self.stats['total_phones_detected'] += 1
            self.add_log(f"检测到手机号: {text} (置信度: {confidence:.2f})", "success")

        # 使用Live创建实时更新界面
        with Live(layout, console=self.console, refresh_per_second=4, screen=True):
            frame_idx = 0
            last_log_frame = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_idx += 1

                # 处理当前帧
                processed_frame, phone_count = video_processor.process_frame(
                    frame,
                    detection_callback=on_detection
                )

                # 写入输出视频
                out.write(processed_frame)

                # 更新统计
                self.stats['processed_frames'] = frame_idx
                self.phase_info['phase_processed'] = frame_idx
                if phone_count > 0:
                    self.stats['frames_with_phones'] += 1

                # 每处理30帧添加一条日志
                if frame_idx - last_log_frame >= 30:
                    percentage = (frame_idx / total_frames) * 100
                    self.add_log(f"处理进度: {frame_idx}/{total_frames} ({percentage:.1f}%)", "info")
                    last_log_frame = frame_idx

                # 更新布局
                self.update_layout(layout)

        # 释放资源
        cap.release()
        out.release()

        # 显示完成信息
        elapsed = time.time() - self.stats['start_time']
        self.add_log(f"处理完成! 耗时: {elapsed:.2f}秒", "success")
        self.add_log(f"输出文件: {output_path}", "success")

        # 最后更新一次布局显示完成状态
        self.update_layout(layout)

        # 显示最终统计
        self.console.print()
        self.show_final_stats(output_path)

        return {
            'total_frames': self.stats['total_frames'],
            'processed_frames': self.stats['processed_frames'],
            'frames_with_phones': self.stats['frames_with_phones'],
            'total_phones_detected': self.stats['total_phones_detected'],
            'ocr_calls': self.stats.get('ocr_calls', self.stats['processed_frames'])
        }

    def process_smart_video_with_ui(
        self,
        smart_processor,
        input_path: str,
        output_path: str
    ) -> dict:
        """
        使用UI界面处理视频（智能采样模式）

        Args:
            smart_processor: SmartVideoProcessor实例
            input_path: 输入视频路径
            output_path: 输出视频路径

        Returns:
            处理统计信息字典
        """
        import cv2
        from pathlib import Path

        # 显示标题
        self.console.print(Panel.fit(
            "[bold green]视频手机号脱敏工具 - 智能采样模式[/bold green]",
            border_style="green"
        ))
        self.console.print()

        # 打开输入视频
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {input_path}")

        # 获取视频属性
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # 设置视频信息
        self.set_video_info(width, height, fps, total_frames)
        self.add_log(f"视频加载完成: {width}x{height}, {fps}FPS, {total_frames}帧", "success")

        # 创建输出目录
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 创建视频写入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        if not out.isOpened():
            cap.release()
            raise ValueError(f"无法创建输出视频文件: {output_path}")

        # 第一阶段：采样检测
        self.add_log("第一阶段: 采样检测手机号位置...", "info")
        self.stats['start_time'] = time.time()
        self.stats['phase_start_time'] = time.time()
        self.current_phase = "sampling"
        self.phase_info = {
            'total_phases': 2,
            'current_phase': 1,
            'phase_name': '采样检测',
            'phase_total': total_frames,
            'phase_processed': 0
        }

        # 创建布局
        layout = self.create_layout()

        phone_regions = []
        unique_phones = set()
        ocr_calls = 0

        with Live(layout, console=self.console, refresh_per_second=4, screen=True):
            frame_idx = 0
            sample_interval_frames = int(smart_processor.sample_interval * fps)

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_idx += 1
                self.stats['processed_frames'] = frame_idx
                self.phase_info['phase_processed'] = frame_idx

                # 是否需要采样
                if (frame_idx - 1) % sample_interval_frames == 0:
                    detections = smart_processor.ocr_detector.detect_text(frame)
                    ocr_calls += 1
                    self.stats['ocr_calls'] = ocr_calls

                    for bbox, text, confidence in detections:
                        if smart_processor.phone_detector.contains_phone(text):
                            # 计算时间范围
                            time_point = (frame_idx - 1) / fps
                            buffer = smart_processor.buffer_time
                            start_time = max(0, time_point - buffer)
                            end_time = min(total_frames / fps, time_point + buffer)

                            phone_regions.append({
                                'bbox': bbox,
                                'start_frame': int(start_time * fps),
                                'end_frame': int(end_time * fps),
                                'text': text
                            })
                            unique_phones.add(text)
                            self.stats['total_phones_detected'] += 1
                            self.add_log(f"采样帧 {frame_idx}: 发现手机号 {text}", "success")

                # 每30帧更新一次
                if frame_idx % 30 == 0:
                    self.update_layout(layout)

        # 重置视频
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        self.add_log(f"采样完成: OCR调用 {ocr_calls} 次, 发现 {len(unique_phones)} 个不重复手机号", "success")
        self.add_log("第二阶段: 应用打码...", "info")

        # 切换到第二阶段
        self.current_phase = "blurring"
        self.stats['phase_start_time'] = time.time()
        self.stats['processed_frames'] = 0
        self.stats['frames_with_phones'] = 0
        self.phase_info = {
            'total_phases': 2,
            'current_phase': 2,
            'phase_name': '应用打码',
            'phase_total': total_frames,
            'phase_processed': 0
        }

        with Live(layout, console=self.console, refresh_per_second=4, screen=True):
            frame_idx = 0
            last_log_frame = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_idx += 1
                processed_frame = frame.copy()

                # 检查当前帧是否需要打码
                has_phone = False
                for region in phone_regions:
                    if region['start_frame'] <= frame_idx <= region['end_frame']:
                        processed_frame = smart_processor.apply_blur(processed_frame, region['bbox'])
                        has_phone = True

                if has_phone:
                    self.stats['frames_with_phones'] += 1

                out.write(processed_frame)
                self.stats['processed_frames'] = frame_idx
                self.phase_info['phase_processed'] = frame_idx

                # 每30帧添加日志
                if frame_idx - last_log_frame >= 30:
                    percentage = (frame_idx / total_frames) * 100
                    self.add_log(f"应用打码: {frame_idx}/{total_frames} ({percentage:.1f}%)", "info")
                    last_log_frame = frame_idx

                # 更新布局
                if frame_idx % 10 == 0:
                    self.update_layout(layout)

        # 释放资源
        cap.release()
        out.release()

        elapsed = time.time() - self.stats['start_time']
        self.add_log(f"处理完成! 耗时: {elapsed:.2f}秒", "success")
        self.add_log(f"输出文件: {output_path}", "success")

        # 最后更新
        self.update_layout(layout)

        # 显示最终统计
        self.console.print()
        self.show_final_stats_smart(output_path, unique_phones, ocr_calls)

        return {
            'total_frames': total_frames,
            'processed_frames': total_frames,
            'frames_with_phones': self.stats['frames_with_phones'],
            'total_phones_detected': len(phone_regions),
            'ocr_calls': ocr_calls,
            'unique_phones': list(unique_phones)
        }

    def show_final_stats(self, output_path: str):
        """显示最终统计信息"""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan bold", justify="right")
        table.add_column(style="white")

        elapsed = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        avg_fps = self.stats['processed_frames'] / elapsed if elapsed > 0 else 0

        table.add_row("总帧数", str(self.stats['total_frames']))
        table.add_row("处理帧数", str(self.stats['processed_frames']))
        table.add_row("包含手机号", f"{self.stats['frames_with_phones']} 帧")
        table.add_row("检测总数", f"{self.stats['total_phones_detected']} 个")
        table.add_row("处理时间", f"{elapsed:.2f} 秒")
        table.add_row("平均速度", f"{avg_fps:.2f} FPS")
        table.add_row("输出文件", output_path)

        panel = Panel(
            table,
            title="[bold green]✓ 处理完成[/bold green]",
            border_style="green",
            padding=(1, 2)
        )
        self.console.print(panel)

    def show_final_stats_smart(self, output_path: str, unique_phones: set, ocr_calls: int):
        """显示智能模式最终统计"""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan bold", justify="right")
        table.add_column(style="white")

        elapsed = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        total = self.stats['total_frames']
        speedup = total / ocr_calls if ocr_calls > 0 else 0

        table.add_row("总帧数", str(total))
        table.add_row("OCR调用", f"{ocr_calls} 次")
        table.add_row("节省调用", f"{total - ocr_calls} 次")
        table.add_row("加速比", f"{speedup:.1f}x")
        table.add_row("包含手机号", f"{self.stats['frames_with_phones']} 帧")
        table.add_row("不重复手机号", f"{len(unique_phones)} 个")
        if unique_phones:
            table.add_row("手机号列表", ", ".join(sorted(unique_phones)))
        table.add_row("处理时间", f"{elapsed:.2f} 秒")
        table.add_row("输出文件", output_path)

        panel = Panel(
            table,
            title="[bold green]✓ 处理完成 (智能采样模式)[/bold green]",
            border_style="green",
            padding=(1, 2)
        )
        self.console.print(panel)
