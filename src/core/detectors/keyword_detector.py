"""
关键字检测模块
用于识别和定位自定义关键字
"""
import re
from typing import List, Tuple, Optional
from ..detector_base import BaseDetector


class KeywordDetector(BaseDetector):
    """关键字检测器 - 支持自定义关键字列表"""

    def __init__(self, keywords: Optional[List[str]] = None, case_sensitive: bool = False):
        """
        初始化关键字检测器

        Args:
            keywords: 关键字列表，如果为None则使用默认关键字
            case_sensitive: 是否区分大小写
        """
        self.keywords = keywords or ['密码', '账号', '用户名', '身份证', 'password', 'username']
        self.case_sensitive = case_sensitive
        self._compile_patterns()

    def _compile_patterns(self):
        """编译正则表达式模式"""
        flags = 0 if self.case_sensitive else re.IGNORECASE
        # 为每个关键字创建一个模式，使用单词边界
        self.patterns = []
        for keyword in self.keywords:
            # 转义特殊字符
            escaped = re.escape(keyword)
            # 对于中文，不使用\b边界；对于英文，使用\b边界
            if re.search(r'[\u4e00-\u9fff]', keyword):  # 包含中文
                pattern = re.compile(escaped, flags)
            else:  # 纯英文
                pattern = re.compile(r'\b' + escaped + r'\b', flags)
            self.patterns.append((keyword, pattern))

    @property
    def name(self) -> str:
        """检测器名称"""
        return "keyword"

    @property
    def description(self) -> str:
        """检测器描述"""
        return f"关键字检测器 (共{len(self.keywords)}个关键字)"

    def contains_pattern(self, text: str, strict: bool = True) -> bool:
        """
        检查文本中是否包含关键字

        Args:
            text: 待检测的文本
            strict: 是否使用严格模式（此参数对关键字检测无影响）

        Returns:
            是否包含关键字
        """
        if not text:
            return False

        for keyword, pattern in self.patterns:
            if pattern.search(text):
                return True
        return False

    def find_patterns(self, text: str) -> List[str]:
        """
        查找文本中的所有关键字

        Args:
            text: 待检测的文本

        Returns:
            匹配到的关键字列表
        """
        if not text:
            return []

        found_keywords = []
        for keyword, pattern in self.patterns:
            if pattern.search(text):
                # 返回原始关键字（保持大小写）
                matches = pattern.findall(text)
                found_keywords.extend(matches)

        return found_keywords

    def find_pattern_positions(self, text: str) -> List[Tuple[str, int, int]]:
        """
        查找文本中所有关键字及其位置

        Args:
            text: 待检测的文本

        Returns:
            (关键字, 起始位置, 结束位置) 的列表
        """
        if not text:
            return []

        results = []
        for keyword, pattern in self.patterns:
            for match in pattern.finditer(text):
                matched_text = match.group()
                start = match.start()
                end = match.end()
                results.append((matched_text, start, end))

        # 按位置排序
        results.sort(key=lambda x: x[1])
        return results

    def set_keywords(self, keywords: List[str]):
        """
        更新关键字列表

        Args:
            keywords: 新的关键字列表
        """
        self.keywords = keywords
        self._compile_patterns()

    def add_keyword(self, keyword: str):
        """
        添加一个关键字

        Args:
            keyword: 要添加的关键字
        """
        if keyword not in self.keywords:
            self.keywords.append(keyword)
            self._compile_patterns()

    def remove_keyword(self, keyword: str):
        """
        删除一个关键字

        Args:
            keyword: 要删除的关键字
        """
        if keyword in self.keywords:
            self.keywords.remove(keyword)
            self._compile_patterns()


if __name__ == '__main__':
    # 测试用例
    print("=== 关键字检测器测试 ===\n")

    # 测试默认关键字
    detector = KeywordDetector()
    print(f"{detector.description}")
    print(f"检测器名称: {detector.name}")
    print(f"关键字列表: {detector.keywords}\n")

    test_cases = [
        "请输入您的密码",
        "账号：admin",
        "USERNAME: test@example.com",
        "这是一段普通文本",
        "密码和账号都要保密",
    ]

    for text in test_cases:
        print(f"文本: {text}")
        print(f"包含关键字: {detector.contains_pattern(text)}")
        print(f"找到的关键字: {detector.find_patterns(text)}")
        print(f"位置信息: {detector.find_pattern_positions(text)}")
        print()

    # 测试自定义关键字
    print("\n=== 自定义关键字测试 ===")
    custom_detector = KeywordDetector(keywords=['姓名', '电话', '地址'], case_sensitive=False)
    print(f"自定义关键字: {custom_detector.keywords}")

    test_text = "姓名：张三，电话：12345678，地址：北京市"
    print(f"\n文本: {test_text}")
    print(f"找到的关键字: {custom_detector.find_patterns(test_text)}")
    print(f"位置信息: {custom_detector.find_pattern_positions(test_text)}")
