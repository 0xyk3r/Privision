#!/usr/bin/env python3
"""
单帧测试工具 - 用于调试OCR和手机号检测
从视频中提取一帧进行详细测试
"""
import cv2
import sys
from privision.core.ocr_detector import OCRDetector
from privision.core.detectors.phone_detector import PhoneDetector


def test_single_frame(video_path: str, frame_number: int = 0, save_debug: bool = True):
    """
    测试视频的单帧

    Args:
        video_path: 视频文件路径
        frame_number: 要测试的帧号（默认第1帧）
        save_debug: 是否保存调试图像
    """
    print("=" * 80)
    print(f"单帧测试工具 - 测试帧号: {frame_number}")
    print("=" * 80)

    # 打开视频
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"✗ 无法打开视频: {video_path}")
        return

    # 跳到指定帧
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print(f"✗ 无法读取帧 {frame_number}")
        return

    print(f"✓ 成功读取帧 {frame_number}")
    print(f"  分辨率: {frame.shape[1]}x{frame.shape[0]}")

    if save_debug:
        cv2.imwrite(f"debug_frame_{frame_number}.png", frame)
        print(f"  已保存: debug_frame_{frame_number}.png")

    # 测试 OCR 检测
    print("\n" + "=" * 80)
    print("OCR 文本检测测试")
    print("=" * 80)

    ocr_detector = OCRDetector(device='cpu')
    detections = ocr_detector.detect_text(frame)

    print(f"\n检测到 {len(detections)} 个文本区域:")

    if len(detections) == 0:
        print("\n⚠ 警告: 没有检测到任何文本！")
        print("  可能的原因:")
        print("  1. 图像质量太低")
        print("  2. 文字太小或太模糊")
        print("  3. 文字颜色与背景对比度不够")
        print("  4. PaddleOCR 模型不适合这种类型的文本")
    else:
        for i, (bbox, text, confidence) in enumerate(detections):
            print(f"\n文本区域 {i+1}:")
            print(f"  内容: '{text}'")
            print(f"  置信度: {confidence:.4f}")
            print(f"  坐标: {bbox.tolist()}")

            # 在图像上标注
            if save_debug:
                cv2.polylines(frame, [bbox], True, (0, 255, 0), 2)
                x, y = bbox[0]
                cv2.putText(frame, f"{i+1}", (int(x), int(y)-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # 保存标注后的图像
    if save_debug and len(detections) > 0:
        cv2.imwrite(f"debug_frame_{frame_number}_annotated.png", frame)
        print(f"\n✓ 已保存标注图像: debug_frame_{frame_number}_annotated.png")

    # 测试手机号检测
    print("\n" + "=" * 80)
    print("手机号匹配测试")
    print("=" * 80)

    phone_detector = PhoneDetector()
    phone_found = False

    for i, (bbox, text, confidence) in enumerate(detections):
        if phone_detector.contains_phone(text):
            phones = phone_detector.find_phones(text)
            print(f"\n✓ 在文本区域 {i+1} 中找到手机号:")
            print(f"  原文本: '{text}'")
            print(f"  手机号: {phones}")
            phone_found = True
        else:
            # 检查是否包含数字
            if any(c.isdigit() for c in text):
                print(f"\n  文本区域 {i+1} 包含数字但不是手机号:")
                print(f"    '{text}'")

    if not phone_found:
        print("\n⚠ 警告: 未检测到手机号！")
        print("\n可能的原因:")
        print("  1. OCR 识别错误（数字被识别成字母）")
        print("  2. 手机号被分割成多个文本区域")
        print("  3. 手机号格式不符合规则（需要连续11位数字）")
        print("\n建议:")
        print("  1. 查看上面的 OCR 检测结果，确认文本内容")
        print("  2. 查看标注图像，确认文本检测框是否正确")
        print("  3. 如果数字被识别成字母，可能需要调整 OCR 参数")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python test_single_frame.py <视频路径> [帧号]")
        print("\n示例:")
        print("  python test_single_frame.py input.mp4")
        print("  python test_single_frame.py input.mp4 100")
        sys.exit(1)

    video_path = sys.argv[1]
    frame_number = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    test_single_frame(video_path, frame_number)
