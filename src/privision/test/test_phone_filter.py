#!/usr/bin/env python3
"""
测试手机号过滤功能
验证智能过滤算法是否能正确识别和过滤
"""
from privision.core.detectors.phone_detector import PhoneDetector

print("=" * 80)
print("手机号智能过滤测试")
print("=" * 80)

detector = PhoneDetector()

# 测试用例: (文本, 应该匹配)
test_cases = [
    # 应该匹配的真实手机号
    ("18562828845", True, "独立手机号"),
    ("Phone: 13812345678", True, "带前缀的手机号"),
    ("联系方式: 15912345678", True, "中文前缀"),
    ("138 1234 5678", True, "带空格的手机号"),
    ("138-1234-5678", True, "带横线的手机号"),
    ("17563210903", True, "1开头手机号"),

    # 应该被过滤的误识别
    ("12025091116093686559485N1", False, "长数字串（超过13位）"),
    ("22025091116072886659485N1", False, "2开头的长数字串"),
    ("投诉>>移网网络>>语音问题投诉>>渠...1716052618863.", False, "嵌入文本中的长数字"),
    ("订单号：202509111609368655948", False, "订单号"),
    ("1234567890123", False, "13位连续数字"),
    ("12345678901", False, "1开头但第二位是2"),
    ("11812345678", False, "第二位是1（无效）"),
    ("19912345678", False, "第二位是9但被嵌入长串"),

    # 边界情况
    ("号码13812345678号", True, "前后有汉字"),
    ("13812345678abc", False, "后面紧跟字母"),
    ("abc13812345678", False, "前面紧跟字母"),
    ("13812345678,15912345678", True, "多个手机号"),
]

print("\n开始测试...\n")

passed = 0
failed = 0

for text, should_match, description in test_cases:
    result = detector.contains_phone(text, strict=True)

    status = "✓" if result == should_match else "✗"
    result_text = "匹配" if result else "不匹配"
    expected_text = "应匹配" if should_match else "应过滤"

    if result == should_match:
        passed += 1
        print(f"{status} {description}")
        print(f"   文本: '{text}'")
        print(f"   结果: {result_text} ({expected_text})")
    else:
        failed += 1
        print(f"{status} {description} - 失败!")
        print(f"   文本: '{text}'")
        print(f"   结果: {result_text}, 期望: {expected_text}")

        # 显示找到的手机号
        if result:
            phones = detector.find_phones(text)
            print(f"   找到的手机号: {phones}")

    print()

print("=" * 80)
print(f"测试结果: {passed} 通过, {failed} 失败")
print("=" * 80)

if failed == 0:
    print("\n✓✓✓ 所有测试通过！智能过滤工作正常！")
else:
    print(f"\n⚠ {failed} 个测试失败，需要调整过滤规则")
