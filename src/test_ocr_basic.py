#!/usr/bin/env python3
"""
最基础的 PaddleOCR 测试 - 确认 API 调用方式
"""
import cv2
import numpy as np
from paddleocr import PaddleOCR
import paddleocr

print("=" * 80)
print("PaddleOCR 基础功能测试")
print("=" * 80)
print(f"\nPaddleOCR 版本: {paddleocr.__version__}")

# 创建一个简单的测试图像
print("\n创建测试图像...")
img = np.ones((200, 600, 3), dtype=np.uint8) * 255
cv2.putText(img, "13812345678", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
cv2.imwrite("test_basic_ocr.png", img)
print("✓ 已保存测试图像: test_basic_ocr.png")

# 初始化 PaddleOCR
print("\n初始化 PaddleOCR...")
ocr = PaddleOCR(lang='ch', device='cpu')
print("✓ 初始化完成")

# 测试1: 使用文件路径
print("\n" + "=" * 80)
print("测试 1: predict(input='文件路径')")
print("=" * 80)
try:
    result = ocr.predict(input="test_basic_ocr.png")
    print(f"✓ 调用成功")
    print(f"  结果类型: {type(result)}")
    print(f"  结果长度: {len(result) if result else 0}")

    if result:
        for i, res in enumerate(result):
            print(f"\n  结果 {i+1}:")
            print(f"    类型: {type(res)}")

            # 尝试访问 json 属性
            try:
                json_data = res.json
                print(f"    JSON 数据: {json_data}")

                if 'rec_texts' in json_data:
                    print(f"    识别文本: {json_data['rec_texts']}")
                if 'rec_scores' in json_data:
                    print(f"    置信度: {json_data['rec_scores']}")
            except Exception as e:
                print(f"    访问 json 失败: {e}")
                print(f"    原始对象: {res}")
except Exception as e:
    print(f"✗ 调用失败: {e}")
    import traceback
    traceback.print_exc()

# 测试2: 使用 numpy array
print("\n" + "=" * 80)
print("测试 2: predict(input=numpy_array)")
print("=" * 80)
try:
    result = ocr.predict(input=img)
    print(f"✓ 调用成功")
    print(f"  结果类型: {type(result)}")
    print(f"  结果长度: {len(result) if result else 0}")

    if result:
        for i, res in enumerate(result):
            print(f"\n  结果 {i+1}:")
            print(f"    类型: {type(res)}")

            try:
                json_data = res.json
                print(f"    JSON 数据: {json_data}")

                if 'rec_texts' in json_data:
                    print(f"    识别文本: {json_data['rec_texts']}")
            except Exception as e:
                print(f"    访问 json 失败: {e}")
except Exception as e:
    print(f"✗ 调用失败: {e}")
    import traceback
    traceback.print_exc()

# 测试3: 使用 ocr() 方法（旧版 API）
print("\n" + "=" * 80)
print("测试 3: ocr('文件路径') - 旧版 API")
print("=" * 80)
try:
    result = ocr.ocr("test_basic_ocr.png")
    print(f"✓ 调用成功")
    print(f"  结果类型: {type(result)}")
    print(f"  结果: {result}")
except Exception as e:
    print(f"✗ 调用失败: {e}")
    import traceback
    traceback.print_exc()

# 测试4: 使用 ocr() 方法 + numpy array
print("\n" + "=" * 80)
print("测试 4: ocr(numpy_array) - 旧版 API")
print("=" * 80)
try:
    result = ocr.ocr(img)
    print(f"✓ 调用成功")
    print(f"  结果类型: {type(result)}")
    print(f"  结果: {result}")
except Exception as e:
    print(f"✗ 调用失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
