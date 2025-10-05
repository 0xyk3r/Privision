"""
手机号检测模块
用于识别和定位中国大陆11位手机号
"""
import re
from typing import List, Tuple


class PhoneDetector:
    """中国大陆手机号检测器"""

    # 中国大陆手机号正则：1开头，第二位3-9，后面9位数字，共11位
    # 使用边界匹配，确保是独立的11位数字
    PHONE_PATTERN = re.compile(r'\b1[3-9]\d{9}\b')

    # 严格模式：手机号前后必须是非数字字符或字符串边界
    PHONE_PATTERN_STRICT = re.compile(r'(?<!\d)1[3-9]\d{9}(?!\d)')

    @classmethod
    def contains_phone(cls, text: str, strict: bool = True) -> bool:
        """
        检查文本中是否包含手机号

        Args:
            text: 待检测的文本
            strict: 是否使用严格模式（排除长数字串中的片段）

        Returns:
            是否包含手机号
        """
        if not text:
            return False

        # 移除空格、横线等分隔符后再匹配
        cleaned_text = re.sub(r'[\s\-\u3000]', '', text)

        # 使用严格模式或普通模式
        pattern = cls.PHONE_PATTERN_STRICT if strict else cls.PHONE_PATTERN
        matches = pattern.findall(cleaned_text)

        if not matches:
            return False

        # 额外过滤：检查是否是超长数字串的一部分
        for match in matches:
            if cls._is_valid_phone_context(cleaned_text, match):
                return True

        return False

    @classmethod
    def _is_valid_phone_context(cls, text: str, phone: str) -> bool:
        """
        验证手机号的上下文是否合理

        Args:
            text: 完整文本
            phone: 匹配到的手机号

        Returns:
            是否是有效的手机号上下文
        """
        # 查找手机号在文本中的位置
        pos = text.find(phone)
        if pos == -1:
            return False

        # 检查前后是否有字母或过多数字
        # 如果前面紧跟着是数字，可能是长数字串的一部分
        if pos > 0 and text[pos - 1].isdigit():
            return False

        # 如果后面紧跟着是数字，可能是长数字串的一部分
        if pos + len(phone) < len(text) and text[pos + len(phone)].isdigit():
            return False

        # 检查文本中连续数字的长度
        # 提取包含手机号的连续数字串
        start = pos
        while start > 0 and text[start - 1].isdigit():
            start -= 1

        end = pos + len(phone)
        while end < len(text) and text[end].isdigit():
            end += 1

        digit_sequence = text[start:end]

        # 如果连续数字超过13位，很可能不是手机号
        if len(digit_sequence) > 13:
            return False

        return True

    @classmethod
    def find_phones(cls, text: str) -> List[str]:
        """
        查找文本中的所有手机号

        Args:
            text: 待检测的文本

        Returns:
            手机号列表
        """
        if not text:
            return []
        # 移除空格、横线等分隔符后再匹配
        cleaned_text = re.sub(r'[\s\-\u3000]', '', text)
        return cls.PHONE_PATTERN.findall(cleaned_text)

    @classmethod
    def find_phone_positions(cls, text: str) -> List[Tuple[str, int, int]]:
        """
        查找文本中所有手机号及其位置

        Args:
            text: 待检测的文本

        Returns:
            (手机号, 起始位置, 结束位置) 的列表
        """
        if not text:
            return []
        # 移除空格、横线等分隔符后再匹配
        cleaned_text = re.sub(r'[\s\-\u3000]', '', text)
        results = []
        for match in cls.PHONE_PATTERN.finditer(cleaned_text):
            results.append((match.group(), match.start(), match.end()))
        return results


if __name__ == '__main__':
    # 测试用例
    detector = PhoneDetector()

    test_cases = [
        "联系电话：13812345678",
        "手机号码13912345678可以联系",
        "电话: 138-1234-5678",
        "多个号码：13812345678，15912345678",
        "无效号码：12345678901",
        "座机：010-12345678",
        ""
    ]

    print("=== 手机号检测测试 ===")
    for text in test_cases:
        print(f"\n文本: {text}")
        print(f"包含手机号: {detector.contains_phone(text)}")
        print(f"找到的手机号: {detector.find_phones(text)}")
        print(f"位置信息: {detector.find_phone_positions(text)}")
