#!/usr/bin/env python3
"""
批量处理示例脚本
演示如何批量处理多个视频文件
"""
import os
import sys
from pathlib import Path
from video_processor import VideoProcessor


def process_videos_in_directory(
    input_dir: str,
    output_dir: str,
    blur_method: str = 'gaussian',
    use_gpu: bool = False
):
    """
    批量处理目录中的所有视频文件

    Args:
        input_dir: 输入视频目录
        output_dir: 输出视频目录
        blur_method: 打码方式
        use_gpu: 是否使用GPU
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # 检查输入目录
    if not input_path.exists():
        print(f"错误: 输入目录不存在: {input_dir}")
        return

    # 创建输出目录
    output_path.mkdir(parents=True, exist_ok=True)

    # 支持的视频格式
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}

    # 查找所有视频文件
    video_files = [
        f for f in input_path.iterdir()
        if f.is_file() and f.suffix.lower() in video_extensions
    ]

    if not video_files:
        print(f"在目录 {input_dir} 中未找到视频文件")
        return

    print(f"找到 {len(video_files)} 个视频文件")
    print("=" * 60)

    # 创建视频处理器
    processor = VideoProcessor(use_gpu=use_gpu, blur_method=blur_method)

    # 处理每个视频
    for i, video_file in enumerate(video_files, 1):
        print(f"\n[{i}/{len(video_files)}] 处理: {video_file.name}")

        # 生成输出文件名
        output_file = output_path / f"{video_file.stem}_masked{video_file.suffix}"

        try:
            # 处理视频
            stats = processor.process_video(
                input_path=str(video_file),
                output_path=str(output_file)
            )

            print(f"✓ 完成: {output_file.name}")
            print(f"  检测到手机号: {stats['total_phones_detected']} 个")

        except Exception as e:
            print(f"✗ 处理失败: {e}")
            continue

    print("\n" + "=" * 60)
    print("批量处理完成！")


if __name__ == '__main__':
    # 示例用法
    if len(sys.argv) < 3:
        print("用法: python example_batch.py <输入目录> <输出目录> [--use-gpu]")
        print("\n示例:")
        print("  python example_batch.py videos/ output/")
        print("  python example_batch.py videos/ output/ --use-gpu")
        sys.exit(1)

    input_directory = sys.argv[1]
    output_directory = sys.argv[2]
    use_gpu_flag = '--use-gpu' in sys.argv

    process_videos_in_directory(
        input_dir=input_directory,
        output_dir=output_directory,
        blur_method='gaussian',
        use_gpu=use_gpu_flag
    )
