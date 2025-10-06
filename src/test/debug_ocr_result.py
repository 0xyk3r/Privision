#!/usr/bin/env python3
"""
详细调试 PaddleOCR 3.2 的返回格式
"""
import numpy as np
import cv2
from paddleocr import PaddleOCR
import json

print("=" * 80)
print("PaddleOCR 3.2 API 详细调试")
print("=" * 80)

# 检查版本
import paddleocr
print(f"\nPaddleOCR 版本: {paddleocr.__version__}")

# 创建测试图像 - 包含手机号
test_img = np.ones((200, 600, 3), dtype=np.uint8) * 255
cv2.putText(test_img, "Phone: 13812345678", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
cv2.putText(test_img, "Contact: 15912345678", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)

# 保存测试图像
cv2.imwrite("test_ocr_image.png", test_img)
print("\n✓ 已保存测试图像: test_ocr_image.png")

print("\n初始化 PaddleOCR...")
try:
    ocr = PaddleOCR(lang='ch', device='cpu')
    print("✓ 初始化成功")
except Exception as e:
    print(f"✗ 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 80)
print("测试 ocr.ocr() 方法")
print("=" * 80)

try:
    result = ocr.ocr(test_img)

    print(f"\n[返回值基本信息]")
    print(f"  类型: {type(result)}")
    print(f"  长度: {len(result) if result else 'None'}")

    if result:
        print(f"\n[第一层结构]")
        print(f"  result[0] 类型: {type(result[0])}")
        print(f"  result[0] 长度: {len(result[0]) if result[0] else 'None'}")

        if result[0]:
            print(f"\n[第二层结构 - 第一个检测结果]")
            first_item = result[0][0]
            print(f"  result[0][0] 类型: {type(first_item)}")
            print(f"  result[0][0] 内容: {first_item}")

            if isinstance(first_item, (list, tuple)) and len(first_item) >= 2:
                print(f"\n[坐标信息]")
                bbox = first_item[0]
                print(f"  bbox 类型: {type(bbox)}")
                print(f"  bbox 内容: {bbox}")

                if bbox:
                    print(f"  bbox 长度: {len(bbox)}")
                    if len(bbox) > 0:
                        print(f"  bbox[0] 类型: {type(bbox[0])}")
                        print(f"  bbox[0] 内容: {bbox[0]}")

                print(f"\n[文本和置信度信息]")
                text_conf = first_item[1]
                print(f"  text_conf 类型: {type(text_conf)}")
                print(f"  text_conf 内容: {text_conf}")

                if isinstance(text_conf, (list, tuple)) and len(text_conf) >= 2:
                    print(f"  文本: {text_conf[0]}")
                    print(f"  置信度: {text_conf[1]}")

    print(f"\n[完整结果 JSON 格式]")
    # 尝试转换为可序列化的格式
    def make_serializable(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (list, tuple)):
            return [make_serializable(item) for item in obj]
        else:
            return obj

    serializable_result = make_serializable(result)
    print(json.dumps(serializable_result, indent=2, ensure_ascii=False))

    print(f"\n[遍历所有检测结果]")
    if result and result[0]:
        for i, line in enumerate(result[0]):
            print(f"\n  检测 {i+1}:")
            print(f"    原始数据: {line}")

            try:
                bbox = line[0]
                text_info = line[1]

                print(f"    坐标类型: {type(bbox)}")
                print(f"    坐标: {bbox}")

                if isinstance(text_info, (list, tuple)):
                    text = text_info[0]
                    conf = text_info[1]
                    print(f"    文本: {text}")
                    print(f"    置信度: {conf}")
                else:
                    print(f"    文本信息类型: {type(text_info)}")
                    print(f"    文本信息: {text_info}")

            except Exception as e:
                print(f"    解析出错: {e}")
                import traceback
                traceback.print_exc()

except Exception as e:
    print(f"\n✗ ocr() 调用失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("测试 ocr.predict() 方法（如果存在）")
print("=" * 80)

if hasattr(ocr, 'predict'):
    try:
        result = ocr.predict("test_ocr_image.png")
        print(f"\n✓ predict() 调用成功")
        print(f"  结果类型: {type(result)}")
        print(f"  结果: {result}")
    except Exception as e:
        print(f"\n✗ predict() 调用失败: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n✗ ocr 对象没有 predict() 方法")

print("\n" + "=" * 80)
print("可用的方法和属性")
print("=" * 80)
methods = [m for m in dir(ocr) if not m.startswith('_')]
for method in methods:
    print(f"  - {method}")

print("\n" + "=" * 80)
