"""
FastAPI 服务器 - 视频内容脱敏 API
提供上传视频、查询进度、下载结果的REST API接口
"""
import shutil
import argparse
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from privision.api.task_queue import get_task_queue, TaskStatus


# ====== 全局配置 ======
# 数据目录配置（将在启动时初始化）
DATA_DIR: Optional[Path] = None
UPLOAD_DIR: Optional[Path] = None
OUTPUT_DIR: Optional[Path] = None
TASKS_DIR: Optional[Path] = None


def init_directories(data_dir: str = None):
    """
    初始化数据目录

    Args:
        data_dir: 数据根目录路径，默认为项目根目录
    """
    global DATA_DIR, UPLOAD_DIR, OUTPUT_DIR, TASKS_DIR

    if data_dir is None:
        # 默认使用项目根目录
        project_root = Path(__file__).parent.parent.parent.resolve()
        DATA_DIR = project_root / "api-data"
    else:
        DATA_DIR = Path(data_dir).resolve()

    # 创建子目录
    UPLOAD_DIR = DATA_DIR / "uploads"
    OUTPUT_DIR = DATA_DIR / "outputs"
    TASKS_DIR = DATA_DIR / "tasks"

    # 创建所有必要的目录
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TASKS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"数据目录: {DATA_DIR}")
    print(f"  - 上传目录: {UPLOAD_DIR}")
    print(f"  - 输出目录: {OUTPUT_DIR}")
    print(f"  - 任务目录: {TASKS_DIR}")


# 创建 FastAPI 应用
app = FastAPI(
    title="视频内容脱敏 API",
    description="提供视频中目标内容自动识别与脱敏服务",
    version="1.0.0"
)

# 配置 CORS - 解除跨域限制
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，生产环境建议指定具体域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

# 文件存储配置
init_directories()  # 初始化目录结构


# ====== 数据模型 ======

class TaskCreateResponse(BaseModel):
    """任务创建响应"""
    task_id: str = Field(..., description="任务ID，用于后续查询和下载")
    message: str = Field(..., description="响应消息")


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态: pending/processing/completed/failed")
    progress: float = Field(..., description="任务总体进度 0-100")
    message: str = Field(..., description="状态消息")
    created_at: str = Field(..., description="创建时间")
    started_at: Optional[str] = Field(None, description="开始处理时间")
    completed_at: Optional[str] = Field(None, description="完成时间")
    error: Optional[str] = Field(None, description="错误信息（仅失败时）")
    result: Optional[dict] = Field(None, description="处理结果统计（仅成功时）")
    current_step: Optional[str] = Field(None, description="当前步骤: detection/masking/compression")
    current_step_progress: float = Field(0.0, description="当前步骤进度 0-100")


class TaskListResponse(BaseModel):
    """任务列表响应"""
    total: int = Field(..., description="总任务数")
    tasks: list[TaskStatusResponse] = Field(..., description="任务列表")


# ====== API 路由 ======

@app.get("/", tags=["基础"])
async def root():
    """API根路径"""
    return {
        "name": "视频目标内容脱敏 API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["基础"])
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("api/tasks", response_model=TaskCreateResponse, tags=["任务管理"])
async def create_task(
    file: UploadFile = File(..., description="要处理的视频文件"),
    detector_type: str = Form("phone", description="检测器类型: phone/keyword/idcard"),
    keywords: Optional[str] = Form(None, description="关键字列表（逗号分隔，仅keyword检测器）"),
    case_sensitive: bool = Form(False, description="关键字是否区分大小写"),
    blur_method: str = Form("gaussian", description="打码方式: gaussian/pixelate/black"),
    blur_strength: int = Form(51, description="模糊强度（仅高斯模糊）"),
    device: str = Form("cpu", description="计算设备: cpu, gpu:0, gpu:1, etc."),
    sample_interval: float = Form(1.0, description="采样间隔（秒）"),
    buffer_time: Optional[float] = Form(None, description="缓冲时间（秒）"),
    precise_location: bool = Form(False, description="是否启用精确定位（避免打码其他文字）"),
    precise_max_iterations: int = Form(3, description="精确定位的最大迭代次数")
):
    """
    上传视频并创建处理任务

    - **file**: 视频文件（支持mp4等格式）
    - **detector_type**: 检测器类型，可选 phone（手机号）、keyword（关键字）、idcard（身份证号）
    - **keywords**: 关键字列表（逗号分隔，仅当detector_type=keyword时有效）
    - **case_sensitive**: 关键字是否区分大小写
    - **blur_method**: 打码方式，可选 gaussian（高斯模糊）、pixelate（像素化）、black（黑色遮挡）
    - **blur_strength**: 模糊强度，仅对高斯模糊有效，必须为奇数
    - **device**: 计算设备，格式为 'cpu' 或 'gpu:0', 'gpu:1' 等
    - **sample_interval**: 采样间隔（秒），建议0.5-2.0
    - **buffer_time**: 缓冲时间（秒），默认等于sample_interval
    - **precise_location**: 是否启用精确定位（通过迭代验证精确定位目标，避免打码其他文字，会增加处理时间）
    - **precise_max_iterations**: 精确定位的最大迭代次数（默认3次）

    返回任务ID，用于后续查询进度和下载结果
    """
    try:
        # 验证文件类型
        if not file.filename:
            raise HTTPException(status_code=400, detail="未提供文件")

        # 验证文件扩展名
        allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式: {file_ext}，支持的格式: {', '.join(allowed_extensions)}"
            )

        # 验证参数
        if detector_type not in ['phone', 'keyword', 'idcard']:
            raise HTTPException(status_code=400, detail=f"不支持的检测器类型: {detector_type}")

        if blur_method not in ['gaussian', 'pixelate', 'black']:
            raise HTTPException(status_code=400, detail=f"不支持的打码方式: {blur_method}")

        # 验证device格式
        if not (device == 'cpu' or device.startswith('gpu:')):
            raise HTTPException(status_code=400, detail=f"无效的设备格式: {device}，请使用 'cpu' 或 'gpu:0', 'gpu:1' 等")

        if blur_strength < 1 or blur_strength % 2 == 0:
            raise HTTPException(status_code=400, detail="blur_strength 必须是大于0的奇数")

        if sample_interval <= 0:
            raise HTTPException(status_code=400, detail="sample_interval 必须大于0")

        if buffer_time is not None and buffer_time < 0:
            raise HTTPException(status_code=400, detail="buffer_time 不能为负数")

        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_filename = f"{timestamp}_{file.filename}"
        input_path = UPLOAD_DIR / input_filename

        output_filename = f"{timestamp}_masked_{file.filename}"
        output_path = OUTPUT_DIR / output_filename

        # 保存上传的文件
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 准备检测器参数
        detector_kwargs = {}
        if detector_type == 'keyword':
            if keywords:
                detector_kwargs['keywords'] = [k.strip() for k in keywords.split(',')]
            detector_kwargs['case_sensitive'] = case_sensitive

        # 创建任务
        task_queue = get_task_queue()
        task_id = task_queue.create_task(
            input_path=str(input_path),
            output_path=str(output_path),
            detector_type=detector_type,
            detector_kwargs=detector_kwargs,
            blur_method=blur_method,
            blur_strength=blur_strength,
            device=device,
            sample_interval=sample_interval,
            buffer_time=buffer_time,
            precise_location=precise_location,
            precise_max_iterations=precise_max_iterations
        )

        return TaskCreateResponse(
            task_id=task_id,
            message=f"任务创建成功，已加入处理队列"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@app.get("api/tasks/{task_id}", response_model=TaskStatusResponse, tags=["任务管理"])
async def get_task_status(task_id: str):
    """
    查询任务进度

    - **task_id**: 任务ID（创建任务时返回）

    返回任务的当前状态、进度和相关信息
    """
    task_queue = get_task_queue()
    task = task_queue.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

    return TaskStatusResponse(
        task_id=task.task_id,
        status=task.status.value,
        progress=task.progress,
        message=task.message,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        error=task.error,
        result=task.result,
        current_step=task.current_step,
        current_step_progress=task.current_step_progress
    )


@app.get("api/tasks", response_model=TaskListResponse, tags=["任务管理"])
async def list_tasks(
    status: Optional[str] = Query(None, description="按状态过滤: pending/processing/completed/failed"),
    limit: int = Query(100, ge=1, le=1000, description="返回任务数量限制")
):
    """
    获取所有任务列表

    - **status**: 可选，按状态过滤
    - **limit**: 返回的最大任务数
    """
    task_queue = get_task_queue()
    all_tasks = task_queue.get_all_tasks()

    # 过滤任务
    tasks = []
    for task in all_tasks.values():
        if status and task.status.value != status:
            continue
        tasks.append(TaskStatusResponse(
            task_id=task.task_id,
            status=task.status.value,
            progress=task.progress,
            message=task.message,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            error=task.error,
            result=task.result,
            current_step=task.current_step,
            current_step_progress=task.current_step_progress
        ))

    # 按创建时间倒序排序
    tasks.sort(key=lambda x: x.created_at, reverse=True)

    # 限制数量
    tasks = tasks[:limit]

    return TaskListResponse(
        total=len(tasks),
        tasks=tasks
    )


@app.get("api/tasks/{task_id}/download", tags=["任务管理"])
async def download_result(task_id: str):
    """
    下载处理后的视频文件

    - **task_id**: 任务ID（创建任务时返回）

    返回处理后的视频文件，仅当任务状态为 completed 时可用
    """
    task_queue = get_task_queue()
    task = task_queue.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"任务尚未完成，当前状态: {task.status.value}"
        )

    output_path = Path(task.output_path)
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="输出文件不存在")

    # 返回文件
    return FileResponse(
        path=str(output_path),
        media_type="video/mp4",
        filename=output_path.name,
        headers={
            "Content-Disposition": f'attachment; filename="{output_path.name}"'
        }
    )


@app.delete("api/tasks/{task_id}", tags=["任务管理"])
async def delete_task(task_id: str):
    """
    删除任务及其关联文件（输入文件和输出文件）

    - **task_id**: 任务ID

    仅可删除已完成或失败的任务
    """
    task_queue = get_task_queue()
    task = task_queue.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

    if task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
        raise HTTPException(
            status_code=400,
            detail=f"只能删除已完成或失败的任务，当前状态: {task.status.value}"
        )

    # 删除任务（会自动删除输入文件和输出文件）
    success = task_queue.delete_task(task_id)

    if success:
        return {"message": f"任务 {task_id} 及其关联文件已删除"}
    else:
        raise HTTPException(status_code=500, detail="删除任务失败")


# ====== 应用启动和关闭事件 ======

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化任务队列"""
    print("正在启动 API 服务器...")
    get_task_queue(storage_dir=TASKS_DIR)  # 初始化任务队列，使用配置的TASKS_DIR
    print("API 服务器启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    print("正在关闭 API 服务器...")
    task_queue = get_task_queue()
    task_queue.shutdown()
    print("API 服务器已关闭")


# ====== 主程序入口 ======

def start_server():
    """启动服务器的入口函数"""
    import uvicorn

    # 解析命令行参数
    parser = argparse.ArgumentParser(description="视频内容脱敏 API 服务器")
    parser.add_argument(
        "--data-dir",
        type=str,
        help="数据根目录路径，默认为项目根目录"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="服务器监听地址，默认为 0.0.0.0"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="服务器监听端口，默认为 8000"
    )
    args = parser.parse_args()

    # 初始化数据目录
    init_directories(args.data_dir)

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║          视频内容脱敏 API 服务器                             ║
╚══════════════════════════════════════════════════════════════╝

服务地址: http://{args.host}:{args.port}
API 文档: http://localhost:{args.port}/docs
交互式文档: http://localhost:{args.port}/redoc

主要接口:
  POST   /api/tasks              - 上传视频并创建任务
  GET    /api/tasks/{{task_id}}   - 查询任务进度
  GET    /api/tasks/{{task_id}}/download - 下载处理后的视频
  GET    /api/tasks              - 获取所有任务列表
  DELETE /api/tasks/{{task_id}}   - 删除任务

按 Ctrl+C 停止服务器
""")

    uvicorn.run(
        "privision.server:app",
        host=args.host,
        port=args.port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    start_server()
