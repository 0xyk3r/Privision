"""
可视化窗口模块
用于实时显示视频处理过程中的检测结果
"""
import cv2
import numpy as np
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


class Visualizer:
    """可视化工具 - 用于显示检测到的手机号和处理帧"""

    # 标签显示模式
    LABEL_NONE = 0      # 不显示标签
    LABEL_PHONE = 1     # 只显示手机号标签
    LABEL_ALL = 2       # 显示所有标签

    def __init__(self, window_name: str = "Phone Detection - Visual Preview"):
        """
        初始化可视化器

        Args:
            window_name: 窗口名称
        """
        self.window_name = window_name
        self.window_created = False
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.6
        self.font_thickness = 2
        self.label_mode = self.LABEL_PHONE  # 默认只显示手机号标签

        # 尝试加载中文字体
        self.pil_font = self._load_chinese_font()

    def _load_chinese_font(self, size: int = 16):
        """
        加载中文字体

        Args:
            size: 字体大小

        Returns:
            PIL字体对象，如果加载失败则返回None
        """
        # Windows常见中文字体路径
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
            "C:/Windows/Fonts/simhei.ttf",    # 黑体
            "C:/Windows/Fonts/simsun.ttc",    # 宋体
            "C:/Windows/Fonts/Arial.ttf",     # Arial (fallback)
        ]

        for font_path in font_paths:
            try:
                if Path(font_path).exists():
                    return ImageFont.truetype(font_path, size)
            except Exception:
                continue

        # 如果都失败，使用默认字体
        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()

    def _cv2_to_pil(self, cv2_image: np.ndarray) -> Image.Image:
        """将OpenCV图像转换为PIL图像"""
        return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))

    def _pil_to_cv2(self, pil_image: Image.Image) -> np.ndarray:
        """将PIL图像转换为OpenCV图像"""
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    def create_window(self):
        """创建可视化窗口"""
        if not self.window_created:
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            self.window_created = True

    def draw_detections(
        self,
        frame: np.ndarray,
        detections: List[Tuple[np.ndarray, str, float]],
        phone_mask: Optional[List[bool]] = None
    ) -> np.ndarray:
        """
        在帧上绘制检测结果

        Args:
            frame: 原始帧
            detections: OCR检测结果列表 [(bbox, text, confidence), ...]
            phone_mask: 布尔列表，标记哪些检测是手机号

        Returns:
            绘制了标注的帧
        """
        display_frame = frame.copy()

        # 步骤1：先在OpenCV上绘制所有边界框
        for idx, (bbox, text, confidence) in enumerate(detections):
            is_phone = phone_mask[idx] if phone_mask and idx < len(phone_mask) else False
            color_bgr = (0, 0, 255) if is_phone else (0, 255, 0)
            thickness = 3 if is_phone else 1

            # 绘制边界框
            pts = bbox.astype(np.int32).reshape((-1, 1, 2))
            cv2.polylines(display_frame, [pts], True, color_bgr, thickness)

        # 步骤2：如果需要绘制标签，转换为PIL并绘制
        if self.label_mode != self.LABEL_NONE:
            pil_image = self._cv2_to_pil(display_frame)
            draw = ImageDraw.Draw(pil_image)

            for idx, (bbox, text, confidence) in enumerate(detections):
                is_phone = phone_mask[idx] if phone_mask and idx < len(phone_mask) else False

                # 只显示手机号模式：跳过非手机号
                if self.label_mode == self.LABEL_PHONE and not is_phone:
                    continue

                # 设置颜色
                color_rgb = (255, 0, 0) if is_phone else (0, 255, 0)

                # 绘制文本标签（使用PIL支持中文）
                x_min = int(np.min(bbox[:, 0]))
                y_min = int(np.min(bbox[:, 1]))

                # 构建标签文本
                if is_phone:
                    label = f"[手机号] {text} ({confidence:.2f})"
                else:
                    label = f"{text} ({confidence:.2f})"

                # 计算文本大小
                bbox_text = draw.textbbox((0, 0), label, font=self.pil_font)
                text_width = bbox_text[2] - bbox_text[0]
                text_height = bbox_text[3] - bbox_text[1]

                # 绘制文本背景
                bg_y1 = max(0, y_min - text_height - 10)
                bg_y2 = bg_y1 + text_height + 10
                bg_x1 = x_min
                bg_x2 = x_min + text_width + 10

                draw.rectangle(
                    [(bg_x1, bg_y1), (bg_x2, bg_y2)],
                    fill=color_rgb
                )

                # 绘制文本
                draw.text(
                    (x_min + 5, bg_y1 + 5),
                    label,
                    font=self.pil_font,
                    fill=(255, 255, 255)
                )

            # 转换回OpenCV格式
            display_frame = self._pil_to_cv2(pil_image)

        return display_frame

    def add_info_panel(
        self,
        frame: np.ndarray,
        frame_idx: int,
        total_frames: int,
        phone_count: int,
        fps: Optional[float] = None
    ) -> np.ndarray:
        """
        在画面下方添加独立的信息面板

        Args:
            frame: 输入帧
            frame_idx: 当前帧索引
            total_frames: 总帧数
            phone_count: 检测到的手机号数量
            fps: 处理帧率

        Returns:
            拼接了信息面板的图像
        """
        h, w = frame.shape[:2]

        # 创建信息面板（黑色背景）
        panel_height = 140
        panel = np.zeros((panel_height, w, 3), dtype=np.uint8)

        # 转换为PIL以支持中文
        pil_panel = self._cv2_to_pil(panel)
        draw = ImageDraw.Draw(pil_panel)

        # 使用稍大的字体
        info_font = self._load_chinese_font(18)

        # 添加文本信息
        y_offset = 10
        line_height = 25

        # 帧信息
        progress = (frame_idx / total_frames * 100) if total_frames > 0 else 0

        # 标签模式提示
        label_mode_text = {
            self.LABEL_NONE: "隐藏",
            self.LABEL_PHONE: "仅手机号",
            self.LABEL_ALL: "全部显示"
        }[self.label_mode]

        info_lines = [
            f"帧: {frame_idx}/{total_frames} ({progress:.1f}%)",
            f"检测到的手机号: {phone_count}",
        ]

        if fps is not None:
            info_lines.append(f"处理速度: {fps:.1f} FPS")

        info_lines.append(f"标签模式: {label_mode_text} (按 'T' 切换)")
        info_lines.append("按 'Q' 或 ESC 退出 | 按 'P' 暂停/继续")

        for i, line in enumerate(info_lines):
            draw.text(
                (10, y_offset + i * line_height),
                line,
                font=info_font,
                fill=(255, 255, 255)
            )

        # 转换回OpenCV格式
        panel_cv = self._pil_to_cv2(pil_panel)

        # 垂直拼接原始帧和信息面板
        result = np.vstack([frame, panel_cv])

        return result

    def show_frame(
        self,
        frame: np.ndarray,
        frame_idx: int,
        total_frames: int,
        detections: List[Tuple[np.ndarray, str, float]],
        phone_mask: Optional[List[bool]] = None,
        fps: Optional[float] = None,
        wait_key: int = 1
    ) -> bool:
        """
        显示带标注的帧

        Args:
            frame: 原始帧
            frame_idx: 当前帧索引
            total_frames: 总帧数
            detections: OCR检测结果
            phone_mask: 手机号标记
            fps: 处理帧率
            wait_key: 等待按键的毫秒数

        Returns:
            False 表示用户请求退出，True 表示继续
        """
        self.create_window()

        # 绘制检测结果
        display_frame = self.draw_detections(frame, detections, phone_mask)

        # 添加信息面板（在画面下方，不覆盖）
        phone_count = sum(phone_mask) if phone_mask else 0
        display_frame = self.add_info_panel(
            display_frame, frame_idx, total_frames, phone_count, fps
        )

        # 显示帧
        cv2.imshow(self.window_name, display_frame)

        # 等待按键
        key = cv2.waitKey(wait_key) & 0xFF

        # 处理按键
        if key == ord('q') or key == ord('Q') or key == 27:  # 'q' 或 ESC
            return False
        elif key == ord('p') or key == ord('P'):  # 'p' 暂停
            self._pause()
        elif key == ord('t') or key == ord('T'):  # 't' 切换标签模式
            self._toggle_label_mode()

        return True

    def _toggle_label_mode(self):
        """切换标签显示模式"""
        if self.label_mode == self.LABEL_PHONE:
            self.label_mode = self.LABEL_ALL
            mode_name = "全部显示"
        elif self.label_mode == self.LABEL_ALL:
            self.label_mode = self.LABEL_NONE
            mode_name = "隐藏"
        else:
            self.label_mode = self.LABEL_PHONE
            mode_name = "仅手机号"

        print(f"[可视化] 标签模式切换为: {mode_name}")

    def _pause(self):
        """暂停播放，等待按键继续"""
        print("\n[可视化] 已暂停，按任意键继续...")
        while True:
            key = cv2.waitKey(0) & 0xFF
            if key == ord('q') or key == ord('Q') or key == 27:
                break
            elif key == ord('p') or key == ord('P'):
                print("[可视化] 继续播放...")
                break
            elif key == ord('t') or key == ord('T'):
                # 在暂停时也可以切换标签模式
                self._toggle_label_mode()

    def close(self):
        """关闭可视化窗口"""
        if self.window_created:
            cv2.destroyWindow(self.window_name)
            self.window_created = False
