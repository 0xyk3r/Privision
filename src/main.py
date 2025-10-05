#!/usr/bin/env python3
"""
视频手机号脱敏工具 - 主程序
使用PaddleOCR识别视频中的手机号并进行打码处理
"""
import argparse
import sys
from pathlib import Path
from video_processor import VideoProcessor
from terminal_ui import VideoProcessorUI


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(
        description='视频手机号脱敏工具 - 自动识别并打码视频中的中国大陆手机号',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本使用（默认高斯模糊）
  python main.py input.mp4 output.mp4

  # 使用像素化打码
  python main.py input.mp4 output.mp4 --blur-method pixelate

  # 使用黑色遮挡
  python main.py input.mp4 output.mp4 --blur-method black

  # 使用GPU加速
  python main.py input.mp4 output.mp4 --use-gpu

  # 调整模糊强度（仅对高斯模糊有效）
  python main.py input.mp4 output.mp4 --blur-strength 71
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
        help='模糊强度（高斯模糊的核大小，必须为奇数，越大越模糊）[默认: 51]'
    )

    parser.add_argument(
        '--use-gpu',
        action='store_true',
        help='使用GPU加速OCR识别（需要安装paddlepaddle-gpu）'
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

    # 创建UI并设置配置信息
    ui = VideoProcessorUI()
    ui.set_config({
        'input': args.input,
        'output': args.output,
        'blur_method': args.blur_method,
        'blur_strength': args.blur_strength,
        'use_gpu': args.use_gpu
    })

    try:
        # 创建视频处理器
        processor = VideoProcessor(
            use_gpu=args.use_gpu,
            blur_method=args.blur_method,
            blur_strength=args.blur_strength
        )

        # 使用UI处理视频
        stats = ui.process_video_with_ui(
            video_processor=processor,
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
