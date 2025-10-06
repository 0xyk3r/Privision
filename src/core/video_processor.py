"""
统一的视频处理模块
支持逐帧模式和智能采样模式，自动检测并打码视频中的手机号
"""
import cv2
import numpy as np
import time
import subprocess
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from dataclasses import dataclass

from src.config.args import ProcessConfig
from src.ui.progress import ProgressCallback
from src.ui.visualizer import Visualizer
from src.core.ocr_detector import OCRDetector
from src.core.phone_detector import PhoneDetector
from src.core.precise_locator import PreciseLocator
from src.core.blur import apply_blur


@dataclass
class PhoneRegion:
    """手机号区域记录（用于智能模式）"""
    bbox: np.ndarray      # 边界框坐标
    text: str             # 识别的文本
    confidence: float     # 置信度
    start_frame: int      # 起始帧号
    end_frame: int        # 结束帧号


class VideoProcessor:
    """
    统一的视频处理器
    支持两种处理模式：
    1. frame-by-frame: 逐帧处理，每帧都进行OCR检测
    2. smart: 智能采样，定期采样检测，区域应用到时间段
    """

    def __init__(
        self,
        config: ProcessConfig,
        progress_callback: Optional[ProgressCallback] = None
    ):
        """
        初始化视频处理器

        Args:
            config: 处理配置对象
            progress_callback: 进度回调接口，用于向UI传递进度信息
        """
        self.config = config
        self.progress_callback = progress_callback

        # 初始化OCR检测器
        self.ocr_detector = OCRDetector(device=config.device)

        # 初始化手机号检测器
        self.phone_detector = PhoneDetector()

        # 初始化精确定位器（如果启用）
        self.precise_locator = None
        if config.precise_phone_location:
            self.precise_locator = PreciseLocator(
                self.ocr_detector,
                max_iterations=config.precise_max_iterations
            )

        # 初始化可视化器（如果启用）
        self.visualizer = None
        if config.enable_visualize:
            self.visualizer = Visualizer(
                window_name="Phone Detection - Visual Preview"
            )
            self._log_visualizer_info()

    def _log_visualizer_info(self):
        """输出可视化模式信息"""
        self._log("\n=== 可视化模式已启用 ===")
        self._log("可视化窗口将在处理开始时打开")
        self._log("快捷键:")
        self._log("  Q/ESC - 退出")
        self._log("  P     - 暂停/继续")
        self._log("  T     - 切换标签显示 (仅手机号 -> 全部显示 -> 隐藏)")
        self._log("")

    def _log(self, message: str, level: str = 'info'):
        """
        输出日志消息

        Args:
            message: 消息内容
            level: 日志级别 (info, success, warning, error)
        """
        if self.progress_callback:
            self.progress_callback.on_log(message, level)
        else:
            print(message)

    @staticmethod
    def _has_ffmpeg() -> bool:
        """检查系统是否安装了 FFmpeg"""
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _reencode_with_ffmpeg(self, temp_path: str, output_path: str):
        """
        使用 FFmpeg 重新编码视频以获得更好的 H.264 压缩

        Args:
            temp_path: 临时视频文件路径
            output_path: 最终输出路径
        """
        self._log("\n使用 FFmpeg 进行 H.264 编码...", 'info')

        try:
            subprocess.run(
                [
                    'ffmpeg',
                    '-i', temp_path,
                    '-c:v', 'libx264',
                    '-preset', 'medium',
                    '-crf', '23',
                    '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart',
                    '-y',
                    output_path
                ],
                check=True,
                capture_output=True,
                text=True
            )

            # 删除临时文件
            Path(temp_path).unlink()
            self._log("  ✓ H.264 编码完成", 'success')

        except subprocess.CalledProcessError as e:
            self._log(f"  ✗ FFmpeg 编码失败: {e.stderr}", 'error')
            self._log("  保留临时文件作为输出", 'warning')
            # 如果 FFmpeg 失败，使用临时文件作为输出
            Path(temp_path).rename(output_path)

    def process_video(
        self,
        input_path: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理视频文件，对所有手机号进行脱敏

        Args:
            input_path: 输入视频路径（如果为None，使用config中的路径）
            output_path: 输出视频路径（如果为None，使用config中的路径）

        Returns:
            处理统计信息字典
        """
        # 使用传入的路径或配置中的路径
        input_path = input_path or self.config.input_path
        output_path = output_path or self.config.output_path

        # 打开输入视频
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {input_path}")

        # 获取视频属性
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # 输出视频信息
        self._log("\n视频信息:")
        self._log(f"  分辨率: {width}x{height}")
        self._log(f"  帧率: {fps} FPS")
        self._log(f"  总帧数: {total_frames}")
        if total_frames > 0:
            self._log(f"  总时长: {total_frames / fps:.2f} 秒")

        # 通知开始处理
        if self.progress_callback:
            self.progress_callback.on_start(total_frames, fps, width, height)

        # 检查 FFmpeg 可用性
        has_ffmpeg = self._has_ffmpeg()
        self._log_ffmpeg_status(has_ffmpeg)

        # 创建输出目录
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 决定输出文件名
        if has_ffmpeg:
            temp_output = str(Path(output_path).with_suffix('.temp.mp4'))
            final_output = output_path
        else:
            temp_output = output_path
            final_output = None

        # 创建视频写入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))

        if not out.isOpened():
            cap.release()
            raise ValueError(f"无法创建输出视频文件: {temp_output}")

        # 根据模式选择处理方法
        try:
            if self.config.mode == 'smart':
                stats = self._process_smart(cap, out, fps, total_frames)
            else:
                stats = self._process_frame_by_frame(cap, out, total_frames, fps)
        finally:
            # 释放资源
            cap.release()
            out.release()

            # 关闭可视化窗口
            if self.visualizer:
                self.visualizer.close()

        # 使用 FFmpeg 重新编码（如果可用）
        if has_ffmpeg and final_output:
            self._reencode_with_ffmpeg(temp_output, final_output)

        # 添加输出路径到统计信息
        stats['output_path'] = output_path

        # 通知完成
        if self.progress_callback:
            self.progress_callback.on_complete(stats)

        # 输出统计信息
        self._log_statistics(stats)

        return stats

    def _log_ffmpeg_status(self, has_ffmpeg: bool):
        """输出FFmpeg状态信息"""
        self._log("\n编码配置:")
        if has_ffmpeg:
            self._log("  ✓ 检测到 FFmpeg，将使用 H.264 高效编码", 'success')
            self._log("  临时编码: MPEG-4")
            self._log("  最终编码: H.264 (CRF 23, Preset Medium)")
        else:
            self._log("  ✗ 未检测到 FFmpeg，使用 MPEG-4 编码", 'warning')
            self._log("  提示: 安装 FFmpeg 可获得更好的压缩率", 'warning')

    def _log_statistics(self, stats: Dict[str, Any]):
        """输出处理统计信息"""
        self._log("\n处理完成！", 'success')
        self._log(f"  总帧数: {stats.get('total_frames', 0)}")
        self._log(f"  处理帧数: {stats.get('processed_frames', 0)}")

        if 'ocr_calls' in stats:
            saved_calls = stats['total_frames'] - stats['ocr_calls']
            self._log(f"  OCR 调用次数: {stats['ocr_calls']} (节省 {saved_calls} 次)")

        self._log(f"  包含手机号的帧数: {stats.get('frames_with_phones', 0)}")
        self._log(f"  检测到的手机号总数: {stats.get('total_phones_detected', 0)}")

        if 'unique_phones' in stats:
            unique_count = len(stats['unique_phones'])
            self._log(f"  不重复手机号: {unique_count} 个")

        self._log(f"  输出文件: {stats.get('output_path', '')}")

    def _process_frame_by_frame(
        self,
        cap: cv2.VideoCapture,
        out: cv2.VideoWriter,
        total_frames: int,
        fps: int
    ) -> Dict[str, Any]:
        """
        逐帧处理模式 - 每帧都进行OCR检测和打码

        Args:
            cap: 视频捕获对象
            out: 视频写入器
            total_frames: 总帧数
            fps: 视频帧率

        Returns:
            处理统计信息
        """
        self._log("\n开始逐帧处理视频...")
        self._log(f"处理模式: 逐帧 (每帧都进行OCR检测)")

        if self.config.precise_phone_location:
            self._log(f"精确定位: 已启用 (最大迭代次数: {self.config.precise_max_iterations})")
        else:
            self._log(f"精确定位: 未启用")

        # 统计信息
        stats = {
            'total_frames': total_frames,
            'processed_frames': 0,
            'frames_with_phones': 0,
            'total_phones_detected': 0
        }

        frame_idx = 0
        start_time = time.time()
        last_fps_update = start_time
        current_fps = 0.0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_idx += 1

                # 计算当前处理速度
                current_time = time.time()
                if current_time - last_fps_update >= 1.0:
                    elapsed = current_time - start_time
                    current_fps = frame_idx / elapsed if elapsed > 0 else 0
                    last_fps_update = current_time

                # 处理当前帧
                processed_frame, phone_count = self._process_single_frame(
                    frame,
                    frame_idx,
                    total_frames,
                    current_fps
                )

                # 写入输出视频
                out.write(processed_frame)

                # 更新统计
                stats['processed_frames'] += 1
                if phone_count > 0:
                    stats['frames_with_phones'] += 1
                    stats['total_phones_detected'] += phone_count

                # 进度回调
                if self.progress_callback:
                    self.progress_callback.on_progress(
                        frame_idx,
                        total_frames,
                        phase='processing'
                    )
                elif frame_idx % 30 == 0:
                    progress = (frame_idx / total_frames) * 100
                    self._log(f"  处理进度: {frame_idx}/{total_frames} ({progress:.1f}%)")

        except KeyboardInterrupt:
            self._log("\n用户中断处理", 'warning')
            raise

        return stats

    def _process_smart(
        self,
        cap: cv2.VideoCapture,
        out: cv2.VideoWriter,
        fps: int,
        total_frames: int
    ) -> Dict[str, Any]:
        """
        智能采样模式 - 定期采样检测，区域应用到时间段

        Args:
            cap: 视频捕获对象
            out: 视频写入器
            fps: 视频帧率
            total_frames: 总帧数

        Returns:
            处理统计信息
        """
        # 计算采样策略
        sample_frame_interval = int(fps * self.config.sample_interval)
        buffer_time = self.config.buffer_time or self.config.sample_interval
        buffer_frames = int(fps * buffer_time)

        self._log("\n开始智能处理视频...")
        self._log(f"智能采样配置:")
        self._log(f"  采样间隔: {self.config.sample_interval} 秒 ({sample_frame_interval} 帧)")
        self._log(f"  缓冲时间: {buffer_time} 秒 ({buffer_frames} 帧)")
        self._log(f"  预计 OCR 次数: {total_frames // sample_frame_interval + 1} 次")
        self._log(f"  理论加速比: {sample_frame_interval}x")

        if self.config.precise_phone_location:
            self._log(f"  精确定位: 已启用 (最大迭代次数: {self.config.precise_max_iterations})")
        else:
            self._log(f"  精确定位: 未启用")

        # 统计信息
        stats = {
            'total_frames': total_frames,
            'processed_frames': 0,
            'ocr_calls': 0,
            'frames_with_phones': 0,
            'total_phones_detected': 0,
            'unique_phones': set()
        }

        try:
            # 阶段1: 识别阶段 - 记录所有需要打码的区域
            self._log("\n[阶段 1/2] 识别手机号区域...")
            if self.progress_callback:
                self.progress_callback.on_phase_change("识别手机号区域", 1, 2)

            phone_regions = self._sampling_phase(
                cap, fps, total_frames, sample_frame_interval,
                buffer_frames, stats
            )

            self._log(f"\n识别完成: 共 {stats['ocr_calls']} 次 OCR 调用, "
                     f"发现 {len(phone_regions)} 个手机号区域", 'success')

            # 阶段2: 打码阶段 - 逐帧处理并应用打码
            self._log("\n[阶段 2/2] 应用打码效果...")
            if self.progress_callback:
                self.progress_callback.on_phase_change("应用打码效果", 2, 2)

            self._blurring_phase(
                cap, out, fps, total_frames, phone_regions, stats
            )

        except KeyboardInterrupt:
            self._log("\n用户中断处理", 'warning')
            raise

        # 转换unique_phones为列表
        stats['unique_phones'] = list(stats['unique_phones'])

        return stats

    def _sampling_phase(
        self,
        cap: cv2.VideoCapture,
        fps: int,
        total_frames: int,
        sample_frame_interval: int,
        buffer_frames: int,
        stats: Dict[str, Any]
    ) -> List[PhoneRegion]:
        """
        采样识别阶段

        Args:
            cap: 视频捕获对象
            fps: 视频帧率
            total_frames: 总帧数
            sample_frame_interval: 采样间隔（帧数）
            buffer_frames: 缓冲帧数
            stats: 统计信息字典

        Returns:
            手机号区域列表
        """
        phone_regions: List[PhoneRegion] = []
        frame_idx = 0

        while frame_idx < total_frames:
            # 跳到采样帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                break

            # 进行 OCR 识别
            detections = self.ocr_detector.detect_text(frame)
            stats['ocr_calls'] += 1

            # 创建手机号标记列表
            phone_mask = []

            # 查找手机号
            for bbox, text, confidence in detections:
                is_phone = self.phone_detector.contains_phone(text, strict=True)
                phone_mask.append(is_phone)

                if is_phone:
                    # 确定打码区域
                    blur_bbox = bbox  # 默认使用原始bbox

                    # 如果启用精确定位，尝试精确定位手机号
                    if self.precise_locator:
                        result = self.precise_locator.refine_phone_bbox(
                            frame, bbox, text, debug=False
                        )
                        if result is not None:
                            refined_bbox, refined_text = result
                            blur_bbox = refined_bbox
                            if self.config.enable_visualize:
                                self._log(f"  [帧 {frame_idx}] ✓ 精确定位: '{text}' → '{refined_text}'")

                    # 计算打码范围
                    start_frame = max(0, frame_idx - buffer_frames)
                    end_frame = min(total_frames - 1, frame_idx + buffer_frames)

                    region = PhoneRegion(
                        bbox=blur_bbox,
                        text=text,
                        confidence=confidence,
                        start_frame=start_frame,
                        end_frame=end_frame
                    )
                    phone_regions.append(region)

                    stats['unique_phones'].add(text)

                    # 通知检测到手机号
                    if self.progress_callback:
                        self.progress_callback.on_phone_detected(
                            frame_idx, text, confidence
                        )
                    else:
                        self._log(f"  [帧 {frame_idx}] 检测到手机号: {text} "
                                 f"(置信度: {confidence:.2f}, 打码范围: {start_frame}-{end_frame})")

            # 可视化
            if self.visualizer:
                should_continue = self.visualizer.show_frame(
                    frame=frame,
                    frame_idx=frame_idx,
                    total_frames=total_frames,
                    detections=detections,
                    phone_mask=phone_mask,
                    wait_key=1
                )
                if not should_continue:
                    self._log("\n用户从可视化窗口退出", 'warning')
                    raise KeyboardInterrupt("用户请求退出")

            # 跳到下一个采样点
            frame_idx += sample_frame_interval

            # 更新进度
            if self.progress_callback:
                self.progress_callback.on_progress(
                    min(frame_idx, total_frames),
                    total_frames,
                    phase='sampling'
                )
            elif stats['ocr_calls'] % 5 == 0:
                progress = (frame_idx / total_frames) * 100
                self._log(f"  识别进度: {min(frame_idx, total_frames)}/{total_frames} "
                         f"({progress:.1f}%) - 已识别 {len(phone_regions)} 个区域")

        return phone_regions

    def _blurring_phase(
        self,
        cap: cv2.VideoCapture,
        out: cv2.VideoWriter,
        fps: int,
        total_frames: int,
        phone_regions: List[PhoneRegion],
        stats: Dict[str, Any]
    ):
        """
        打码应用阶段

        Args:
            cap: 视频捕获对象
            out: 视频写入器
            fps: 视频帧率
            total_frames: 总帧数
            phone_regions: 手机号区域列表
            stats: 统计信息字典
        """
        # 重置到开头
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        frame_idx = 0
        start_time = time.time()
        last_fps_update = start_time
        current_fps = 0.0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 计算当前处理速度
            current_time = time.time()
            if current_time - last_fps_update >= 1.0:
                elapsed = current_time - start_time
                current_fps = frame_idx / elapsed if elapsed > 0 else 0
                last_fps_update = current_time

            processed_frame = frame.copy()
            current_frame_phones = 0

            # 收集当前帧需要打码的区域
            current_regions = []
            for region in phone_regions:
                if region.start_frame <= frame_idx <= region.end_frame:
                    current_regions.append(region)
                    processed_frame = apply_blur(
                        processed_frame,
                        region.bbox,
                        method=self.config.blur_method,
                        strength=self.config.blur_strength
                    )
                    current_frame_phones += 1

            # 可视化
            if self.visualizer:
                detections = [(r.bbox, r.text, r.confidence) for r in current_regions]
                phone_mask = [True] * len(detections)

                should_continue = self.visualizer.show_frame(
                    frame=frame,
                    frame_idx=frame_idx,
                    total_frames=total_frames,
                    detections=detections,
                    phone_mask=phone_mask,
                    fps=current_fps,
                    wait_key=1
                )
                if not should_continue:
                    self._log("\n用户从可视化窗口退出", 'warning')
                    raise KeyboardInterrupt("用户请求退出")

            # 写入输出视频
            out.write(processed_frame)

            stats['processed_frames'] += 1
            if current_frame_phones > 0:
                stats['frames_with_phones'] += 1
                stats['total_phones_detected'] += current_frame_phones

            frame_idx += 1

            # 更新进度
            if self.progress_callback:
                self.progress_callback.on_progress(
                    frame_idx,
                    total_frames,
                    phase='blurring'
                )
            elif frame_idx % (fps * 5) == 0 or frame_idx == total_frames:
                progress = (frame_idx / total_frames) * 100
                self._log(f"  打码进度: {frame_idx}/{total_frames} ({progress:.1f}%)")

    def _process_single_frame(
        self,
        frame: np.ndarray,
        frame_idx: int,
        total_frames: int,
        current_fps: float
    ) -> Tuple[np.ndarray, int]:
        """
        处理单帧图像，检测并打码手机号

        Args:
            frame: 输入帧
            frame_idx: 当前帧索引
            total_frames: 总帧数
            current_fps: 当前处理帧率

        Returns:
            (处理后的帧, 检测到的手机号数量)
        """
        if frame is None or frame.size == 0:
            return frame, 0

        # 使用OCR检测文本
        detections = self.ocr_detector.detect_text(frame)

        processed_frame = frame.copy()
        phone_count = 0
        phone_mask = []  # 标记哪些检测是手机号

        # 遍历所有检测到的文本
        for bbox, text, confidence in detections:
            # 检查是否包含手机号
            is_phone = self.phone_detector.contains_phone(text)
            phone_mask.append(is_phone)

            if is_phone:
                # 确定打码区域
                blur_bbox = bbox  # 默认使用原始bbox

                # 如果启用精确定位，尝试精确定位手机号
                if self.precise_locator:
                    result = self.precise_locator.refine_phone_bbox(
                        frame, bbox, text, debug=False
                    )
                    if result is not None:
                        refined_bbox, refined_text = result
                        blur_bbox = refined_bbox

                # 应用打码
                processed_frame = apply_blur(
                    processed_frame,
                    blur_bbox,
                    method=self.config.blur_method,
                    strength=self.config.blur_strength
                )
                phone_count += 1

                # 通知检测到手机号
                if self.progress_callback:
                    self.progress_callback.on_phone_detected(
                        frame_idx, text, confidence
                    )

        # 如果启用了可视化，显示检测结果
        if self.visualizer:
            should_continue = self.visualizer.show_frame(
                frame=frame,  # 显示原始帧（未打码）
                frame_idx=frame_idx,
                total_frames=total_frames,
                detections=detections,
                phone_mask=phone_mask,
                fps=current_fps,
                wait_key=1
            )
            if not should_continue:
                raise KeyboardInterrupt("用户请求退出")

        return processed_frame, phone_count


if __name__ == '__main__':
    print("=== 统一视频处理器模块 ===")
    print("这是一个模块文件，请使用 main.py 来处理视频")
    print("\n支持的处理模式:")
    print("  - frame-by-frame: 逐帧处理模式")
    print("  - smart: 智能采样模式")
