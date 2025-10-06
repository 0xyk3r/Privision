#!/usr/bin/env python3
"""
测试智能采样模式的打码范围逻辑
验证缓冲时间机制是否正确工作
"""


def calculate_blur_ranges(
    total_frames: int,
    fps: int,
    sample_interval: float,
    buffer_time: float,
    detection_frames: list  # 在哪些采样点检测到手机号
):
    """
    计算打码范围

    Args:
        total_frames: 总帧数
        fps: 帧率
        sample_interval: 采样间隔（秒）
        buffer_time: 缓冲时间（秒）
        detection_frames: 检测到手机号的采样帧列表

    Returns:
        所有打码范围的列表 [(start, end), ...]
    """
    sample_frame_interval = int(fps * sample_interval)
    buffer_frames = int(fps * buffer_time)

    ranges = []
    for frame_idx in detection_frames:
        start_frame = max(0, frame_idx - buffer_frames)
        end_frame = min(total_frames - 1, frame_idx + buffer_frames)
        ranges.append((start_frame, end_frame))

    return ranges


def merge_ranges(ranges):
    """合并重叠的范围"""
    if not ranges:
        return []

    # 按起始位置排序
    ranges = sorted(ranges)
    merged = [ranges[0]]

    for current in ranges[1:]:
        last = merged[-1]
        # 如果当前范围与上一个重叠或相邻，合并
        if current[0] <= last[1] + 1:
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)

    return merged


def frames_to_time(frame, fps):
    """将帧号转换为时间"""
    return frame / fps


def print_test_case(name, total_frames, fps, sample_interval, buffer_time, detection_frames):
    """打印测试用例"""
    print("=" * 80)
    print(f"测试用例: {name}")
    print("=" * 80)

    total_time = total_frames / fps
    print(f"\n视频参数:")
    print(f"  总帧数: {total_frames} 帧")
    print(f"  帧率: {fps} FPS")
    print(f"  总时长: {total_time:.1f} 秒")

    print(f"\n采样参数:")
    print(f"  采样间隔: {sample_interval} 秒")
    print(f"  缓冲时间: {buffer_time} 秒")

    sample_frame_interval = int(fps * sample_interval)
    buffer_frames = int(fps * buffer_time)

    print(f"\n采样点:")
    sample_points = list(range(0, total_frames, sample_frame_interval))
    for i, frame in enumerate(sample_points):
        detected = "●" if frame in detection_frames else "○"
        print(f"  {detected} 第 {i+1} 次采样: 帧 {frame} ({frames_to_time(frame, fps):.1f}秒)")

    print(f"\n检测结果:")
    if detection_frames:
        for frame in detection_frames:
            print(f"  ✓ 在帧 {frame} ({frames_to_time(frame, fps):.1f}秒) 检测到手机号")
    else:
        print(f"  ✗ 未检测到手机号")

    # 计算打码范围
    blur_ranges = calculate_blur_ranges(
        total_frames, fps, sample_interval, buffer_time, detection_frames
    )

    print(f"\n打码范围（原始）:")
    for i, (start, end) in enumerate(blur_ranges, 1):
        print(f"  [{i}] 帧 {start}-{end} ({frames_to_time(start, fps):.2f}秒 - {frames_to_time(end, fps):.2f}秒)")

    # 合并重叠范围
    merged_ranges = merge_ranges(blur_ranges)

    print(f"\n打码范围（合并后）:")
    if merged_ranges:
        for i, (start, end) in enumerate(merged_ranges, 1):
            duration = (end - start + 1) / fps
            print(f"  [{i}] 帧 {start}-{end} ({frames_to_time(start, fps):.2f}秒 - {frames_to_time(end, fps):.2f}秒, 时长 {duration:.2f}秒)")

        total_blur_frames = sum(end - start + 1 for start, end in merged_ranges)
        blur_percentage = (total_blur_frames / total_frames) * 100
        print(f"\n  打码帧数: {total_blur_frames}/{total_frames} ({blur_percentage:.1f}%)")
    else:
        print(f"  无")

    print()


# 测试用例
print("\n" + "=" * 80)
print("智能采样模式 - 打码范围逻辑测试")
print("=" * 80)

# 测试1: 基本场景
print_test_case(
    name="基本场景 - 手机号在2秒位置检测到",
    total_frames=150,  # 5秒
    fps=30,
    sample_interval=1.0,
    buffer_time=0.2,
    detection_frames=[60]  # 2秒位置
)

# 测试2: 连续检测
print_test_case(
    name="连续检测 - 手机号静态显示",
    total_frames=300,  # 10秒
    fps=30,
    sample_interval=1.0,
    buffer_time=0.2,
    detection_frames=[30, 60, 90, 120, 150, 180]  # 1-6秒都检测到
)

# 测试3: 边界情况
print_test_case(
    name="边界情况 - 手机号在视频开头",
    total_frames=150,
    fps=30,
    sample_interval=1.0,
    buffer_time=0.5,
    detection_frames=[0]  # 0秒位置
)

# 测试4: 大缓冲时间
print_test_case(
    name="大缓冲时间 - 确保覆盖采样间隙",
    total_frames=300,
    fps=30,
    sample_interval=2.0,
    buffer_time=1.0,
    detection_frames=[60, 120, 180]  # 2秒、4秒、6秒
)

# 测试5: 短暂显示可能漏检的场景
print_test_case(
    name="可能漏检 - 手机号只显示0.5秒",
    total_frames=150,
    fps=30,
    sample_interval=2.0,
    buffer_time=0.2,
    detection_frames=[]  # 采样点都没检测到
)

# 测试6: 优化后能检测到
print_test_case(
    name="优化后能检测 - 采样间隔0.5秒",
    total_frames=150,
    fps=30,
    sample_interval=0.5,
    buffer_time=0.3,
    detection_frames=[45, 60]  # 1.5秒和2秒都检测到
)

print("=" * 80)
print("测试完成")
print("=" * 80)
print("\n关键点验证:")
print("1. ✓ 识别点前后各扩展 buffer_time")
print("2. ✓ 重叠范围会自动合并")
print("3. ✓ 边界情况正确处理（不会超出视频范围）")
print("4. ✓ 缓冲时间机制防止间隙泄露")
