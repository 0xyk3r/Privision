"""
OCR文本检测和识别模块
基于PaddleOCR 3.x实现文本区域检测和内容识别
"""
from typing import List, Tuple, Optional
import numpy as np
from paddleocr import PaddleOCR
import cv2


class OCRDetector:
    """基于PaddleOCR 3.x的文本检测器"""

    def __init__(self, device: str = 'cpu', lang: str = 'ch'):
        """
        初始化OCR检测器

        Args:
            device: 计算设备，格式为 'cpu' 或 'gpu:0', 'gpu:1' 等
            lang: 语言，默认'ch'表示中英文
        """
        # 初始化PaddleOCR 3.x
        # PaddleOCR接受的device格式: "cpu" 或 "gpu:0"
        print(f"Initializing Detector，device: {device}, lang: {lang}")

        self.ocr = PaddleOCR(
            lang=lang,
            device=device,
            # 禁用一些不需要的功能以提高速度
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False
        )

    def detect_text(self, image: np.ndarray) -> List[Tuple[np.ndarray, str, float]]:
        """
        检测图像中的文本并返回位置和内容

        Args:
            image: 输入图像（numpy数组，BGR格式）

        Returns:
            [(坐标数组, 文本内容, 置信度), ...]
            坐标数组格式: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] (四个顶点)
        """
        if image is None or image.size == 0:
            return []

        try:
            # PaddleOCR 3.x 使用 predict() 方法
            result = self.ocr.predict(input=image)

            if not result:
                return []

            # PaddleOCR 3.x 返回结果对象列表
            detections = []
            for res in result:
                # 访问 json 属性获取结果字典
                # PaddleOCR 3.2 的结构是 res.json['res']
                json_data = res.json.get('res', res.json)

                # 提取检测框、文本和置信度
                dt_polys = json_data.get('dt_polys', [])
                rec_texts = json_data.get('rec_texts', [])
                rec_scores = json_data.get('rec_scores', [])

                # 组合结果
                for bbox, text, score in zip(dt_polys, rec_texts, rec_scores):
                    # bbox 已经是 numpy 数组，确保是整数类型
                    bbox_int = np.array(bbox, dtype=np.int32)
                    detections.append((bbox_int, text, score))

            return detections

        except Exception as e:
            print(f"OCR检测出错: {e}")
            import traceback
            traceback.print_exc()
            return []

    def detect_text_with_filter(
        self,
        image: np.ndarray,
        min_confidence: float = 0.5
    ) -> List[Tuple[np.ndarray, str, float]]:
        """
        检测文本并过滤低置信度结果

        Args:
            image: 输入图像
            min_confidence: 最小置信度阈值

        Returns:
            [(坐标数组, 文本内容, 置信度), ...]
        """
        detections = self.detect_text(image)
        return [
            (bbox, text, conf)
            for bbox, text, conf in detections
            if conf >= min_confidence
        ]

    @staticmethod
    def get_bbox_rect(bbox: np.ndarray) -> Tuple[int, int, int, int]:
        """
        从四顶点坐标获取矩形边界框

        Args:
            bbox: 四个顶点坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]

        Returns:
            (x_min, y_min, x_max, y_max)
        """
        x_coords = bbox[:, 0]
        y_coords = bbox[:, 1]
        return (
            int(np.min(x_coords)),
            int(np.min(y_coords)),
            int(np.max(x_coords)),
            int(np.max(y_coords))
        )


if __name__ == '__main__':
    # 简单测试 PaddleOCR 3.x
    print("=== OCR检测器初始化测试 (PaddleOCR 3.x) ===")

    # 检查版本
    import paddleocr
    print(f"PaddleOCR 版本: {paddleocr.__version__}")

    try:
        detector = OCRDetector(device='cpu')
        print("✓ OCR检测器初始化成功！")

        # 创建测试图像
        test_img = np.ones((100, 400, 3), dtype=np.uint8) * 255
        cv2.putText(
            test_img,
            "Phone: 13812345678",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 0),
            2
        )

        print("\n测试文本检测...")
        results = detector.detect_text(test_img)
        print(f"✓ 检测到 {len(results)} 个文本区域")

        for i, (bbox, text, conf) in enumerate(results):
            print(f"\n区域 {i+1}:")
            print(f"  文本: {text}")
            print(f"  置信度: {conf:.4f}")
            print(f"  坐标: {bbox.tolist()}")

    except Exception as e:
        print(f"✗ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        print("\n请确保已安装 PaddleOCR 3.x: pip install paddleocr>=3.0.0")
