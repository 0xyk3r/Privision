"""
任务队列管理系统
用于异步处理视频任务
"""
import uuid
import threading
import queue
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"  # 等待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


@dataclass
class Task:
    """任务数据类"""
    task_id: str
    input_path: str
    output_path: str
    status: TaskStatus
    progress: float  # 0-100
    message: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    result: Optional[Dict] = None

    # 处理配置
    blur_method: str = 'gaussian'
    blur_strength: int = 51
    use_gpu: bool = False
    sample_interval: float = 1.0
    buffer_time: Optional[float] = None

    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        data['status'] = self.status.value
        return data


class TaskQueue:
    """任务队列管理器"""

    def __init__(self, max_workers: int = 1, storage_dir: str = "./tasks", auto_delete_hours: int = 48):
        """
        初始化任务队列

        Args:
            max_workers: 最大并发处理任务数
            storage_dir: 任务数据存储目录
            auto_delete_hours: 自动删除完成任务的小时数（默认48小时）
        """
        self.max_workers = max_workers
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.auto_delete_hours = auto_delete_hours

        # 任务队列和存储
        self.task_queue = queue.Queue()
        self.tasks: Dict[str, Task] = {}
        self.tasks_lock = threading.Lock()

        # 工作线程
        self.workers = []
        self.running = True

        # 加载已存在的任务
        self._load_tasks()

        # 启动工作线程
        self._start_workers()

        # 启动自动清理线程
        self._start_cleanup_worker()

    def _load_tasks(self):
        """从磁盘加载任务"""
        task_file = self.storage_dir / "tasks.json"
        if task_file.exists():
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    tasks_data = json.load(f)
                    for task_data in tasks_data:
                        task = Task(**task_data)
                        # 将状态字符串转换为枚举
                        if isinstance(task.status, str):
                            task.status = TaskStatus(task.status)
                        self.tasks[task.task_id] = task

                        # 重新加入处理中的任务到队列
                        if task.status == TaskStatus.PENDING:
                            self.task_queue.put(task.task_id)

                print(f"从磁盘加载了 {len(self.tasks)} 个任务")
            except Exception as e:
                print(f"加载任务失败: {e}")

    def _save_tasks(self):
        """保存任务到磁盘"""
        task_file = self.storage_dir / "tasks.json"
        try:
            with self.tasks_lock:
                tasks_data = [task.to_dict() for task in self.tasks.values()]
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存任务失败: {e}")

    def _start_workers(self):
        """启动工作线程"""
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker, daemon=True, name=f"Worker-{i}")
            worker.start()
            self.workers.append(worker)
        print(f"启动了 {self.max_workers} 个工作线程")

    def _start_cleanup_worker(self):
        """启动自动清理线程"""
        cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True, name="CleanupWorker")
        cleanup_thread.start()
        print(f"启动自动清理线程，将每小时清理一次超过 {self.auto_delete_hours} 小时的已完成任务")

    def _cleanup_worker(self):
        """自动清理过期任务的工作线程"""
        while self.running:
            try:
                # 每小时检查一次
                time.sleep(3600)

                if not self.running:
                    break

                self._cleanup_expired_tasks()

            except Exception as e:
                print(f"清理过期任务时出错: {e}")

    def _cleanup_expired_tasks(self):
        """清理过期的已完成任务"""
        now = datetime.now()
        expired_tasks = []

        with self.tasks_lock:
            for task_id, task in list(self.tasks.items()):
                # 只清理已完成或失败的任务
                if task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    continue

                # 检查完成时间
                if not task.completed_at:
                    continue

                try:
                    completed_time = datetime.fromisoformat(task.completed_at)
                    age = now - completed_time

                    # 如果超过指定小时数，标记为过期
                    if age > timedelta(hours=self.auto_delete_hours):
                        expired_tasks.append(task_id)
                except Exception as e:
                    print(f"解析任务 {task_id} 完成时间失败: {e}")

        # 删除过期任务
        deleted_count = 0
        for task_id in expired_tasks:
            if self.delete_task(task_id):
                deleted_count += 1
                print(f"自动删除过期任务: {task_id}")

        if deleted_count > 0:
            print(f"自动清理完成，共删除 {deleted_count} 个过期任务")

    def _worker(self):
        """工作线程处理函数"""
        while self.running:
            try:
                # 从队列获取任务 (超时1秒，避免阻塞shutdown)
                task_id = self.task_queue.get(timeout=1.0)

                with self.tasks_lock:
                    if task_id not in self.tasks:
                        continue
                    task = self.tasks[task_id]

                # 处理任务
                self._process_task(task)

                self.task_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"工作线程错误: {e}")

    def _process_task(self, task: Task):
        """
        处理单个任务

        Args:
            task: 任务对象
        """
        try:
            # 更新任务状态
            with self.tasks_lock:
                task.status = TaskStatus.PROCESSING
                task.started_at = datetime.now().isoformat()
                task.message = "开始处理视频"
                task.progress = 0
            self._save_tasks()

            # 导入处理器
            from video_processor_smart import SmartVideoProcessor

            # 创建进度回调
            def progress_callback(progress: float, message: str):
                with self.tasks_lock:
                    task.progress = progress
                    task.message = message
                self._save_tasks()

            # 创建处理器
            processor = SmartVideoProcessor(
                use_gpu=task.use_gpu,
                blur_method=task.blur_method,
                blur_strength=task.blur_strength,
                sample_interval=task.sample_interval,
                buffer_time=task.buffer_time,
                visualize=False  # API模式不支持可视化
            )

            # 处理视频（使用进度回调）
            stats = processor.process_video(
                input_path=task.input_path,
                output_path=task.output_path,
                progress_callback=progress_callback
            )

            # 任务完成
            with self.tasks_lock:
                task.status = TaskStatus.COMPLETED
                task.progress = 100
                task.message = "处理完成"
                task.completed_at = datetime.now().isoformat()
                task.result = stats
            self._save_tasks()

        except Exception as e:
            # 任务失败
            with self.tasks_lock:
                task.status = TaskStatus.FAILED
                task.message = "处理失败"
                task.completed_at = datetime.now().isoformat()
                task.error = str(e)
            self._save_tasks()
            print(f"任务 {task.task_id} 失败: {e}")

    def create_task(
        self,
        input_path: str,
        output_path: str,
        blur_method: str = 'gaussian',
        blur_strength: int = 51,
        use_gpu: bool = False,
        sample_interval: float = 1.0,
        buffer_time: Optional[float] = None
    ) -> str:
        """
        创建新任务

        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            blur_method: 打码方式
            blur_strength: 模糊强度
            use_gpu: 是否使用GPU
            sample_interval: 采样间隔
            buffer_time: 缓冲时间

        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())

        task = Task(
            task_id=task_id,
            input_path=input_path,
            output_path=output_path,
            status=TaskStatus.PENDING,
            progress=0,
            message="任务已创建，等待处理",
            created_at=datetime.now().isoformat(),
            blur_method=blur_method,
            blur_strength=blur_strength,
            use_gpu=use_gpu,
            sample_interval=sample_interval,
            buffer_time=buffer_time
        )

        with self.tasks_lock:
            self.tasks[task_id] = task

        # 添加到队列
        self.task_queue.put(task_id)

        # 保存到磁盘
        self._save_tasks()

        print(f"创建任务: {task_id}")
        return task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务信息

        Args:
            task_id: 任务ID

        Returns:
            任务对象，如果不存在则返回None
        """
        with self.tasks_lock:
            return self.tasks.get(task_id)

    def get_all_tasks(self) -> Dict[str, Task]:
        """获取所有任务"""
        with self.tasks_lock:
            return self.tasks.copy()

    def delete_task(self, task_id: str) -> bool:
        """
        删除任务及其关联的所有文件

        Args:
            task_id: 任务ID

        Returns:
            是否成功删除
        """
        with self.tasks_lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]

                # 只能删除已完成或失败的任务
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    # 删除输入文件
                    if task.input_path and Path(task.input_path).exists():
                        try:
                            Path(task.input_path).unlink()
                            print(f"已删除输入文件: {task.input_path}")
                        except Exception as e:
                            print(f"删除输入文件失败: {e}")

                    # 删除输出文件
                    if task.output_path and Path(task.output_path).exists():
                        try:
                            Path(task.output_path).unlink()
                            print(f"已删除输出文件: {task.output_path}")
                        except Exception as e:
                            print(f"删除输出文件失败: {e}")

                    # 删除任务记录
                    del self.tasks[task_id]
                    self._save_tasks()
                    return True

        return False

    def shutdown(self):
        """关闭任务队列"""
        print("正在关闭任务队列...")
        self.running = False

        # 等待所有工作线程结束
        for worker in self.workers:
            worker.join(timeout=5.0)

        # 保存任务状态
        self._save_tasks()
        print("任务队列已关闭")


# 全局任务队列实例
_task_queue: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    """获取全局任务队列实例"""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue(max_workers=5)
    return _task_queue
