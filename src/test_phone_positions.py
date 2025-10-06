#!/usr/bin/env python3
"""
测试 phone_detector.find_phone_positions 的位置映射
"""
from phone_detector import PhoneDetector

def test_phone_positions():
    """测试手机号位置查找"""
    detector = PhoneDetector()

    test_cases = [
        # (文本, 期望的手机号, 期望在原始文本中的起始位置)
        ("来电号码：17563210903", "17563210903", 5),
        ("手机号码: 13812345678", "13812345678", 6),
        ("联系方式 138 1234 5678", "13812345678", 5),  # 有空格的情况
        ("电话:13912345678可联系", "13912345678", 3),
        ("13712345678", "13712345678", 0),
    ]

    print("=== 测试手机号位置查找 ===\n")

    for text, expected_phone, expected_start in test_cases:
        positions = detector.find_phone_positions(text)

        print(f"文本: '{text}'")
        print(f"  期望: 手机号='{expected_phone}', 起始位置={expected_start}")

        if positions:
            phone, start, end = positions[0]
            actual_substr = text[start:end]

            print(f"  实际: 手机号='{phone}', 起始位置={start}, 结束位置={end}")
            print(f"  验证: 原始文本[{start}:{end}] = '{actual_substr}'")

            # 验证位置是否正确（从原始文本中提取）
            # 注意：提取的子串可能包含空格等字符
            cleaned_substr = actual_substr.replace(' ', '').replace('-', '')
            if cleaned_substr == phone:
                print(f"  ✓ 位置映射正确")
            else:
                print(f"  ✗ 位置映射错误: '{actual_substr}' (清理后: '{cleaned_substr}') != '{phone}'")
        else:
            print(f"  ✗ 未找到手机号")

        print()

if __name__ == '__main__':
    test_phone_positions()
