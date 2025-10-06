"""
视频处理模块
实现视频逐帧处理、文本检测、手机号识别和打码
"""
import cv2
import numpy as np
import time
import subprocess
from typing import Optional, Callable
from pathlib import Path
from ocr_detector import OCRDetector
from phone_detector import PhoneDetector
from debug_visualizer import DebugVisualizer
from precise_locator import PreciseLocator


class VideoProcessor:
    """视频处理器 - 用于手机号脱敏"""

    def __init__(
            self,
            use_gpu: bool = False,
            blur_method: str = 'gaussian',
            blur_strength: int = 51,
            visualize: bool = False,
            precise_phone_location: bool = False,
            precise_max_iterations: int = 3
    ):
        """
        初始化视频处理器

        Args:
            use_gpu: 是否使用GPU加速OCR
            blur_method: 打码方式 ('gaussian'高斯模糊, 'pixelate'像素化, 'black'黑色遮挡)
            blur_strength: 模糊强度 (高斯模糊的核大小，必须为奇数)
            visualize: 是否启用可视化窗口
            precise_phone_location: 是否启用精确定位（通过迭代验证精确定位手机号，避免打码其他文字）
            precise_max_iterations: 精确定位的最大迭代次数
        """
        self.ocr_detector = OCRDetector(use_gpu=use_gpu)
        self.phone_detector = PhoneDetector()
        self.blur_method = blur_method
        self.blur_strength = blur_strength if blur_strength % 2 == 1 else blur_strength + 1
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

    def apply_blur(self, image: np.ndarray, bbox: np.ndarray) -> np.ndarray:
        """
        在指定区域应用打码效果

        Args:
            image: 原始图像
            bbox: 四个顶点坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]

        Returns:
            打码后的图像
        """
        # 获取矩形边界
        x_coords = bbox[:, 0]
        y_coords = bbox[:, 1]
        x_min, y_min = int(np.min(x_coords)), int(np.min(y_coords))
        x_max, y_max = int(np.max(x_coords)), int(np.max(y_coords))

        # 边界检查
        h, w = image.shape[:2]
        x_min = max(0, x_min)
        y_min = max(0, y_min)
        x_max = min(w, x_max)
        y_max = min(h, y_max)

        if x_min >= x_max or y_min >= y_max:
            return image

        # 提取区域
        roi = image[y_min:y_max, x_min:x_max]

        if roi.size == 0:
            return image

        # 应用打码效果
        if self.blur_method == 'gaussian':
            # 高斯模糊
            blurred_roi = cv2.GaussianBlur(roi, (self.blur_strength, self.blur_strength), 0)
        elif self.blur_method == 'pixelate':
            # 像素化（马赛克）
            small = cv2.resize(roi, (10, 10), interpolation=cv2.INTER_LINEAR)
            blurred_roi = cv2.resize(small, (roi.shape[1], roi.shape[0]), interpolation=cv2.INTER_NEAREST)
        elif self.blur_method == 'black':
            # 黑色遮挡
            blurred_roi = np.zeros_like(roi)
        else:
            # 默认使用高斯模糊
            blurred_roi = cv2.GaussianBlur(roi, (self.blur_strength, self.blur_strength), 0)

        # 将打码后的区域放回原图
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

    def _reencode_with_ffmpeg(self, temp_path: str, output_path: str):
        """
        使用 FFmpeg 重新编码视频以获得更好的 H.264 压缩

        Args:
            temp_path: 临时视频文件路径
            output_path: 最终输出路径
        """
        print(f"\n使用 FFmpeg 进行 H.264 编码...")

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

        except subprocess.CalledProcessError as e:
            print(f"  ✗ FFmpeg 编码失败: {e.stderr}")
            print(f"  保留临时文件作为输出")
            # 如果 FFmpeg 失败，使用临时文件作为输出
            Path(temp_path).rename(output_path)

    def process_frame(
            self,
            frame: np.ndarray,
            debug: bool = False,
            detection_callback: Optional[Callable[[str, float], None]] = None,
            frame_idx: int = 0,
            total_frames: int = 0,
            current_fps: Optional[float] = None
    ) -> tuple[np.ndarray, int]:
        """
        处理单帧图像，检测并打码手机号

        Args:
            frame: 输入帧
            debug: 是否输出调试信息
            detection_callback: 检测回调函数 callback(text, confidence)
            frame_idx: 当前帧索引（用于可视化）
            total_frames: 总帧数（用于可视化）
            current_fps: 当前处理帧率（用于可视化）

        Returns:
            (处理后的帧, 检测到的手机号数量)
        """
        if frame is None or frame.size == 0:
            return frame, 0

        # 使用OCR检测文本
        detections = self.ocr_detector.detect_text(frame)

        if debug:
            print(f"\n[调试] OCR检测到 {len(detections)} 个文本区域")
            for i, (bbox, text, confidence) in enumerate(detections):
                print(f"  [{i + 1}] 文本: '{text}' (置信度: {confidence:.4f})")

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
                if self.precise_phone_location and self.precise_locator:
                    result = self.precise_locator.refine_phone_bbox(
                        frame, bbox, text, debug=debug
                    )
                    if result is not None:
                        refined_bbox, refined_text = result
                        blur_bbox = refined_bbox
                        if debug:
                            print(f"  → 使用精确定位的bbox ('{text}' → '{refined_text}')")

                # 在手机号区域应用打码
                processed_frame = self.apply_blur(processed_frame, blur_bbox)
                phone_count += 1

                # 调用检测回调
                if detection_callback:
                    detection_callback(text, confidence)
                elif not debug:  # 只有在没有回调且非debug模式时才打印
                    print(f"  ✓ 检测到手机号: {text} (置信度: {confidence:.2f})")

                if debug:
                    print(f"  ✓ 检测到手机号: {text} (置信度: {confidence:.2f})")
            elif debug:
                # 显示为什么不匹配
                phones = self.phone_detector.find_phones(text)
                if phones:
                    print(f"  ℹ 文本 '{text}' 包含数字但不是完整手机号")

        # 如果启用了调试可视化，显示检测结果
        if self.visualizer:
            # 显示原始帧（未打码）上的检测结果
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
                raise KeyboardInterrupt("用户请求退出")

        return processed_frame, phone_count

    def process_video(
            self,
            input_path: str,
            output_path: str,
            progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> dict:
        """
        处理视频文件，对所有手机号进行脱敏

        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            progress_callback: 进度回调函数 callback(current_frame, total_frames)

        Returns:
            处理统计信息字典
        """
        # 打开输入视频
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
            'frames_with_phones': 0,
            'total_phones_detected': 0
        }

        print(f"\n开始处理视频...")

        # 逐帧处理
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

                # 计算当前处理速度（每秒更新一次）
                current_time = time.time()
                if current_time - last_fps_update >= 1.0:
                    elapsed = current_time - start_time
                    current_fps = frame_idx / elapsed if elapsed > 0 else 0
                    last_fps_update = current_time

                # 处理当前帧
                try:
                    processed_frame, phone_count = self.process_frame(
                        frame,
                        debug=self.visualize,
                        frame_idx=frame_idx,
                        total_frames=total_frames,
                        current_fps=current_fps
                    )
                except KeyboardInterrupt:
                    print("\n[可视化] 用户从可视化窗口退出")
                    raise

                # 写入输出视频
                out.write(processed_frame)

                # 更新统计
                stats['processed_frames'] += 1
                if phone_count > 0:
                    stats['frames_with_phones'] += 1
                    stats['total_phones_detected'] += phone_count

                # 进度回调
                if progress_callback:
                    progress_callback(frame_idx, total_frames)
                elif frame_idx % 30 == 0:  # 每30帧打印一次进度
                    progress = (frame_idx / total_frames) * 100
                    print(f"  处理进度: {frame_idx}/{total_frames} ({progress:.1f}%)")

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

        print(f"\n处理完成！")
        print(f"  处理帧数: {stats['processed_frames']}")
        print(f"  包含手机号的帧数: {stats['frames_with_phones']}")
        print(f"  检测到的手机号总数: {stats['total_phones_detected']}")
        print(f"  输出文件: {output_path}")

        return stats


if __name__ == '__main__':
    print("=== 视频处理器模块 ===")
    print("这是一个模块文件，请使用 main.py 来处理视频")
