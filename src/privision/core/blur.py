"""
打码效果模块
提供多种打码方式的统一接口
"""
import cv2
import numpy as np
from typing import Literal


def apply_blur(
    image: np.ndarray,
    bbox: np.ndarray,
    method: Literal['gaussian', 'pixelate', 'black'] = 'gaussian',
    strength: int = 51
) -> np.ndarray:
    """
    在指定区域应用打码效果

    Args:
        image: 原始图像
        bbox: 四个顶点坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        method: 打码方式 (gaussian, pixelate, black)
        strength: 模糊强度 (仅对gaussian有效)

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
    if method == 'gaussian':
        # 高斯模糊
        # 确保strength为奇数
        if strength % 2 == 0:
            strength += 1
        blurred_roi = cv2.GaussianBlur(roi, (strength, strength), 0)
    elif method == 'pixelate':
        # 像素化（马赛克）
        small = cv2.resize(roi, (10, 10), interpolation=cv2.INTER_LINEAR)
        blurred_roi = cv2.resize(small, (roi.shape[1], roi.shape[0]), interpolation=cv2.INTER_NEAREST)
    elif method == 'black':
        # 黑色遮挡
        blurred_roi = np.zeros_like(roi)
    else:
        # 默认使用高斯模糊
        if strength % 2 == 0:
            strength += 1
        blurred_roi = cv2.GaussianBlur(roi, (strength, strength), 0)

    # 替换区域
    result = image.copy()
    result[y_min:y_max, x_min:x_max] = blurred_roi

    return result
