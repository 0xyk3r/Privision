#!/usr/bin/env python3
"""
测试 PaddleOCR API 调用方式
用于确定正确的调用方法和返回格式
"""
import numpy as np
import cv2
from paddleocr import PaddleOCR

print("=" * 60)
print("PaddleOCR API 测试")
print("=" * 60)

# 检查版本
import paddleocr
print(f"\nPaddleOCR 版本: {paddleocr.__version__}")

# 创建测试图像
test_img = np.ones((100, 400, 3), dtype=np.uint8) * 255
cv2.putText(test_img, "13812345678", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2)

print("\n初始化 PaddleOCR...")
try:
    ocr = PaddleOCR(lang='ch', device='cpu')
    print("✓ 初始化成功")
except Exception as e:
    print(f"✗ 初始化失败: {e}")
    exit(1)

print("\n测试不同的调用方式:")

# 测试 1: ocr() 方法不带参数
print("\n[测试 1] ocr(image) - 不带任何参数")
try:
    result = ocr.ocr(test_img)
    print(f"✓ 成功")
    print(f"  结果类型: {type(result)}")
    print(f"  结果长度: {len(result) if result else 0}")
    if result and result[0]:
        print(f"  第一个元素类型: {type(result[0])}")
        print(f"  第一个元素: {result[0][0] if result[0] else 'None'}")
except Exception as e:
    print(f"✗ 失败: {e}")

# 测试 2: ocr() 方法带 cls 参数
print("\n[测试 2] ocr(image, cls=True)")
try:
    result = ocr.ocr(test_img, cls=True)
    print(f"✓ 成功")
    print(f"  结果: {result}")
except Exception as e:
    print(f"✗ 失败: {e}")

# 测试 3: predict() 方法
print("\n[测试 3] predict(image)")
try:
    result = ocr.predict(test_img)
    print(f"✓ 成功")
    print(f"  结果类型: {type(result)}")
    print(f"  结果: {result}")
except Exception as e:
    print(f"✗ 失败: {e}")

# 测试 4: 检查可用方法
print("\n[可用方法]")
methods = [m for m in dir(ocr) if not m.startswith('_')]
for method in methods[:10]:  # 只显示前10个
    print(f"  - {method}")

print("\n" + "=" * 60)
