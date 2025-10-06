"""
智能视频处理模块
使用时间段采样策略：每隔固定时间识别一次，识别到的区域应用到整个时间段
"""
import cv2
import numpy as np
import time
import subprocess
from typing import Optional, Callable, List, Tuple, Dict
from pathlib import Path
from ocr_detector import OCRDetector
from phone_detector import PhoneDetector
from debug_visualizer import DebugVisualizer
from precise_locator import PreciseLocator


class PhoneRegion:
    """手机号区域记录"""

    def __init__(self, bbox: np.ndarray, text: str, confidence: float,
                 start_frame: int, end_frame: int):
        """
        初始化手机号区域

        Args:
            bbox: 坐标框
            text: 识别的文本
            confidence: 置信度
            start_frame: 起始帧号
            end_frame: 结束帧号
        """
        self.bbox = bbox
        self.text = text
        self.confidence = confidence
        self.start_frame = start_frame
        self.end_frame = end_frame


class SmartVideoProcessor:
    """智能视频处理器 - 使用采样识别策略"""

    def __init__(
            self,
            use_gpu: bool = False,
            blur_method: str = 'gaussian',
            blur_strength: int = 51,
            sample_interval: float = 1.0,
            buffer_time: float = None,
            visualize: bool = False,
            precise_phone_location: bool = False,
            precise_max_iterations: int = 3
    ):
        """
        初始化智能视频处理器

        Args:
            use_gpu: 是否使用GPU加速
            blur_method: 打码方式
            blur_strength: 模糊强度
            sample_interval: 采样间隔（秒），每隔多久识别一次
            buffer_time: 缓冲时间（秒），识别点前后各扩展的时间
                        如果为 None，自动设置为 sample_interval（确保覆盖采样间隙）
            visualize: 是否启用可视化窗口
            precise_phone_location: 是否启用精确定位（通过迭代验证精确定位手机号，避免打码其他文字）
            precise_max_iterations: 精确定位的最大迭代次数
        """
        self.ocr_detector = OCRDetector(use_gpu=use_gpu)
        self.phone_detector = PhoneDetector()
        self.blur_method = blur_method
        self.blur_strength = blur_strength if blur_strength % 2 == 1 else blur_strength + 1
        self.sample_interval = sample_interval
        self.visualize = visualize
        self.visualizer = DebugVisualizer() if visualize else None
        self.precise_phone_location = precise_phone_location
        self.precise_locator = PreciseLocator(self.ocr_detector, max_iterations=precise_max_iterations) if precise_phone_location else None

        if visualize:
            print("\n=== 可视化模式已启用 ===")
            print("可视化窗口将在处理开始时打开")
            print("快捷键:")
            print("  Q/ESC - 退出")
            print("  P     - 暂停/继续")
            print("  T     - 切换标签显示 (仅手机号 -> 全部显示 -> 隐藏)")
            print()

        # 如果没有指定 buffer_time，默认为 sample_interval
        # 这样可以确保完全覆盖采样间隙，不会有马赛克消失的情况
        if buffer_time is None:
            self.buffer_time = sample_interval
            self.auto_buffer = True
        else:
            self.buffer_time = buffer_time
            self.auto_buffer = False

    def apply_blur(self, image: np.ndarray, bbox: np.ndarray) -> np.ndarray:
        """在指定区域应用打码效果"""
        x_coords = bbox[:, 0]
        y_coords = bbox[:, 1]
        x_min, y_min = int(np.min(x_coords)), int(np.min(y_coords))
        x_max, y_max = int(np.max(x_coords)), int(np.max(y_coords))

        h, w = image.shape[:2]
        x_min = max(0, x_min)
        y_min = max(0, y_min)
        x_max = min(w, x_max)
        y_max = min(h, y_max)

        if x_min >= x_max or y_min >= y_max:
            return image

        roi = image[y_min:y_max, x_min:x_max]
        if roi.size == 0:
            return image

        if self.blur_method == 'gaussian':
            blurred_roi = cv2.GaussianBlur(roi, (self.blur_strength, self.blur_strength), 0)
        elif self.blur_method == 'pixelate':
            small = cv2.resize(roi, (10, 10), interpolation=cv2.INTER_LINEAR)
            blurred_roi = cv2.resize(small, (roi.shape[1], roi.shape[0]), interpolation=cv2.INTER_NEAREST)
        elif self.blur_method == 'black':
            blurred_roi = np.zeros_like(roi)
        else:
            blurred_roi = cv2.GaussianBlur(roi, (self.blur_strength, self.blur_strength), 0)

        result = image.copy()
        result[y_min:y_max, x_min:x_max] = blurred_roi
        return result

    @staticmethod
    def _has_ffmpeg() -> bool:
        """检查系统是否安装了 FFmpeg"""
        try:
            subprocess.run(['ffmpeg', '-version'],
                           capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _reencode_with_ffmpeg(self, temp_path: str, output_path: str,
                              progress_callback: Optional[Callable[[float, str], None]] = None):
        """
        使用 FFmpeg 重新编码视频以获得更好的 H.264 压缩

        Args:
            temp_path: 临时视频文件路径
            output_path: 最终输出路径
            progress_callback: 进度回调函数
        """
        print(f"\n使用 FFmpeg 进行 H.264 编码...")
        if progress_callback:
            progress_callback(95, "使用 FFmpeg 进行 H.264 编码...")

        try:
            result = subprocess.run(
                [
                    'ffmpeg',
                    '-i', temp_path,  # 输入临时文件
                    '-c:v', 'libx264',  # 使用 H.264 编码器
                    '-preset', 'medium',  # 编码速度 (ultrafast, fast, medium, slow, veryslow)
                    '-crf', '23',  # 质量控制 (18-28，数值越小质量越好)
                    '-pix_fmt', 'yuv420p',  # 像素格式，确保兼容性
                    '-movflags', '+faststart',  # 优化网络播放（元数据前置）
                    '-y',  # 覆盖输出文件
                    output_path
                ],
                check=True,
                capture_output=True,
                text=True
            )

            # 删除临时文件
            Path(temp_path).unlink()
            print(f"  ✓ H.264 编码完成")
            if progress_callback:
                progress_callback(100, "H.264 编码完成")

        except subprocess.CalledProcessError as e:
            print(f"  ✗ FFmpeg 编码失败: {e.stderr}")
            print(f"  保留临时文件作为输出")
            # 如果 FFmpeg 失败，使用临时文件作为输出
            Path(temp_path).rename(output_path)
            if progress_callback:
                progress_callback(100, "FFmpeg 编码失败，使用临时文件")

    def process_video(
            self,
            input_path: str,
            output_path: str,
            progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> dict:
        """
        智能处理视频文件

        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            progress_callback: 进度回调函数 (progress: float, message: str)

        Returns:
            处理统计信息字典
        """
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {input_path}")

        # 获取视频属性
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"\n视频信息:")
        print(f"  分辨率: {width}x{height}")
        print(f"  帧率: {fps} FPS")
        print(f"  总帧数: {total_frames}")
        print(f"  总时长: {total_frames / fps:.2f} 秒")

        # 计算采样策略
        sample_frame_interval = int(fps * self.sample_interval)
        buffer_frames = int(fps * self.buffer_time)

        print(f"\n智能采样配置:")
        print(f"  采样间隔: {self.sample_interval} 秒 ({sample_frame_interval} 帧)")
        if self.auto_buffer:
            print(f"  缓冲时间: {self.buffer_time} 秒 ({buffer_frames} 帧) [自动: sample_interval]")
        else:
            print(f"  缓冲时间: {self.buffer_time} 秒 ({buffer_frames} 帧) [用户指定]")
        print(f"  预计 OCR 次数: {total_frames // sample_frame_interval + 1} 次")
        print(f"  理论加速比: {sample_frame_interval}x")
        print(f"  采样覆盖策略: 每个识别点前后各 {self.buffer_time} 秒打码")
        if self.precise_phone_location:
            print(f"  精确定位: 已启用 (会对每个检测到的手机号进行精确定位)")
        else:
            print(f"  精确定位: 未启用 (打码整个OCR识别区域)")

        # 检查 FFmpeg 可用性
        has_ffmpeg = self._has_ffmpeg()
        if has_ffmpeg:
            print(f"\n编码配置:")
            print(f"  ✓ 检测到 FFmpeg，将使用 H.264 高效编码")
            print(f"  临时编码: MPEG-4")
            print(f"  最终编码: H.264 (CRF 23, Preset Medium)")
        else:
            print(f"\n编码配置:")
            print(f"  ✗ 未检测到 FFmpeg，使用 MPEG-4 编码")
            print(f"  提示: 安装 FFmpeg 可获得更好的压缩率")

        # 创建输出目录
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 决定输出文件名
        if has_ffmpeg:
            # 使用临时文件，后续用 FFmpeg 重新编码
            temp_output = str(Path(output_path).with_suffix('.temp.mp4'))
            final_output = output_path
        else:
            # 直接输出到目标文件
            temp_output = output_path
            final_output = None

        # 创建视频写入器 - 使用 MPEG-4 编解码器（兼容性最好）
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))

        if not out.isOpened():
            cap.release()
            raise ValueError(f"无法创建输出视频文件: {temp_output}")

        # 统计信息
        stats = {
            'total_frames': total_frames,
            'processed_frames': 0,
            'ocr_calls': 0,
            'frames_with_phones': 0,
            'total_phones_detected': 0,
            'unique_phones': set()
        }

        print(f"\n开始智能处理视频...")

        try:
            # 阶段1: 识别阶段 - 记录所有需要打码的区域
            print("\n[阶段 1/2] 识别手机号区域...")
            if progress_callback:
                progress_callback(0, "[阶段 1/2] 开始识别手机号区域...")
            phone_regions: List[PhoneRegion] = []

            frame_idx = 0
            last_progress_update = 0
            while frame_idx < total_frames:
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
                        if self.precise_phone_location and self.precise_locator:
                            result = self.precise_locator.refine_phone_bbox(
                                frame, bbox, text, debug=True  # 启用调试模式
                            )
                            if result is not None:
                                refined_bbox, refined_text = result
                                blur_bbox = refined_bbox
                                print(f"  [帧 {frame_idx}] ✓ 精确定位成功: '{text}' → '{refined_text}'")
                            else:
                                print(f"  [帧 {frame_idx}] ✗ 精确定位失败，使用原始bbox: '{text}'")

                        start_frame = max(0, frame_idx - buffer_frames)
                        end_frame = min(total_frames - 1, frame_idx + buffer_frames)

                        region = PhoneRegion(blur_bbox, text, confidence, start_frame, end_frame)
                        phone_regions.append(region)

                        stats['unique_phones'].add(text)
                        print(f"  [帧 {frame_idx}] 检测到手机号: {text} "
                              f"(置信度: {confidence:.2f}, 打码范围: {start_frame}-{end_frame})")

                # 可视化
                if self.visualizer:
                    try:
                        should_continue = self.visualizer.show_frame(
                            frame=frame,
                            frame_idx=frame_idx,
                            total_frames=total_frames,
                            detections=detections,
                            phone_mask=phone_mask,
                            wait_key=1
                        )
                        if not should_continue:
                            print("\n[可视化] 用户从可视化窗口退出")
                            raise KeyboardInterrupt("用户请求退出")
                    except KeyboardInterrupt:
                        raise

                # 跳到下一个采样点
                frame_idx += sample_frame_interval

                # 更新进度（识别阶段占 75%）
                current_progress = (frame_idx / total_frames) * 75
                if current_progress - last_progress_update >= 0.5 or frame_idx >= total_frames - sample_frame_interval:
                    message = f"[阶段 1/2] 识别进度: {frame_idx}/{total_frames} ({(frame_idx / total_frames) * 100:.1f}%) - 已识别 {len(phone_regions)} 个区域"
                    if stats['ocr_calls'] % 5 == 0 or frame_idx >= total_frames - sample_frame_interval:
                        print(f"  {message}")
                    if progress_callback:
                        progress_callback(current_progress, message)
                    last_progress_update = current_progress

            print(f"\n识别完成: 共 {stats['ocr_calls']} 次 OCR 调用, "
                  f"发现 {len(phone_regions)} 个手机号区域")
            if progress_callback:
                progress_callback(75, f"[阶段 1/2] 识别完成，发现 {len(phone_regions)} 个手机号区域")

            # 阶段2: 打码阶段 - 逐帧处理并应用打码
            print("\n[阶段 2/2] 应用打码效果...")
            if progress_callback:
                progress_callback(75, "[阶段 2/2] 开始应用打码效果...")

            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 重置到开头
            frame_idx = 0
            start_time = time.time()
            last_fps_update = start_time
            current_fps = 0.0
            last_progress_update = 75

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
                        processed_frame = self.apply_blur(processed_frame, region.bbox)
                        current_frame_phones += 1

                # 可视化
                if self.visualizer:
                    detections = [(r.bbox, r.text, r.confidence) for r in current_regions]
                    phone_mask = [True] * len(detections)

                    try:
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
                            print("\n[可视化] 用户从可视化窗口退出")
                            raise KeyboardInterrupt("用户请求退出")
                    except KeyboardInterrupt:
                        raise

                # 写入输出视频
                out.write(processed_frame)

                stats['processed_frames'] += 1
                if current_frame_phones > 0:
                    stats['frames_with_phones'] += 1
                    stats['total_phones_detected'] += current_frame_phones

                frame_idx += 1

                # 更新进度（打码阶段占 15%，75%-90%）
                current_progress = 75 + (stats['processed_frames'] / total_frames) * 15
                if current_progress - last_progress_update >= 0.5 or frame_idx == total_frames:
                    message = f"[阶段 2/2] 打码进度: {stats['processed_frames']}/{total_frames} ({(stats['processed_frames'] / total_frames) * 100:.1f}%)"
                    if frame_idx % (fps * 5) == 0 or frame_idx == total_frames:
                        print(f"  {message}")
                    if progress_callback:
                        progress_callback(current_progress, message)
                    last_progress_update = current_progress

        finally:
            # 释放资源
            cap.release()
            out.release()

            # 关闭可视化窗口
            if self.visualizer:
                self.visualizer.close()

        # 阶段3: FFmpeg 重新编码（如果可用）
        if has_ffmpeg and final_output:
            self._reencode_with_ffmpeg(temp_output, final_output, progress_callback)
        else:
            if progress_callback:
                progress_callback(100, "处理完成")

        print(f"\n处理完成！")
        print(f"  总帧数: {stats['total_frames']}")
        print(f"  OCR 调用次数: {stats['ocr_calls']} (节省 {total_frames - stats['ocr_calls']} 次)")
        print(f"  包含手机号的帧数: {stats['frames_with_phones']}")
        print(f"  检测到的手机号总数: {stats['total_phones_detected']}")
        print(f"  不重复手机号: {len(stats['unique_phones'])} 个")
        print(f"  输出文件: {output_path}")

        stats['unique_phones'] = list(stats['unique_phones'])
        return stats


if __name__ == '__main__':
    print("=== 智能视频处理器模块 ===")
    print("这是一个模块文件，请使用 main_smart.py 来处理视频")
