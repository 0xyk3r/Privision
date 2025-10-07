"""统一的参数配置管理"""
from dataclasses import dataclass, field
from typing import Optional, Literal, Dict, Any


@dataclass
class ProcessConfig:
    """视频处理配置"""
    # 输入输出
    input_path: str
    output_path: str

    # 处理模式
    mode: Literal['frame-by-frame', 'smart'] = 'frame-by-frame'

    # 检测器设置
    detector_type: str = 'phone'  # phone, keyword, idcard
    detector_kwargs: Dict[str, Any] = field(default_factory=dict)  # 传递给检测器的额外参数

    # 打码设置
    blur_method: Literal['gaussian', 'pixelate', 'black'] = 'gaussian'
    blur_strength: int = 51

    # 设备设置
    device: str = 'cpu'  # cpu, gpu:0, gpu:1, etc.

    # 智能采样设置（仅smart模式）
    sample_interval: float = 1.0
    buffer_time: Optional[float] = None

    # 精确定位设置
    precise_location: bool = False
    precise_max_iterations: int = 3

    # UI设置
    enable_rich: bool = True
    enable_visualize: bool = False

    def __post_init__(self):
        """参数验证"""
        # 确保blur_strength为奇数
        if self.blur_strength % 2 == 0:
            self.blur_strength += 1

        # 验证device格式
        if not (self.device == 'cpu' or self.device.startswith('gpu:')):
            raise ValueError(f"Invalid device format: {self.device}. Use 'cpu' or 'gpu:0', 'gpu:1', etc.")

        # 验证模式
        if self.mode not in ['frame-by-frame', 'smart']:
            raise ValueError(f"Invalid mode: {self.mode}")

    @property
    def device_type(self) -> Literal['cpu', 'gpu']:
        """获取设备类型"""
        return 'gpu' if self.device.startswith('gpu:') else 'cpu'

    @property
    def gpu_id(self) -> int:
        """获取GPU ID（仅当使用GPU时有效）"""
        if self.device.startswith('gpu:'):
            return int(self.device.split(':')[1])
        return 0


def parse_args():
    """解析命令行参数"""
    import argparse
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description='视频敏感信息脱敏工具 - 自动识别并打码视频中的敏感信息',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本使用（逐帧模式，检测手机号）
  python main.py input.mp4 output.mp4

  # 检测身份证号
  python main.py input.mp4 output.mp4 --detector idcard

  # 检测关键字
  python main.py input.mp4 output.mp4 --detector keyword --keywords 密码 账号 用户名

  # 智能采样模式（更快）
  python main.py input.mp4 output.mp4 --mode smart

  # 使用GPU加速
  python main.py input.mp4 output.mp4 --device gpu:0

  # 禁用Rich UI
  python main.py input.mp4 output.mp4 --no-rich

  # 启用可视化窗口
  python main.py input.mp4 output.mp4 --visualize

  # 精确定位模式
  python main.py input.mp4 output.mp4 --precise-phone-location
        """
    )

    # 位置参数
    parser.add_argument('input', type=str, help='输入视频文件路径')
    parser.add_argument('output', type=str, help='输出视频文件路径')

    # 检测器设置
    parser.add_argument(
        '--detector',
        type=str,
        choices=['phone', 'keyword', 'idcard'],
        default='phone',
        help='检测器类型: phone(手机号), keyword(关键字), idcard(身份证号) [默认: phone]'
    )

    parser.add_argument(
        '--keywords',
        type=str,
        nargs='+',
        help='关键字列表（仅在 --detector keyword 时有效），例如: --keywords 密码 账号 用户名'
    )

    parser.add_argument(
        '--case-sensitive',
        action='store_true',
        help='关键字检测是否区分大小写（仅在 --detector keyword 时有效）'
    )

    # 处理模式
    parser.add_argument(
        '--mode',
        type=str,
        choices=['frame-by-frame', 'smart'],
        default='frame-by-frame',
        help='处理模式: frame-by-frame(逐帧), smart(智能采样) [默认: frame-by-frame]'
    )

    # 打码设置
    parser.add_argument(
        '--blur-method',
        type=str,
        choices=['gaussian', 'pixelate', 'black'],
        default='gaussian',
        help='打码方式: gaussian(高斯模糊), pixelate(像素化), black(黑色遮挡) [默认: gaussian]'
    )

    parser.add_argument(
        '--blur-strength',
        type=int,
        default=51,
        help='模糊强度（高斯模糊的核大小，必须为奇数）[默认: 51]'
    )

    # 设备设置
    parser.add_argument(
        '--device',
        type=str,
        default='cpu',
        help='计算设备: cpu, gpu:0, gpu:1, etc. [默认: cpu]'
    )

    # 智能采样设置
    parser.add_argument(
        '--sample-interval',
        type=float,
        default=1.0,
        help='采样间隔（秒），仅smart模式有效 [默认: 1.0]'
    )

    parser.add_argument(
        '--buffer-time',
        type=float,
        default=None,
        help='缓冲时间（秒），仅smart模式有效，默认等于采样间隔'
    )

    # 精确定位设置
    parser.add_argument(
        '--precise-location',
        action='store_true',
        help='启用精确定位（通过迭代验证精确定位目标，避免打码其他文字，会增加处理时间）'
    )

    parser.add_argument(
        '--precise-max-iterations',
        type=int,
        default=3,
        help='精确定位的最大迭代次数 [默认: 3]'
    )

    # UI设置
    parser.add_argument(
        '--no-rich',
        action='store_true',
        help='禁用Rich终端UI'
    )

    parser.add_argument(
        '--visualize',
        action='store_true',
        help='启用可视化窗口，实时显示检测结果'
    )

    args = parser.parse_args()

    # 检查输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误: 输入文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)

    if not input_path.is_file():
        print(f"错误: 输入路径不是文件: {args.input}", file=sys.stderr)
        sys.exit(1)

    # 检查输出路径
    output_path = Path(args.output)
    if output_path.exists():
        response = input(f"警告: 输出文件已存在: {args.output}\n是否覆盖? (y/n): ")
        if response.lower() not in ['y', 'yes']:
            print("操作已取消")
            sys.exit(0)

    # 准备检测器参数
    detector_kwargs = {}
    if args.detector == 'keyword':
        if args.keywords:
            detector_kwargs['keywords'] = args.keywords
        detector_kwargs['case_sensitive'] = args.case_sensitive

    # 创建配置对象
    config = ProcessConfig(
        input_path=str(input_path),
        output_path=str(output_path),
        detector_type=args.detector,
        detector_kwargs=detector_kwargs,
        mode=args.mode,
        blur_method=args.blur_method,
        blur_strength=args.blur_strength,
        device=args.device,
        sample_interval=args.sample_interval,
        buffer_time=args.buffer_time,
        precise_location=args.precise_location,
        precise_max_iterations=args.precise_max_iterations,
        enable_rich=not args.no_rich,
        enable_visualize=args.visualize
    )

    return config
