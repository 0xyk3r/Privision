"""
API 客户端测试脚本
演示如何使用视频手机号脱敏 API
"""
import requests
import time
import sys
from pathlib import Path

API_BASE = "http://localhost:8000"


def test_api_workflow(video_path: str):
    """
    测试完整的API工作流

    Args:
        video_path: 要处理的视频文件路径
    """
    print("=" * 60)
    print("视频手机号脱敏 API 测试")
    print("=" * 60)

    # 检查文件是否存在
    if not Path(video_path).exists():
        print(f"错误: 文件不存在 - {video_path}")
        return

    # 1. 上传视频并创建任务
    print("\n[1/4] 上传视频并创建任务...")
    try:
        with open(video_path, "rb") as f:
            files = {"file": (Path(video_path).name, f, "video/mp4")}
            data = {
                "blur_method": "gaussian",
                "blur_strength": 51,
                "use_gpu": False,
                "sample_interval": 1.0
            }
            response = requests.post(f"{API_BASE}/api/tasks", files=files, data=data)
            response.raise_for_status()
            result = response.json()
            task_id = result["task_id"]
            print(f"✓ 任务创建成功")
            print(f"  任务ID: {task_id}")
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到API服务器")
        print("  请确保API服务器正在运行: cd src && python api_server.py")
        return
    except Exception as e:
        print(f"✗ 上传失败: {e}")
        return

    # 2. 轮询查询进度
    print("\n[2/4] 查询处理进度...")
    last_progress = -1
    while True:
        try:
            response = requests.get(f"{API_BASE}/api/tasks/{task_id}")
            response.raise_for_status()
            status = response.json()

            # 只在进度变化时打印
            if status['progress'] != last_progress:
                print(f"  状态: {status['status']:12} | 进度: {status['progress']:6.1f}% | {status['message']}")
                last_progress = status['progress']

            if status['status'] == 'completed':
                print("✓ 处理完成！")
                print(f"\n处理结果统计:")
                if status.get('result'):
                    result = status['result']
                    print(f"  总帧数: {result.get('total_frames', 0)}")
                    print(f"  OCR调用次数: {result.get('ocr_calls', 0)}")
                    print(f"  包含手机号的帧数: {result.get('frames_with_phones', 0)}")
                    print(f"  检测到的手机号: {len(result.get('unique_phones', []))} 个")
                    if result.get('unique_phones'):
                        print(f"  手机号列表: {', '.join(result['unique_phones'])}")
                break
            elif status['status'] == 'failed':
                print(f"✗ 处理失败: {status.get('error', '未知错误')}")
                return

            time.sleep(2)  # 每2秒查询一次

        except KeyboardInterrupt:
            print("\n\n中断查询")
            return
        except Exception as e:
            print(f"✗ 查询失败: {e}")
            return

    # 3. 下载处理后的视频
    print("\n[3/4] 下载处理后的视频...")
    try:
        response = requests.get(f"{API_BASE}/api/tasks/{task_id}/download")
        response.raise_for_status()

        # 保存文件
        output_filename = f"output_masked_{Path(video_path).name}"
        with open(output_filename, "wb") as f:
            f.write(response.content)

        file_size_mb = len(response.content) / (1024 * 1024)
        print(f"✓ 视频下载完成")
        print(f"  保存路径: {output_filename}")
        print(f"  文件大小: {file_size_mb:.2f} MB")
    except Exception as e:
        print(f"✗ 下载失败: {e}")
        return

    # 4. 可选：删除任务
    print("\n[4/4] 清理任务...")
    try:
        delete_choice = input("是否删除服务器上的任务记录和文件？(y/n): ")
        if delete_choice.lower() in ['y', 'yes']:
            response = requests.delete(f"{API_BASE}/api/tasks/{task_id}")
            response.raise_for_status()
            print("✓ 任务已删除")
        else:
            print("  跳过删除（任务将在48小时后自动删除）")
    except Exception as e:
        print(f"✗ 删除失败: {e}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


def list_all_tasks():
    """列出所有任务"""
    print("\n查询所有任务...")
    try:
        response = requests.get(f"{API_BASE}/api/tasks")
        response.raise_for_status()
        result = response.json()

        print(f"\n总任务数: {result['total']}")
        if result['tasks']:
            print("\n任务列表:")
            for task in result['tasks']:
                print(f"  - {task['task_id'][:8]}... | {task['status']:12} | 进度: {task['progress']:6.1f}%")
        else:
            print("  (暂无任务)")
    except Exception as e:
        print(f"查询失败: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python test_api_client.py <视频文件路径>    # 测试处理视频")
        print("  python test_api_client.py --list          # 列出所有任务")
        print("\n示例:")
        print("  python test_api_client.py test.mp4")
        sys.exit(1)

    if sys.argv[1] == "--list":
        list_all_tasks()
    else:
        video_path = sys.argv[1]
        test_api_workflow(video_path)
