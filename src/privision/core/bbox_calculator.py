"""
边界框计算模块
根据文本中的子串位置，计算子串在原始边界框中的精确位置
"""
import numpy as np
from typing import Tuple


class BboxCalculator:
    """边界框计算器 - 用于从整行文本的bbox中提取子串的bbox"""

    @staticmethod
    def calculate_substring_bbox(
        original_bbox: np.ndarray,
        full_text: str,
        substring_start: int,
        substring_end: int,
        padding_ratio: float = 0.05
    ) -> np.ndarray:
        """
        根据子串在文本中的字符位置，按比例计算子串的边界框

        注意：此方法假设字符均匀分布，适用于等宽字体或作为初始估算
        对于非等宽字体，建议配合迭代验证使用（见 PreciseLocator）

        Args:
            original_bbox: 原始文本的四个顶点坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            full_text: 完整文本内容
            substring_start: 子串起始位置（字符索引）
            substring_end: 子串结束位置（字符索引，不包含）
            padding_ratio: 边界框的扩展比例（相对于子串宽度）

        Returns:
            子串的四个顶点坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        """
        text_length = len(full_text)
        if text_length == 0 or substring_start >= substring_end:
            return original_bbox.copy()

        # 计算子串在文本中的相对位置（0-1之间）
        start_ratio = substring_start / text_length
        end_ratio = substring_end / text_length

        # 添加padding（基于子串宽度的比例扩展）
        substring_width_ratio = end_ratio - start_ratio
        padding_size = substring_width_ratio * padding_ratio

        start_ratio = max(0.0, start_ratio - padding_size)
        end_ratio = min(1.0, end_ratio + padding_size)

        # 对于四边形bbox，通常顺序为：
        # bbox[0] - 左上角, bbox[1] - 右上角
        # bbox[2] - 右下角, bbox[3] - 左下角
        # 沿文本方向（水平从左到右）进行切分

        # 计算左边界（start_ratio位置的点）
        left_top = BboxCalculator._interpolate_point(
            original_bbox[0], original_bbox[1], start_ratio
        )
        left_bottom = BboxCalculator._interpolate_point(
            original_bbox[3], original_bbox[2], start_ratio
        )

        # 计算右边界（end_ratio位置的点）
        right_top = BboxCalculator._interpolate_point(
            original_bbox[0], original_bbox[1], end_ratio
        )
        right_bottom = BboxCalculator._interpolate_point(
            original_bbox[3], original_bbox[2], end_ratio
        )

        # 构建子串的bbox（保持顺时针或逆时针顺序）
        substring_bbox = np.array([
            left_top,
            right_top,
            right_bottom,
            left_bottom
        ], dtype=np.int32)

        return substring_bbox

    @staticmethod
    def _interpolate_point(
        point1: np.ndarray,
        point2: np.ndarray,
        ratio: float
    ) -> np.ndarray:
        """
        在两点之间按比例插值

        Args:
            point1: 起始点 [x, y]
            point2: 结束点 [x, y]
            ratio: 插值比例（0-1之间，0返回point1，1返回point2）

        Returns:
            插值后的点 [x, y]
        """
        return point1 + (point2 - point1) * ratio

    @staticmethod
    def adjust_bbox_horizontally(
        bbox: np.ndarray,
        left_shift_ratio: float = 0.0,
        right_shift_ratio: float = 0.0
    ) -> np.ndarray:
        """
        水平方向调整边界框（用于迭代优化）

        Args:
            bbox: 四个顶点坐标
            left_shift_ratio: 左边界移动比例（正值向右移，负值向左移）
            right_shift_ratio: 右边界移动比例（正值向右移，负值向左移）

        Returns:
            调整后的bbox
        """
        # 计算bbox的宽度向量（从左到右）
        width_vector_top = bbox[1] - bbox[0]
        width_vector_bottom = bbox[2] - bbox[3]

        # 调整左边界
        new_left_top = bbox[0] + width_vector_top * left_shift_ratio
        new_left_bottom = bbox[3] + width_vector_bottom * left_shift_ratio

        # 调整右边界
        new_right_top = bbox[1] + width_vector_top * right_shift_ratio
        new_right_bottom = bbox[2] + width_vector_bottom * right_shift_ratio

        return np.array([
            new_left_top,
            new_right_top,
            new_right_bottom,
            new_left_bottom
        ], dtype=np.int32)

    @staticmethod
    def crop_image_by_bbox(image: np.ndarray, bbox: np.ndarray) -> np.ndarray:
        """
        根据bbox裁剪图像（提取矩形区域）

        Args:
            image: 原始图像
            bbox: 四个顶点坐标

        Returns:
            裁剪后的图像
        """
        # 获取矩形边界
        x_coords = bbox[:, 0]
        y_coords = bbox[:, 1]
        x_min, y_min = int(np.min(x_coords)), int(np.min(y_coords))
        x_max, y_max = int(np.max(x_coords)), int(np.max(y_coords))

        # 边界检查
        h, w = image.shape[:2]
        x_min = max(0, min(x_min, w))
        y_min = max(0, min(y_min, h))
        x_max = max(0, min(x_max, w))
        y_max = max(0, min(y_max, h))

        if x_min >= x_max or y_min >= y_max:
            return np.zeros((1, 1, 3), dtype=np.uint8)

        return image[y_min:y_max, x_min:x_max].copy()


if __name__ == '__main__':
    print("=== BboxCalculator 测试 ===\n")

    # 测试用例：模拟一个水平文本框
    full_text = "手机号码: 13812345678"
    print(f"完整文本: '{full_text}'")
    print(f"文本长度: {len(full_text)} 字符\n")

    # 模拟水平bbox（宽160像素，高20像素）
    original_bbox = np.array([
        [10, 10],   # 左上
        [170, 10],  # 右上
        [170, 30],  # 右下
        [10, 30]    # 左下
    ], dtype=np.int32)

    print(f"原始bbox: {original_bbox.tolist()}\n")

    # 查找目标位置
    pattern_start = full_text.find("13812345678")
    pattern_end = pattern_start + 11
    print(f"目标位置: 索引 [{pattern_start}, {pattern_end})")
    print(f"目标号: '{full_text[pattern_start:pattern_end]}'")
    print(f"目标占比: {pattern_start}/{len(full_text)} 到 {pattern_end}/{len(full_text)}\n")

    # 计算目标的bbox
    pattern_bbox = BboxCalculator.calculate_substring_bbox(
        original_bbox,
        full_text,
        pattern_start,
        pattern_end,
        padding_ratio=0.05
    )

    print(f"计算得到的目标bbox: {pattern_bbox.tolist()}")
    print(f"X 范围: {pattern_bbox[0][0]} - {pattern_bbox[1][0]}")
    print(f"Y 范围: {pattern_bbox[0][1]} - {pattern_bbox[2][1]}\n")

    # 测试边界调整
    print("=== 测试边界调整 ===")
    adjusted_bbox = BboxCalculator.adjust_bbox_horizontally(
        pattern_bbox,
        left_shift_ratio=0.1,   # 左边界向右移动10%
        right_shift_ratio=-0.05  # 右边界向左移动5%
    )
    print(f"调整后bbox: {adjusted_bbox.tolist()}")
    print(f"X 范围: {adjusted_bbox[0][0]} - {adjusted_bbox[1][0]}")
