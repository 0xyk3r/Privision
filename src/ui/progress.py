"""进度回调接口 - 用于解耦UI和处理逻辑"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime


class ProgressCallback(ABC):
    """进度回调基类 - 处理器通过此接口向UI传递信息"""

    @abstractmethod
    def on_start(self, total_frames: int, fps: int, width: int, height: int):
        """
        处理开始时调用

        Args:
            total_frames: 视频总帧数
            fps: 视频帧率
            width: 视频宽度
            height: 视频高度
        """
        pass

    @abstractmethod
    def on_progress(self, current_frame: int, total_frames: int, phase: str = 'processing'):
        """
        处理进度更新

        Args:
            current_frame: 当前处理的帧号
            total_frames: 总帧数
            phase: 当前阶段 (processing, sampling, blurring)
        """
        pass

    @abstractmethod
    def on_detected(self, frame_idx: int, text: str, confidence: float):
        """
        检测到目标内容时调用

        Args:
            frame_idx: 帧号
            text: 目标内容文本
            confidence: 置信度
        """
        pass

    @abstractmethod
    def on_log(self, message: str, level: str = 'info'):
        """
        日志消息

        Args:
            message: 日志内容
            level: 日志级别 (info, success, warning, error)
        """
        pass

    @abstractmethod
    def on_phase_change(self, phase: str, phase_num: int, total_phases: int):
        """
        阶段切换

        Args:
            phase: 阶段名称
            phase_num: 当前阶段编号
            total_phases: 总阶段数
        """
        pass

    @abstractmethod
    def on_complete(self, stats: Dict[str, Any]):
        """
        处理完成时调用

        Args:
            stats: 统计信息字典
        """
        pass

    @abstractmethod
    def on_error(self, error: Exception):
        """
        错误发生时调用

        Args:
            error: 异常对象
        """
        pass

    def on_ocr_call(self):
        """
        OCR调用时调用（用于统计OCR调用次数）
        """
        pass  # 默认空实现，子类可选择性重写


class ConsoleProgress(ProgressCallback):
    """简单的控制台进度输出（当禁用Rich时使用）"""

    def __init__(self):
        self.start_time = None
        self.last_progress = 0

    def on_start(self, total_frames: int, fps: int, width: int, height: int):
        """开始处理"""
        self.start_time = datetime.now()
        print(f"\n开始处理视频:")
        print(f"  分辨率: {width}x{height}")
        print(f"  帧率: {fps} FPS")
        print(f"  总帧数: {total_frames}")
        print()

    def on_progress(self, current_frame: int, total_frames: int, phase: str = 'processing'):
        """更新进度"""
        progress = int((current_frame / total_frames) * 100)

        # 每5%输出一次
        if progress >= self.last_progress + 5:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            fps = current_frame / elapsed if elapsed > 0 else 0
            print(f"进度: {progress}% ({current_frame}/{total_frames}) - 速度: {fps:.2f} FPS")
            self.last_progress = progress

    def on_detected(self, frame_idx: int, text: str, confidence: float):
        """检测到目标内容"""
        print(f"  [帧 {frame_idx}] 检测到目标内容: {text} (置信度: {confidence:.2f})")

    def on_log(self, message: str, level: str = 'info'):
        """输出日志"""
        prefix = {
            'info': '[INFO]',
            'success': '[✓]',
            'warning': '[!]',
            'error': '[✗]'
        }.get(level, '[INFO]')
        print(f"{prefix} {message}")

    def on_phase_change(self, phase: str, phase_num: int, total_phases: int):
        """阶段切换"""
        print(f"\n{'='*60}")
        print(f"阶段 {phase_num}/{total_phases}: {phase}")
        print(f"{'='*60}\n")
        self.last_progress = 0

    def on_complete(self, stats: Dict[str, Any]):
        """处理完成"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"\n{'='*60}")
        print("处理完成!")
        print(f"{'='*60}")
        print(f"总帧数: {stats.get('total_frames', 0)}")
        print(f"处理帧数: {stats.get('processed_frames', 0)}")
        print(f"包含目标: {stats.get('frames_with_detections', 0)} 帧")
        print(f"检测总数: {stats.get('total_detections', 0)} 个")
        if 'ocr_calls' in stats:
            print(f"OCR调用: {stats['ocr_calls']} 次")
        print(f"处理时间: {elapsed:.2f} 秒")
        print(f"输出文件: {stats.get('output_path', '')}")
        print()

    def on_error(self, error: Exception):
        """错误处理"""
        print(f"\n[错误] {str(error)}")
        import traceback
        traceback.print_exc()

    def on_ocr_call(self):
        """OCR调用"""
        # 在这里可以统计OCR调用次数
        super().on_ocr_call()  # 调用父类的空实现（可选）
