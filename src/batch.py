#!/usr/bin/env python3
"""
批量视频处理模块
用于批量打码处理多个视频文件中的目标内容
"""
import sys
from pathlib import Path
from typing import Literal, Optional, List, Dict, Any
import argparse
from datetime import datetime

from src.config.args import ProcessConfig
from src.core.video_processor import VideoProcessor


class BatchVideoProcessor:
    """批量视频处理器"""

    # 支持的视频格式
    SUPPORTED_FORMATS = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'}

    def __init__(
        self,
        detector_type: str = 'phone',
        detector_kwargs: Optional[Dict[str, Any]] = None,
        blur_method: Literal['gaussian', 'pixelate', 'black'] = 'gaussian',
        device: str = 'cpu',
        mode: Literal['frame-by-frame', 'smart'] = 'frame-by-frame',
        enable_rich: bool = False,
        enable_visualize: bool = False,
        output_suffix: str = '_masked',
    ):
        """
        初始化批量处理器

        Args:
            detector_type: 检测器类型 ('phone', 'keyword', 'idcard')
            detector_kwargs: 检测器参数（字典）
            blur_method: 打码方式 ('gaussian', 'pixelate', 'black')
            device: 计算设备 ('cpu' 或 'gpu:0', 'gpu:1', ...)
            mode: 处理模式 ('frame-by-frame' 或 'smart')
            enable_rich: 是否启用Rich UI
            enable_visualize: 是否启用可视化
            output_suffix: 输出文件后缀
        """
        self.detector_type = detector_type
        self.detector_kwargs = detector_kwargs or {}
        self.blur_method = blur_method
        self.device = device
        self.mode = mode
        self.enable_rich = enable_rich
        self.enable_visualize = enable_visualize
        self.output_suffix = output_suffix

    def find_video_files(self, input_dir: Path) -> List[Path]:
        """
        查找目录中的所有视频文件

        Args:
            input_dir: 输入目录路径

        Returns:
            视频文件路径列表
        """
        video_files = [
            f for f in input_dir.iterdir()
            if f.is_file() and f.suffix.lower() in self.SUPPORTED_FORMATS
        ]
        return sorted(video_files)

    def process_single_video(
        self,
        video_file: Path,
        output_file: Path,
    ) -> Optional[Dict[str, Any]]:
        """
        处理单个视频文件

        Args:
            video_file: 输入视频文件路径
            output_file: 输出视频文件路径

        Returns:
            处理统计信息，如果失败返回None
        """
        try:
            # 创建配置对象
            config = ProcessConfig(
                input_path=str(video_file),
                output_path=str(output_file),
                detector_type=self.detector_type,
                detector_kwargs=self.detector_kwargs,
                blur_method=self.blur_method,
                device=self.device,
                mode=self.mode,
                enable_rich=self.enable_rich,
                enable_visualize=self.enable_visualize,
            )

            # 创建视频处理器
            processor = VideoProcessor(config, progress_callback=None)

            # 处理视频
            stats = processor.process_video(str(video_file), str(output_file))

            return stats

        except Exception as e:
            print(f"✗ 处理失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def process_directory(
        self,
        input_dir: str,
        output_dir: str,
        recursive: bool = False,
    ) -> Dict[str, Any]:
        """
        批量处理目录中的所有视频文件

        Args:
            input_dir: 输入视频目录
            output_dir: 输出视频目录
            recursive: 是否递归处理子目录

        Returns:
            批量处理统计信息
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        # 检查输入目录
        if not input_path.exists():
            print(f"错误: 输入目录不存在: {input_dir}")
            return {'success': False, 'error': '输入目录不存在'}

        if not input_path.is_dir():
            print(f"错误: 输入路径不是目录: {input_dir}")
            return {'success': False, 'error': '输入路径不是目录'}

        # 创建输出目录
        output_path.mkdir(parents=True, exist_ok=True)

        # 查找所有视频文件
        if recursive:
            video_files = [
                f for f in input_path.rglob('*')
                if f.is_file() and f.suffix.lower() in self.SUPPORTED_FORMATS
            ]
        else:
            video_files = self.find_video_files(input_path)

        if not video_files:
            print(f"在目录 {input_dir} 中未找到视频文件")
            return {'success': True, 'processed': 0, 'failed': 0, 'total': 0}

        print(f"找到 {len(video_files)} 个视频文件")
        print("=" * 60)

        # 统计信息
        total_files = len(video_files)
        processed_files = 0
        failed_files = 0
        total_phones = 0
        start_time = datetime.now()

        # 处理每个视频
        for i, video_file in enumerate(video_files, 1):
            print(f"\n[{i}/{total_files}] 处理: {video_file.name}")

            # 生成输出文件路径
            if recursive:
                # 保持目录结构
                relative_path = video_file.relative_to(input_path)
                output_file = output_path / relative_path.parent / f"{video_file.stem}{self.output_suffix}{video_file.suffix}"
                output_file.parent.mkdir(parents=True, exist_ok=True)
            else:
                output_file = output_path / f"{video_file.stem}{self.output_suffix}{video_file.suffix}"

            # 处理视频
            stats = self.process_single_video(video_file, output_file)

            if stats is not None:
                processed_files += 1
                total_phones += stats.get('total_patterns_detected', 0)
                print(f"✓ 完成: {output_file.name}")
                print(f"  检测到目标内容: {stats.get('total_patterns_detected', 0)} 个")
            else:
                failed_files += 1

        # 计算处理时间
        end_time = datetime.now()
        duration = end_time - start_time

        # 打印汇总信息
        print("\n" + "=" * 60)
        print("批量处理完成！")
        print(f"总文件数: {total_files}")
        print(f"成功处理: {processed_files}")
        print(f"处理失败: {failed_files}")
        print(f"检测到目标内容总数: {total_phones}")
        print(f"总耗时: {duration}")
        print("=" * 60)

        return {
            'success': True,
            'total': total_files,
            'processed': processed_files,
            'failed': failed_files,
            'total_patterns_detected': total_phones,
            'duration': str(duration),
        }


def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        description='批量处理视频文件中的目标内容',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m src.batch input_videos/ output_videos/
  python -m src.batch input_videos/ output_videos/ --device gpu:0
  python -m src.batch input_videos/ output_videos/ --mode smart
  python -m src.batch input_videos/ output_videos/ --blur-method pixelate --recursive
        """
    )

    parser.add_argument('input_dir', help='输入视频目录')
    parser.add_argument('output_dir', help='输出视频目录')
    parser.add_argument(
        '--detector',
        choices=['phone', 'keyword', 'idcard'],
        default='phone',
        help='检测器类型 (默认: phone)'
    )
    parser.add_argument(
        '--keywords',
        nargs='+',
        help='关键字列表（仅在 --detector keyword 时有效）'
    )
    parser.add_argument(
        '--case-sensitive',
        action='store_true',
        help='关键字检测是否区分大小写'
    )
    parser.add_argument(
        '--blur-method',
        choices=['gaussian', 'pixelate', 'black'],
        default='gaussian',
        help='打码方式 (默认: gaussian)'
    )
    parser.add_argument(
        '--device',
        default='cpu',
        help='计算设备 (cpu 或 gpu:0, gpu:1, ...) (默认: cpu)'
    )
    parser.add_argument(
        '--mode',
        choices=['frame-by-frame', 'smart'],
        default='frame-by-frame',
        help='处理模式 (默认: frame-by-frame)'
    )
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='递归处理子目录'
    )
    parser.add_argument(
        '--enable-rich',
        action='store_true',
        help='启用Rich UI界面'
    )
    parser.add_argument(
        '--enable-visualize',
        action='store_true',
        help='启用可视化'
    )
    parser.add_argument(
        '--output-suffix',
        default='_masked',
        help='输出文件后缀 (默认: _masked)'
    )

    args = parser.parse_args()

    # 准备检测器参数
    detector_kwargs = {}
    if args.detector == 'keyword':
        if args.keywords:
            detector_kwargs['keywords'] = args.keywords
        detector_kwargs['case_sensitive'] = args.case_sensitive

    # 创建批量处理器
    processor = BatchVideoProcessor(
        detector_type=args.detector,
        detector_kwargs=detector_kwargs,
        blur_method=args.blur_method,
        device=args.device,
        mode=args.mode,
        enable_rich=args.enable_rich,
        enable_visualize=args.enable_visualize,
        output_suffix=args.output_suffix,
    )

    # 执行批量处理
    result = processor.process_directory(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        recursive=args.recursive,
    )

    # 返回退出码
    if result.get('success') and result.get('failed', 0) == 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()

