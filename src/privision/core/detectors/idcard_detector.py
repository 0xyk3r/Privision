"""
身份证号检测模块
用于识别和定位中国大陆18位身份证号
"""
import re
from typing import List, Tuple
from ..detector_base import BaseDetector


class IDCardDetector(BaseDetector):
    """中国大陆身份证号检测器（18位）"""

    # 18位身份证号正则
    # 格式：6位地区码 + 8位出生日期 + 3位顺序码 + 1位校验码
    # 校验码可以是数字0-9或字母X
    IDCARD_PATTERN = re.compile(r'\b\d{17}[\dXx]\b')

    # 严格模式：前后必须是非数字字符
    IDCARD_PATTERN_STRICT = re.compile(r'(?<!\d)\d{17}[\dXx](?!\d)')

    @property
    def name(self) -> str:
        """检测器名称"""
        return "idcard"

    @property
    def description(self) -> str:
        """检测器描述"""
        return "中国大陆身份证号检测器 (18位)"

    def contains_pattern(self, text: str, strict: bool = True) -> bool:
        """
        检查文本中是否包含身份证号

        Args:
            text: 待检测的文本
            strict: 是否使用严格模式

        Returns:
            是否包含身份证号
        """
        if not text:
            return False

        # 移除空格、横线等分隔符后再匹配
        cleaned_text = re.sub(r'[\s\-\u3000]', '', text)

        # 使用严格模式或普通模式
        pattern = self.IDCARD_PATTERN_STRICT if strict else self.IDCARD_PATTERN
        matches = pattern.findall(cleaned_text)

        if not matches:
            return False

        # 验证每个匹配
        for match in matches:
            if self._is_valid_idcard(match):
                return True

        return False

    def _is_valid_idcard(self, idcard: str) -> bool:
        """
        验证身份证号的有效性（基础验证）

        Args:
            idcard: 身份证号

        Returns:
            是否有效
        """
        if len(idcard) != 18:
            return False

        # 验证出生日期部分（第7-14位）
        year = idcard[6:10]
        month = idcard[10:12]
        day = idcard[12:14]

        try:
            year_int = int(year)
            month_int = int(month)
            day_int = int(day)

            # 基础验证
            if year_int < 1900 or year_int > 2100:
                return False
            if month_int < 1 or month_int > 12:
                return False
            if day_int < 1 or day_int > 31:
                return False

            # 可以添加更严格的日期验证和校验码验证
            # 这里为了简化，只做基础验证

            return True

        except ValueError:
            return False

    def find_patterns(self, text: str) -> List[str]:
        """
        查找文本中的所有身份证号

        Args:
            text: 待检测的文本

        Returns:
            身份证号列表
        """
        if not text:
            return []

        # 移除空格、横线等分隔符后再匹配
        cleaned_text = re.sub(r'[\s\-\u3000]', '', text)
        matches = self.IDCARD_PATTERN.findall(cleaned_text)

        # 只返回有效的身份证号
        valid_idcards = []
        for match in matches:
            if self._is_valid_idcard(match):
                valid_idcards.append(match)

        return valid_idcards

    def find_pattern_positions(self, text: str) -> List[Tuple[str, int, int]]:
        """
        查找文本中所有身份证号及其位置

        Args:
            text: 待检测的文本

        Returns:
            (身份证号, 起始位置, 结束位置) 的列表
        """
        if not text:
            return []

        # 移除空格、横线等分隔符后再匹配
        cleaned_text = re.sub(r'[\s\-\u3000]', '', text)

        # 建立清理后位置到原始位置的映射
        cleaned_to_original = []
        original_idx = 0
        for char in text:
            if not re.match(r'[\s\-\u3000]', char):
                cleaned_to_original.append(original_idx)
            original_idx += 1

        results = []
        for match in self.IDCARD_PATTERN.finditer(cleaned_text):
            idcard = match.group()

            # 验证有效性
            if not self._is_valid_idcard(idcard):
                continue

            cleaned_start = match.start()
            cleaned_end = match.end()

            # 映射回原始文本的位置
            if cleaned_start < len(cleaned_to_original) and cleaned_end <= len(cleaned_to_original):
                original_start = cleaned_to_original[cleaned_start]
                if cleaned_end < len(cleaned_to_original):
                    original_end = cleaned_to_original[cleaned_end]
                else:
                    original_end = len(text)

                results.append((idcard, original_start, original_end))

        return results


if __name__ == '__main__':
    # 测试用例
    detector = IDCardDetector()

    test_cases = [
        "身份证号：110101199001011234",
        "证件号码：11010119900101123X",
        "ID: 110101 1990 0101 1234",
        "无效：12345678901234567890",  # 超长数字
        "无效：123456789012345678",     # 18位但日期无效
        ""
    ]

    print(f"=== {detector.description} ===")
    print(f"检测器名称: {detector.name}\n")

    for text in test_cases:
        print(f"文本: {text}")
        print(f"包含身份证号: {detector.contains_pattern(text)}")
        print(f"找到的身份证号: {detector.find_patterns(text)}")
        print(f"位置信息: {detector.find_pattern_positions(text)}")
        print()
