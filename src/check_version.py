#!/usr/bin/env python3
"""
检查 PaddleOCR 版本并测试安装
"""
import sys

print("=" * 60)
print("环境检查")
print("=" * 60)

# 检查 Python 版本
print(f"\nPython 版本: {sys.version}")

# 检查 PaddleOCR
try:
    import paddleocr
    print(f"PaddleOCR 版本: {paddleocr.__version__}")

    # 判断是 2.x 还是 3.x
    version_parts = paddleocr.__version__.split('.')
    major_version = int(version_parts[0])

    if major_version >= 3:
        print("✓ 检测到 PaddleOCR 3.x 版本（本项目已适配）")
    else:
        print("⚠ 检测到 PaddleOCR 2.x 版本（需要升级到 3.x）")
        print("\n升级命令:")
        print("  pip uninstall paddleocr paddlepaddle")
        print("  pip install paddleocr>=3.0.0")

except ImportError:
    print("✗ PaddleOCR 未安装")
    print("\n安装命令:")
    print("  pip install paddleocr>=3.0.0")

# 检查 PaddlePaddle
try:
    import paddle
    print(f"\nPaddlePaddle 版本: {paddle.__version__}")
    print(f"CUDA 支持: {paddle.device.is_compiled_with_cuda()}")
    if paddle.device.is_compiled_with_cuda():
        print(f"当前设备: {paddle.device.get_device()}")
except ImportError:
    print("\n✗ PaddlePaddle 未安装")

# 检查 OpenCV
try:
    import cv2
    print(f"\nOpenCV 版本: {cv2.__version__}")
except ImportError:
    print("\n✗ OpenCV 未安装")

# 检查 NumPy
try:
    import numpy
    print(f"NumPy 版本: {numpy.__version__}")
except ImportError:
    print("✗ NumPy 未安装")

print("\n" + "=" * 60)

# 如果 PaddleOCR 已安装，测试初始化
try:
    import paddleocr
    version_parts = paddleocr.__version__.split('.')
    major_version = int(version_parts[0])

    print("\n测试 PaddleOCR 初始化...")

    if major_version >= 3:
        # PaddleOCR 3.x
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(lang='ch', device='cpu')
        print("✓ PaddleOCR 3.x 初始化成功（使用 device='cpu'）")
    else:
        # PaddleOCR 2.x
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(lang='ch', use_gpu=False, show_log=False)
        print("✓ PaddleOCR 2.x 初始化成功（使用 use_gpu=False）")

    print("\n✓ 所有组件工作正常！")

except Exception as e:
    print(f"\n✗ 初始化失败: {e}")
    print("\n请查看 VERSION_COMPATIBILITY.md 了解详细信息")

print("=" * 60)
