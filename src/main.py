#!/usr/bin/env python3
"""
视频手机号脱敏工具 - 统一CLI入口
使用PaddleOCR识别视频中的手机号并进行打码处理
"""
import sys

from src.config import parse_args
from src.core import VideoProcessor
from src.ui import RichUI, ConsoleProgress, Visualizer


def main():
    """主程序入口"""
    try:
        # 解析参数
        config = parse_args()

        # 创建进度回调
        if config.enable_visualize:
            # 可视化模式：不使用Rich UI
            progress_callback = None
            print("\n=== 可视化模式已启用 ===")
            print("可视化窗口将在处理开始时打开")
            print("快捷键:")
            print("  Q/ESC - 退出")
            print("  P     - 暂停/继续")
            print("  T     - 切换标签显示 (仅手机号 -> 全部显示 -> 隐藏)")
            print()
        elif config.enable_rich:
            # Rich UI模式
            progress_callback = RichUI(config.__dict__)
            progress_callback.start_ui()
        else:
            # 简单控制台模式
            progress_callback = ConsoleProgress()

        # 创建视频处理器
        processor = VideoProcessor(config, progress_callback=progress_callback)

        # 处理视频
        stats = processor.process_video(config.input_path, config.output_path)

        # 确保UI停止
        if isinstance(progress_callback, RichUI):
            progress_callback.stop_ui()

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
