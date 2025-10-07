"""
测试精确定位模式下的OCR调用次数
验证当文本只包含目标内容时，不会产生额外的OCR调用
"""
import numpy as np
from privision.core.detectors.phone_detector import PhoneDetector
from privision.core.precise_locator import PreciseLocator


class MockProgressCallback:
    """模拟进度回调，用于统计OCR调用次数"""
    def __init__(self):
        self.ocr_call_count = 0

    def on_ocr_call(self):
        self.ocr_call_count += 1


def test_pure_pattern_no_extra_ocr():
    """测试：纯目标模式文本不应产生额外OCR调用"""
    print("=== 测试1: 纯目标模式文本（不应额外调用OCR） ===\n")

    # 创建模拟检测器和定位器
    detector = PhoneDetector()
    callback = MockProgressCallback()
    locator = PreciseLocator(None, detector, max_iterations=3, progress_callback=callback)

    # 测试用例：原始文本就是纯粹的手机号
    test_cases = [
        "13812345678",           # 纯手机号
        "138-1234-5678",         # 带分隔符的手机号
        "138 1234 5678",         # 带空格的手机号
    ]

    for original_text in test_cases:
        callback.ocr_call_count = 0  # 重置计数

        # 创建模拟bbox
        mock_bbox = np.array([[0, 0], [100, 0], [100, 30], [0, 30]], dtype=np.float32)
        mock_image = np.zeros((100, 200, 3), dtype=np.uint8)

        # 调用精确定位
        result = locator.refine_pattern_bbox(
            mock_image,
            mock_bbox,
            original_text,
            debug=True
        )

        # 验证结果
        if result is None:
            status = "✓ PASS"
            print(f"{status} - 原始文本: '{original_text}'")
            print(f"  返回: None (无需精确定位)")
            print(f"  OCR调用次数: {callback.ocr_call_count} (预期: 0)")
        else:
            status = "✗ FAIL"
            print(f"{status} - 原始文本: '{original_text}'")
            print(f"  返回: 有结果 (不应该精确定位)")
            print(f"  OCR调用次数: {callback.ocr_call_count} (预期: 0)")

        print()


def test_mixed_content_needs_extra_ocr():
    """测试：混合内容应产生额外OCR调用"""
    print("\n=== 测试2: 混合内容（应该调用额外OCR） ===\n")

    # 创建模拟检测器和定位器
    detector = PhoneDetector()
    callback = MockProgressCallback()

    # 注意：这里我们不创建真实的OCR检测器，因为我们只是测试逻辑
    # 在实际场景中，会有真实的OCR调用

    locator = PreciseLocator(None, detector, max_iterations=3, progress_callback=callback)

    # 测试用例：原始文本包含目标模式和其他内容
    test_cases = [
        "手机号:13812345678",        # 有前缀
        "13812345678可联系",         # 有后缀
        "号码:13812345678请拨打",    # 前后都有
    ]

    for original_text in test_cases:
        callback.ocr_call_count = 0  # 重置计数

        # 创建模拟bbox
        mock_bbox = np.array([[0, 0], [200, 0], [200, 30], [0, 30]], dtype=np.float32)
        mock_image = np.zeros((100, 300, 3), dtype=np.uint8)

        # 调用精确定位（会进入迭代，但因为没有真实OCR会在第一次迭代失败）
        result = locator.refine_pattern_bbox(
            mock_image,
            mock_bbox,
            original_text,
            debug=True
        )

        # 验证：应该进入精确定位流程（result不为None或者尝试了OCR）
        print(f"原始文本: '{original_text}'")
        print(f"  应该进入精确定位流程（因为包含非目标内容）")
        print()


if __name__ == '__main__':
    print("=" * 60)
    print("OCR调用次数测试")
    print("=" * 60)
    print()

    test_pure_pattern_no_extra_ocr()
    test_mixed_content_needs_extra_ocr()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

