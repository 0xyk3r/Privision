#!/usr/bin/env python3
"""
快速测试修复后的 OCR 检测器
"""
import cv2
import numpy as np
from ocr_detector import OCRDetector
from phone_detector import PhoneDetector

print("=" * 80)
print("快速测试 - OCR 和手机号检测")
print("=" * 80)

# 创建测试图像
img = np.ones((200, 600, 3), dtype=np.uint8) * 255
cv2.putText(img, "Phone: 13812345678", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2)
cv2.putText(img, "Tel: 15912345678", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2)

print("\n✓ 创建测试图像（包含两个手机号）")

# 测试 OCR
print("\n测试 OCR 检测器...")
ocr = OCRDetector(use_gpu=False)
detections = ocr.detect_text(img)

print(f"\n✓ OCR 检测到 {len(detections)} 个文本区域:")
for i, (bbox, text, confidence) in enumerate(detections):
    print(f"  [{i+1}] 文本: '{text}' (置信度: {confidence:.4f})")

# 测试手机号匹配
print("\n测试手机号匹配...")
phone_detector = PhoneDetector()
phone_count = 0

for bbox, text, confidence in detections:
    if phone_detector.contains_phone(text):
        phones = phone_detector.find_phones(text)
        print(f"  ✓ 找到手机号: {phones} (原文本: '{text}')")
        phone_count += 1

print(f"\n结果: 共检测到 {phone_count} 个手机号")

if phone_count > 0:
    print("\n✓✓✓ 测试成功！OCR 和手机号检测都工作正常！")
else:
    print("\n✗ 警告: 未检测到手机号")

print("=" * 80)
