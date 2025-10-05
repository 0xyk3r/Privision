#!/usr/bin/env python3
"""
视频手机号脱敏工具 - 智能采样
使用时间段采样策略大幅提升处理速度
"""
import argparse
import sys
from pathlib import Path
from video_processor_smart import SmartVideoProcessor
from terminal_ui import VideoProcessorUI


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(
        description='视频手机号脱敏工具（智能采样） - 大幅提升处理速度',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
工作原理:
  1. 每隔 sample-interval 秒进行一次 OCR 识别
  2. 识别到手机号后，记录其位置
  3. 在识别点前后各 buffer-time 秒应用打码（防止间隙泄露）
  4. 逐帧处理时只需应用打码，无需重复 OCR

优势:
  - 速度提升 10-30 倍（取决于采样间隔）
  - 适合静态或慢速移动的手机号
  - 缓冲时间防止敏感信息泄露

示例:
  # 基本使用（1秒采样，自动缓冲1秒）
  python main_smart.py input.mp4 output.mp4

  # 更快速度（2秒采样，自动缓冲2秒）
  python main_smart.py input.mp4 output.mp4 --sample-interval 2.0

  # 手动指定缓冲时间（覆盖自动值）
  python main_smart.py input.mp4 output.mp4 --buffer-time 0.3

  # 快速移动场景（0.5秒采样，自动缓冲0.5秒）
  python main_smart.py input.mp4 output.mp4 --sample-interval 0.5

  # 使用 GPU 加速
  python main_smart.py input.mp4 output.mp4 --use-gpu

注意事项:
  - 适合静态显示的手机号（如截图、文档）
  - 不适合快速移动或频繁变化的场景
  - 如果手机号移动速度快，降低 sample-interval
        """
    )

    parser.add_argument(
        'input',
        type=str,
        help='输入视频文件路径'
    )

    parser.add_argument(
        'output',
        type=str,
        help='输出视频文件路径'
    )

    parser.add_argument(
        '--sample-interval',
        type=float,
        default=1.0,
        help='采样间隔（秒），每隔多久识别一次 [默认: 1.0，推荐范围: 0.5-2.0]'
    )

    parser.add_argument(
        '--buffer-time',
        type=float,
        default=None,
        help='缓冲时间（秒），在识别点前后各扩展的时间。'
             '默认: sample-interval（自动覆盖间隙），可手动指定以覆盖默认值'
    )

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

    parser.add_argument(
        '--use-gpu',
        action='store_true',
        help='使用GPU加速OCR识别'
    )

    args = parser.parse_args()

    # 检查输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误: 输入文件不存在: {args.input}", file=sys.stderr)
        return 1

    if not input_path.is_file():
        print(f"错误: 输入路径不是文件: {args.input}", file=sys.stderr)
        return 1

    # 检查输出路径
    output_path = Path(args.output)
    if output_path.exists():
        response = input(f"警告: 输出文件已存在: {args.output}\n是否覆盖? (y/n): ")
        if response.lower() not in ['y', 'yes']:
            print("操作已取消")
            return 0

    # 参数验证
    if args.sample_interval <= 0:
        print(f"错误: 采样间隔必须大于 0", file=sys.stderr)
        return 1

    if args.buffer_time is not None and args.buffer_time < 0:
        print(f"错误: 缓冲时间不能为负数", file=sys.stderr)
        return 1

    # 创建UI并设置配置信息
    ui = VideoProcessorUI()
    ui.set_config({
        'input': args.input,
        'output': args.output,
        'blur_method': args.blur_method,
        'blur_strength': args.blur_strength,
        'use_gpu': args.use_gpu,
        'sample_interval': args.sample_interval,
        'buffer_time': args.buffer_time
    })

    try:
        # 创建智能视频处理器
        processor = SmartVideoProcessor(
            use_gpu=args.use_gpu,
            blur_method=args.blur_method,
            blur_strength=args.blur_strength,
            sample_interval=args.sample_interval,
            buffer_time=args.buffer_time
        )

        # 使用UI处理视频
        stats = ui.process_smart_video_with_ui(
            smart_processor=processor,
            input_path=str(input_path),
            output_path=str(output_path)
        )

        return 0

    except KeyboardInterrupt:
        print("\n\n操作被用户中断", file=sys.stderr)
        return 130

    except Exception as e:
        print(f"\n错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
