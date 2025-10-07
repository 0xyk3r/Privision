"""
检测器工厂模块
用于统一管理和创建各种检测器实例
"""
from typing import Dict, Type, Optional, List, Any
from .detector_base import BaseDetector
from .detectors import PhoneDetector, KeywordDetector, IDCardDetector


class DetectorFactory:
    """
    检测器工厂
    负责注册、创建和管理检测器实例
    """

    # 注册的检测器类型
    _detectors: Dict[str, Type[BaseDetector]] = {
        'phone': PhoneDetector,
        'keyword': KeywordDetector,
        'idcard': IDCardDetector,
    }

    @classmethod
    def register_detector(cls, name: str, detector_class: Type[BaseDetector]):
        """
        注册新的检测器类型

        Args:
            name: 检测器名称
            detector_class: 检测器类
        """
        if not issubclass(detector_class, BaseDetector):
            raise TypeError(f"检测器类必须继承自 BaseDetector")

        cls._detectors[name] = detector_class

    @classmethod
    def create_detector(
        cls,
        detector_type: str,
        **kwargs: Any
    ) -> BaseDetector:
        """
        创建检测器实例

        Args:
            detector_type: 检测器类型名称 ('phone', 'keyword', 'idcard')
            **kwargs: 传递给检测器构造函数的参数

        Returns:
            检测器实例

        Raises:
            ValueError: 如果检测器类型不存在

        Examples:
            # 创建手机号检测器
            phone_detector = DetectorFactory.create_detector('phone')

            # 创建关键字检测器（自定义关键字）
            keyword_detector = DetectorFactory.create_detector(
                'keyword',
                keywords=['姓名', '电话', '地址'],
                case_sensitive=False
            )

            # 创建身份证号检测器
            idcard_detector = DetectorFactory.create_detector('idcard')
        """
        if detector_type not in cls._detectors:
            available = ', '.join(cls._detectors.keys())
            raise ValueError(
                f"未知的检测器类型: '{detector_type}'. "
                f"可用的类型: {available}"
            )

        detector_class = cls._detectors[detector_type]
        return detector_class(**kwargs)

    @classmethod
    def get_available_detectors(cls) -> List[str]:
        """
        获取所有可用的检测器类型

        Returns:
            检测器类型名称列表
        """
        return list(cls._detectors.keys())

    @classmethod
    def get_detector_info(cls, detector_type: str) -> Dict[str, str]:
        """
        获取检测器的详细信息

        Args:
            detector_type: 检测器类型名称

        Returns:
            包含检测器信息的字典

        Raises:
            ValueError: 如果检测器类型不存在
        """
        if detector_type not in cls._detectors:
            raise ValueError(f"未知的检测器类型: '{detector_type}'")

        detector_class = cls._detectors[detector_type]
        # 创建临时实例以获取信息
        temp_instance = detector_class() if detector_type != 'keyword' else detector_class(keywords=[])

        return {
            'name': temp_instance.name,
            'description': temp_instance.description,
            'class_name': detector_class.__name__
        }

    @classmethod
    def list_all_detectors(cls) -> Dict[str, Dict[str, str]]:
        """
        列出所有注册的检测器及其信息

        Returns:
            字典，键为检测器类型，值为检测器信息
        """
        result = {}
        for detector_type in cls._detectors.keys():
            result[detector_type] = cls.get_detector_info(detector_type)
        return result


# 兼容旧代码：提供便捷的获取函数
def get_detector(detector_type: str = 'phone', **kwargs) -> BaseDetector:
    """
    便捷函数：获取检测器实例

    Args:
        detector_type: 检测器类型，默认为 'phone'
        **kwargs: 传递给检测器的参数

    Returns:
        检测器实例
    """
    return DetectorFactory.create_detector(detector_type, **kwargs)


if __name__ == '__main__':
    print("=== 检测器工厂测试 ===\n")

    # 列出所有可用的检测器
    print("可用的检测器:")
    available = DetectorFactory.get_available_detectors()
    print(f"  {', '.join(available)}\n")

    # 获取所有检测器的详细信息
    print("检测器详细信息:")
    all_info = DetectorFactory.list_all_detectors()
    for detector_type, info in all_info.items():
        print(f"  [{detector_type}]")
        print(f"    名称: {info['name']}")
        print(f"    描述: {info['description']}")
        print(f"    类名: {info['class_name']}")
        print()

    # 测试创建不同的检测器
    print("=== 创建和测试检测器 ===\n")

    # 1. 手机号检测器
    print("1. 手机号检测器:")
    phone_detector = DetectorFactory.create_detector('phone')
    test_text = "联系电话：13812345678"
    print(f"   文本: {test_text}")
    print(f"   结果: {phone_detector.find_patterns(test_text)}\n")

    # 2. 关键字检测器
    print("2. 关键字检测器:")
    keyword_detector = DetectorFactory.create_detector(
        'keyword',
        keywords=['姓名', '电话'],
        case_sensitive=False
    )
    test_text = "姓名：张三，电话：12345678"
    print(f"   文本: {test_text}")
    print(f"   结果: {keyword_detector.find_patterns(test_text)}\n")

    # 3. 身份证号检测器
    print("3. 身份证号检测器:")
    idcard_detector = DetectorFactory.create_detector('idcard')
    test_text = "身份证号：110101199001011234"
    print(f"   文本: {test_text}")
    print(f"   结果: {idcard_detector.find_patterns(test_text)}\n")

    # 测试错误处理
    print("=== 错误处理测试 ===")
    try:
        DetectorFactory.create_detector('unknown_type')
    except ValueError as e:
        print(f"✓ 正确捕获错误: {e}")
