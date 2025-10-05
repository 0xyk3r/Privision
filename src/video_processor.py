"""
视频处理模块
实现视频逐帧处理、文本检测、手机号识别和打码
"""
import cv2
import numpy as np
from typing import Optional, Callable
from pathlib import Path
from ocr_detector import OCRDetector
from phone_detector import PhoneDetector


class VideoProcessor:
    """视频处理器 - 用于手机号脱敏"""

    def __init__(
        self,
        use_gpu: bool = False,
        blur_method: str = 'gaussian',
        blur_strength: int = 51
    ):
        """
        初始化视频处理器

        Args:
            use_gpu: 是否使用GPU加速OCR
            blur_method: 打码方式 ('gaussian'高斯模糊, 'pixelate'像素化, 'black'黑色遮挡)
            blur_strength: 模糊强度 (高斯模糊的核大小，必须为奇数)
        """
        self.ocr_detector = OCRDetector(use_gpu=use_gpu)
        self.phone_detector = PhoneDetector()
        self.blur_method = blur_method
        self.blur_strength = blur_strength if blur_strength % 2 == 1 else blur_strength + 1

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

    def process_frame(self, frame: np.ndarray, debug: bool = False) -> tuple[np.ndarray, int]:
        """
        处理单帧图像，检测并打码手机号

        Args:
            frame: 输入帧
            debug: 是否输出调试信息

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
                print(f"  [{i+1}] 文本: '{text}' (置信度: {confidence:.4f})")

        processed_frame = frame.copy()
        phone_count = 0

        # 遍历所有检测到的文本
        for bbox, text, confidence in detections:
            # 检查是否包含手机号
            if self.phone_detector.contains_phone(text):
                # 在手机号区域应用打码
                processed_frame = self.apply_blur(processed_frame, bbox)
                phone_count += 1
                print(f"  ✓ 检测到手机号: {text} (置信度: {confidence:.2f})")
            elif debug:
                # 显示为什么不匹配
                phones = self.phone_detector.find_phones(text)
                if phones:
                    print(f"  ℹ 文本 '{text}' 包含数字但不是完整手机号")

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

        # 创建输出目录
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 创建视频写入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        if not out.isOpened():
            cap.release()
            raise ValueError(f"无法创建输出视频文件: {output_path}")

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
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1

            # 处理当前帧
            processed_frame, phone_count = self.process_frame(frame)

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

        # 释放资源
        cap.release()
        out.release()

        print(f"\n处理完成！")
        print(f"  处理帧数: {stats['processed_frames']}")
        print(f"  包含手机号的帧数: {stats['frames_with_phones']}")
        print(f"  检测到的手机号总数: {stats['total_phones_detected']}")
        print(f"  输出文件: {output_path}")

        return stats


if __name__ == '__main__':
    print("=== 视频处理器模块 ===")
    print("这是一个模块文件，请使用 main.py 来处理视频")
