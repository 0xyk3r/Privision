"""
检测器基类模块
定义所有检测器的通用接口
"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional


class BaseDetector(ABC):
    """
    检测器抽象基类
    所有具体的检测器都应该继承这个类并实现其抽象方法
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        检测器名称（用于标识）

        Returns:
            检测器的唯一标识名称
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        检测器描述

        Returns:
            检测器功能的简短描述
        """
        pass

    @abstractmethod
    def contains_pattern(self, text: str, strict: bool = True) -> bool:
        """
        检查文本中是否包含目标模式

        Args:
            text: 待检测的文本
            strict: 是否使用严格模式

        Returns:
            是否包含目标模式
        """
        pass

    @abstractmethod
    def find_patterns(self, text: str) -> List[str]:
        """
        查找文本中的所有匹配模式

        Args:
            text: 待检测的文本

        Returns:
            匹配到的模式列表
        """
        pass

    @abstractmethod
    def find_pattern_positions(self, text: str) -> List[Tuple[str, int, int]]:
        """
        查找文本中所有匹配模式及其位置

        Args:
            text: 待检测的文本

        Returns:
            (匹配文本, 起始位置, 结束位置) 的列表
        """
        pass

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<{self.__class__.__name__}: {self.name}>"
