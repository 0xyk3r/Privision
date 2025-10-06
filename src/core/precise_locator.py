"""
精确定位模块
通过迭代验证OCR结果，精确定位手机号在图像中的位置
"""
import numpy as np
from typing import Tuple, Optional
import sys
from pathlib import Path
from src.core.bbox_calculator import BboxCalculator
from src.core.phone_detector import PhoneDetector

class PreciseLocator:
    """精确定位器 - 通过迭代验证精确定位手机号"""

    def __init__(self, ocr_detector, max_iterations: int = 3):
        """
        初始化精确定位器

        Args:
            ocr_detector: OCR检测器实例
            max_iterations: 最大迭代次数
        """
        self.ocr_detector = ocr_detector
        self.phone_detector = PhoneDetector()
        self.max_iterations = max_iterations

    def refine_phone_bbox(
        self,
        image: np.ndarray,
        original_bbox: np.ndarray,
        original_text: str,
        debug: bool = False
    ) -> Optional[Tuple[np.ndarray, str]]:
        """
        精确定位手机号的bbox

        策略：
        1. 在原始文本中找到手机号的字符位置
        2. 按字符比例从原始bbox中切分出初始手机号bbox
        3. 对切分区域进行OCR验证
        4. 根据验证结果调整边界：
           - 若识别内容包含前缀（如"手机号:"）→ 左边界右移
           - 若识别内容包含后缀（如"可联系"）→ 右边界左移
           - 若只识别到部分手机号 → 扩展边界
           - 若精确识别到手机号 → 返回当前bbox
        5. 最多迭代max_iterations次

        Args:
            image: 原始图像
            original_bbox: 原始文本的bbox
            original_text: 原始文本内容（包含手机号）
            debug: 是否输出调试信息

        Returns:
            (精确的手机号bbox, 识别到的文本) 元组，如果失败返回None
        """
        # 1. 查找手机号在原始文本中的位置
        phone_positions = self.phone_detector.find_phone_positions(original_text)
        if not phone_positions:
            if debug:
                print(f"  [PreciseLocator] 未在文本中找到手机号: '{original_text}'")
            return None

        # 取第一个手机号（通常只有一个）
        phone_number, phone_start, phone_end = phone_positions[0]

        if debug:
            print(f"  [PreciseLocator] 原始文本: '{original_text}' (长度: {len(original_text)})")
            print(f"  [PreciseLocator] 手机号: '{phone_number}' 位置: [{phone_start}, {phone_end})")
            print(f"  [PreciseLocator] 原始bbox: {original_bbox.tolist()}")

        # 2. 计算初始bbox（按字符比例切分）
        current_bbox = BboxCalculator.calculate_substring_bbox(
            original_bbox,
            original_text,
            phone_start,
            phone_end,
            padding_ratio=0.05  # 减小padding，避免包含过多区域
        )

        if debug:
            print(f"  [PreciseLocator] 初始切分bbox: {current_bbox.tolist()}")

        # 3. 迭代验证和调整
        for iteration in range(self.max_iterations):
            # 裁剪图像区域
            cropped_image = BboxCalculator.crop_image_by_bbox(image, current_bbox)

            if cropped_image.size == 0:
                if debug:
                    print(f"  [PreciseLocator] 迭代 {iteration + 1}: 裁剪区域为空")
                break

            # 对裁剪区域进行OCR识别
            detections = self.ocr_detector.detect_text(cropped_image)

            if not detections:
                if debug:
                    print(f"  [PreciseLocator] 迭代 {iteration + 1}: OCR未识别到文本，停止迭代")
                break

            # 取置信度最高的识别结果
            detections_sorted = sorted(detections, key=lambda x: x[2], reverse=True)
            _, detected_text, confidence = detections_sorted[0]

            if debug:
                print(f"  [PreciseLocator] 迭代 {iteration + 1}: 识别到 '{detected_text}' (置信度: {confidence:.3f})")

            # 分析识别结果
            adjustment = self._analyze_detection(phone_number, detected_text)

            if adjustment == "perfect":
                # 精确匹配，返回当前bbox和识别的文本
                if debug:
                    print(f"  [PreciseLocator] ✓ 精确定位成功！")
                    print(f"  [PreciseLocator]   原始: '{original_text}' → 精确定位后: '{detected_text}'")
                    print(f"  [PreciseLocator]   最终bbox: {current_bbox.tolist()}")
                return current_bbox, detected_text

            elif adjustment == "expand_left":
                # 需要向左扩展（手机号被截断左侧）
                if debug:
                    print(f"  [PreciseLocator] 调整: 向左扩展")
                current_bbox = BboxCalculator.adjust_bbox_horizontally(
                    current_bbox,
                    left_shift_ratio=-0.15,
                    right_shift_ratio=0.0
                )

            elif adjustment == "expand_right":
                # 需要向右扩展（手机号被截断右侧）
                if debug:
                    print(f"  [PreciseLocator] 调整: 向右扩展")
                current_bbox = BboxCalculator.adjust_bbox_horizontally(
                    current_bbox,
                    left_shift_ratio=0.0,
                    right_shift_ratio=0.15
                )

            elif adjustment == "shrink_left":
                # 需要右移左边界（包含了前缀）
                if debug:
                    print(f"  [PreciseLocator] 调整: 左边界右移")
                current_bbox = BboxCalculator.adjust_bbox_horizontally(
                    current_bbox,
                    left_shift_ratio=0.1,
                    right_shift_ratio=0.0
                )

            elif adjustment == "shrink_right":
                # 需要左移右边界（包含了后缀）
                if debug:
                    print(f"  [PreciseLocator] 调整: 右边界左移")
                current_bbox = BboxCalculator.adjust_bbox_horizontally(
                    current_bbox,
                    left_shift_ratio=0.0,
                    right_shift_ratio=-0.1
                )

            else:
                # 无法判断如何调整，返回当前bbox
                if debug:
                    print(f"  [PreciseLocator] 无法进一步优化，使用当前结果")
                last_detected = detected_text if 'detected_text' in locals() else phone_number
                return current_bbox, last_detected

        # 迭代结束，返回当前bbox（即使没有完美匹配，也返回最后的结果）
        if debug:
            print(f"  [PreciseLocator] 达到最大迭代次数，返回当前结果")
        # 返回当前bbox和最后识别到的文本（如果有的话）
        last_detected = detected_text if 'detected_text' in locals() else phone_number
        return current_bbox, last_detected

    def _analyze_detection(
        self,
        target_phone: str,
        detected_text: str
    ) -> str:
        """
        分析OCR识别结果，决定如何调整bbox

        Args:
            target_phone: 目标手机号（11位）
            detected_text: 当前识别到的文本

        Returns:
            调整策略: "perfect", "expand_left", "expand_right",
                     "shrink_left", "shrink_right", "unknown"
        """
        # 清理文本（去除空格、特殊字符）
        import re
        cleaned_detected = re.sub(r'[\s\-\u3000]', '', detected_text)
        cleaned_target = re.sub(r'[\s\-\u3000]', '', target_phone)

        # 情况1: 精确匹配（只包含手机号）
        if cleaned_detected == cleaned_target:
            return "perfect"

        # 情况2: 识别结果包含完整手机号，但有额外内容
        if cleaned_target in cleaned_detected:
            phone_pos = cleaned_detected.find(cleaned_target)

            # 手机号前面有其他内容 → 需要右移左边界
            if phone_pos > 0:
                return "shrink_left"

            # 手机号后面有其他内容 → 需要左移右边界
            if phone_pos + len(cleaned_target) < len(cleaned_detected):
                return "shrink_right"

            # 理论上不应该到这里
            return "perfect"

        # 情况3: 只识别到部分手机号（被截断）
        # 检查是否是手机号的前缀或后缀
        if len(cleaned_detected) > 0 and len(cleaned_detected) < len(cleaned_target):
            # 是手机号的前缀 → 右边被截断，需要向右扩展
            if cleaned_target.startswith(cleaned_detected):
                return "expand_right"

            # 是手机号的后缀 → 左边被截断，需要向左扩展
            if cleaned_target.endswith(cleaned_detected):
                return "expand_left"

        # 情况4: 无法判断（可能是识别错误）
        # 尝试模糊匹配：检查是否大部分数字匹配
        phone_digits = set(cleaned_target)
        detected_digits = set(c for c in cleaned_detected if c.isdigit())

        if len(phone_digits & detected_digits) >= 8:  # 至少8个数字匹配
            # 可能是识别到了手机号但有些字符错误
            # 保守处理，返回perfect（使用当前结果）
            return "perfect"

        return "unknown"


if __name__ == '__main__':
    print("=== PreciseLocator 测试 ===\n")

    # 测试 _analyze_detection 方法
    locator = PreciseLocator(None, max_iterations=3)

    test_cases = [
        ("13812345678", "13812345678", "perfect"),
        ("13812345678", "手机号:13812345678", "shrink_left"),
        ("13812345678", "13812345678可联系", "shrink_right"),
        ("13812345678", "号码:13812345678请拨打", "shrink_left"),  # 应优先处理左边
        ("13812345678", "138123456", "expand_right"),
        ("13812345678", "12345678", "expand_left"),
        ("13812345678", "138 1234 5678", "perfect"),  # 带空格也应该匹配
        ("13812345678", "无关文本", "unknown"),
    ]

    print("测试识别结果分析:")
    for target, detected, expected in test_cases:
        result = locator._analyze_detection(target, detected)
        status = "✓" if result == expected else "✗"
        print(f"{status} 目标: '{target}' | 识别: '{detected}' | 预期: {expected} | 结果: {result}")
