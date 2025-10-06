# 视频手机号脱敏工具 (VideoPhoneMask)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

基于 PaddleOCR 的视频手机号自动识别与脱敏工具，可精确定位并打码视频中的中国大陆手机号。支持命令行工具、批量处理和 RESTful API 三种使用方式。

## ✨ 功能特性

### 核心功能
- **🎯 精确识别**: 精确识别中国大陆 11 位手机号
- **🔍 智能过滤**: 过滤误识别的长数字串和编号，尽可能只保留真实手机号
- **📍 精确定位**: 基于文本坐标进行像素级精确打码
- **🎨 多样打码**: 支持高斯模糊、像素化、黑色遮挡三种打码效果
- **⚡ 计算加速**: 可选 GPU 加速提升处理速度
- **📊 实时进度**: 提供美观的终端界面，实时显示处理进度和统计信息

### 处理模式
- **逐帧模式 (frame-by-frame)**: 对每一帧进行 OCR 检测，识别最准确
- **智能采样模式 (smart)**: 定期采样检测，速度快 10-30 倍，适合大部分场景

### 使用方式
- **命令行工具**: 直接使用 CLI 或安装后直接使用 `videophone-mask` 命令
- **批量处理**: 支持目录批量处理，自动递归处理子目录
- **RESTful API**: 完整的 HTTP API 接口，支持任务队列和异步处理

## 📋 目录

- [安装部署](#-安装部署)
- [快速开始](#-快速开始)
- [使用方法](#-使用方法)
  - [1. 命令行工具](#1-命令行工具推荐)
  - [2. 批量处理](#2-批量处理)
  - [3. API 服务](#3-api-服务)
  - [4. Python 模块运行](#4-python-模块运行)
- [项目结构](#-项目结构)
- [技术架构](#-技术架构)
- [性能优化](#-性能优化)
- [常见问题](#-常见问题)
- [开发指南](#-开发指南)

## 🚀 安装部署

### 环境要求

- Python 3.8+
- pip
- (可选) NVIDIA GPU + CUDA Toolkit (用于 GPU 加速)

### 安装方式

#### 方式 1: 开发模式安装（推荐）

```bash
# 克隆项目
git clone https://github.com/0xyk3r/VideoPhoneMask.git
cd VideoPhoneMask

# 安装项目（开发模式）
pip install -e .

# 验证安装
videophone-mask --help
videophone-batch --help
videophone-server --help
```

安装后可以直接使用以下命令：
- `videophone-mask` - 处理单个视频
- `videophone-batch` - 批量处理视频
- `videophone-server` - 启动 API 服务器

#### 方式 2: 仅安装依赖

```bash
# 进入项目目录
cd VideoPhoneMask

# 安装 Python 依赖（CPU 版本）
pip install -r requirements.txt
```

> **注意**: 使用此方式需要使用 `python -m src.main` 等命令运行程序

### GPU 加速安装

GPU 版本需要根据 CUDA 版本单独安装：

**检查 CUDA 版本**:
```bash
nvidia-smi  # 查看右上角 "CUDA Version: xx.x"
```

**安装 GPU 依赖**:

```bash
# 先安装通用依赖
pip install -r requirements.txt

# 根据 CUDA 版本安装 GPU 依赖
# CUDA 11.8
python -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/

# CUDA 12.6
python -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/

# CUDA 12.9
python -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu129/
```

**验证 GPU 依赖安装结果**:
```bash
python -c "import paddle; print('Device:', paddle.device.get_device()); print('GPU available:', paddle.device.is_compiled_with_cuda())"
```

### 依赖说明

主要依赖包（详见 `requirements.txt`）：

- `paddlepaddle` >= 2.5.0 - PaddlePaddle 深度学习框架
- `paddleocr` >= 2.7.0 - PaddleOCR 文字识别库
- `opencv-python` >= 4.8.0 - OpenCV 视频处理库
- `numpy` >= 1.24.0 - 数值计算库
- `fastapi` >= 0.104.0 - Web API 框架
- `uvicorn` >= 0.24.0 - ASGI 服务器
- `rich` >= 13.0.0 - 终端美化库

## ⚡ 快速开始

### 命令行工具（推荐）

```bash
# 安装后直接使用
videophone-mask input.mp4 output.mp4

# 智能采样模式
videophone-mask input.mp4 output.mp4 --mode smart

# 使用 GPU 加速
videophone-mask input.mp4 output.mp4 --device gpu:0
```

### Python 模块运行

```bash
# 单个视频处理
python -m src.main input.mp4 output.mp4 --mode smart

# 批量处理
python -m src.batch input_dir/ output_dir/ --mode smart

# 启动 API 服务器
python -m src.server
```

## 📖 使用方法

### 1. 命令行工具（推荐）

安装后可以直接使用 `videophone-mask` 命令：

#### 基本用法

```bash
# 逐帧处理模式（默认，最准确）
videophone-mask input.mp4 output.mp4

# 智能采样模式（推荐，速度快 10-30 倍）
videophone-mask input.mp4 output.mp4 --mode smart

# 指定采样间隔（仅 smart 模式）
videophone-mask input.mp4 output.mp4 --mode smart --sample-interval 2.0
```

#### 高级选项

**选择打码方式**:
```bash
# 高斯模糊（默认，效果自然）
videophone-mask input.mp4 output.mp4 --blur-method gaussian

# 像素化（马赛克效果）
videophone-mask input.mp4 output.mp4 --blur-method pixelate

# 黑色遮挡（完全遮挡）
videophone-mask input.mp4 output.mp4 --blur-method black
```

**调整模糊强度**:
```bash
# 模糊强度（仅对高斯模糊有效，必须为奇数，越大越模糊）
videophone-mask input.mp4 output.mp4 --blur-strength 71
```

**使用 GPU 加速**:
```bash
# 使用第一个 GPU
videophone-mask input.mp4 output.mp4 --device gpu:0

# 使用第二个 GPU
videophone-mask input.mp4 output.mp4 --device gpu:1
```

**精确定位模式**:
```bash
# 通过多次迭代处理尽可能精确地识别手机号区域而不包含其他内容
videophone-mask input.mp4 output.mp4 --precise-phone-location --precise-max-iterations 3
```

**可视化调试模式**:
```bash
# 处理过程中显示视频窗口（调试用）
videophone-mask input.mp4 output.mp4 --visualize
```

**禁用终端 UI 美化**:
```bash
# 使用简单的文本输出（适合日志记录）
videophone-mask input.mp4 output.mp4 --no-rich
```

#### 命令行参数

```
位置参数:
  input                         输入视频文件路径
  output                        输出视频文件路径

处理模式:
  --mode {frame-by-frame,smart}
                                处理模式 [默认: frame-by-frame]
                                  - frame-by-frame: 逐帧处理，最准确
                                  - smart: 智能采样，速度快 10-30 倍

打码设置:
  --blur-method {gaussian,pixelate,black}
                                打码方式 [默认: gaussian]
  --blur-strength STRENGTH      模糊强度（高斯模糊核大小，必须为奇数）[默认: 51]

设备设置:
  --device DEVICE               计算设备 (cpu, gpu:0, gpu:1, ...) [默认: cpu]

采样设置（仅 smart 模式）:
  --sample-interval SECONDS     采样间隔（秒）[默认: 1.0]
  --buffer-time SECONDS         缓冲时间（秒）[默认: 等于采样间隔]

精确定位:
  --precise-phone-location      启用精确定位模式（避免打码其他文字）
  --precise-max-iterations N    精确定位最大迭代次数 [默认: 3]

界面设置:
  --visualize                   可视化处理过程（显示视频窗口）
  --no-rich                     禁用 Rich UI，使用简单文本输出

其他:
  -h, --help                    显示帮助信息
```

### 2. 批量处理

使用 `videophone-batch` 命令批量处理目录中的所有视频文件。

#### 基本用法

```bash
# 批量处理目录中的所有视频
videophone-batch input_videos/ output_videos/

# 智能采样模式 + GPU 加速
videophone-batch input_videos/ output_videos/ --mode smart --device gpu:0

# 递归处理子目录
videophone-batch input_videos/ output_videos/ --recursive
```

#### 命令行参数

```
位置参数:
  input_dir                     输入视频目录
  output_dir                    输出视频目录

可选参数:
  --blur-method {gaussian,pixelate,black}
                                打码方式 [默认: gaussian]
  --device DEVICE               计算设备 (cpu, gpu:0, ...) [默认: cpu]
  --mode {frame-by-frame,smart}
                                处理模式 [默认: frame-by-frame]
  --recursive                   递归处理子目录
  --enable-rich                 启用 Rich UI 界面
  --enable-visualize            启用可视化
  --output-suffix SUFFIX        输出文件后缀 [默认: _masked]
```

#### 示例

```bash
# 批量处理，使用像素化打码
videophone-batch videos/ outputs/ --blur-method pixelate

# 批量处理子目录，使用 GPU
videophone-batch videos/ outputs/ --recursive --device gpu:0

# 批量处理，自定义输出后缀
videophone-batch videos/ outputs/ --output-suffix _processed
```

支持的视频格式：`.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`, `.webm`

### 3. API 服务

使用 `videophone-server` 命令启动 FastAPI 服务器，提供 RESTful API 接口。

#### 启动服务器

```bash
# 默认配置启动（监听 0.0.0.0:8000）
videophone-server

# 自定义端口
videophone-server --port 9000

# 自定义数据目录
videophone-server --data-dir /path/to/data
```

服务器启动后，访问：
- **API 服务地址**: http://localhost:8000
- **交互式 API 文档**: http://localhost:8000/docs
- **API 文档（备用）**: http://localhost:8000/redoc

#### API 接口说明

**1. 创建任务 - 上传视频**

`POST /api/tasks`

请求参数（`multipart/form-data`）:

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `file` | File | 是 | - | 视频文件 |
| `blur_method` | String | 否 | `gaussian` | 打码方式：gaussian/pixelate/black |
| `blur_strength` | Integer | 否 | `51` | 模糊强度（仅高斯模糊，必须为奇数） |
| `device` | String | 否 | `cpu` | 计算设备：cpu, gpu:0, gpu:1, ... |
| `sample_interval` | Float | 否 | `1.0` | 采样间隔（秒） |
| `buffer_time` | Float | 否 | `null` | 缓冲时间（秒，默认等于采样间隔） |
| `precise_phone_location` | Boolean | 否 | `false` | 是否启用精确定位 |
| `precise_max_iterations` | Integer | 否 | `3` | 精确定位最大迭代次数 |

请求示例（curl）:
```bash
curl -X POST "http://localhost:8000/api/tasks" \
  -F "file=@test.mp4" \
  -F "blur_method=gaussian" \
  -F "device=cpu" \
  -F "sample_interval=1.0"
```

请求示例（Python）:
```python
import requests

url = "http://localhost:8000/api/tasks"
files = {"file": open("test.mp4", "rb")}
data = {
    "blur_method": "gaussian",
    "blur_strength": 51,
    "device": "cpu",
    "sample_interval": 1.0
}

response = requests.post(url, files=files, data=data)
result = response.json()
task_id = result["task_id"]
print(f"任务ID: {task_id}")
```

响应示例:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "任务创建成功，已加入处理队列"
}
```

**2. 查询任务进度**

`GET /api/tasks/{task_id}`

请求示例:
```bash
curl "http://localhost:8000/api/tasks/550e8400-e29b-41d4-a716-446655440000"
```

响应示例:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 45.5,
  "message": "处理中...",
  "created_at": "2024-01-01T10:00:00",
  "started_at": "2024-01-01T10:00:05",
  "completed_at": null,
  "error": null,
  "result": null
}
```

任务状态说明:
- `pending`: 等待处理
- `processing`: 处理中
- `completed`: 已完成
- `failed`: 失败

**3. 下载处理后的视频**

`GET /api/tasks/{task_id}/download`

请求示例:
```bash
curl -O -J "http://localhost:8000/api/tasks/550e8400-e29b-41d4-a716-446655440000/download"
```

Python 示例:
```python
import requests

task_id = "550e8400-e29b-41d4-a716-446655440000"
url = f"http://localhost:8000/api/tasks/{task_id}/download"

response = requests.get(url)
if response.status_code == 200:
    with open("output.mp4", "wb") as f:
        f.write(response.content)
    print("视频下载完成")
```

**4. 获取所有任务列表**

`GET /api/tasks?status={status}&limit={limit}`

查询参数:
- `status` (可选): 按状态过滤（pending/processing/completed/failed）
- `limit` (可选): 返回的最大任务数，默认 100

**5. 删除任务**

`DELETE /api/tasks/{task_id}`

删除任务及其关联文件（仅可删除已完成或失败的任务）。

#### 完整工作流示例

```python
import requests
import time

API_BASE = "http://localhost:8000"

# 1. 上传视频
print("上传视频...")
with open("test.mp4", "rb") as f:
    files = {"file": f}
    data = {"blur_method": "gaussian", "device": "cpu", "sample_interval": 1.0}
    response = requests.post(f"{API_BASE}/api/tasks", files=files, data=data)
    task_id = response.json()["task_id"]
    print(f"任务ID: {task_id}")

# 2. 轮询查询进度
print("\n查询处理进度...")
while True:
    response = requests.get(f"{API_BASE}/api/tasks/{task_id}")
    status = response.json()

    print(f"状态: {status['status']}, 进度: {status['progress']:.1f}%")

    if status['status'] == 'completed':
        print("处理完成！")
        break
    elif status['status'] == 'failed':
        print(f"处理失败: {status['error']}")
        break

    time.sleep(2)  # 每 2 秒查询一次

# 3. 下载结果
if status['status'] == 'completed':
    print("\n下载处理后的视频...")
    response = requests.get(f"{API_BASE}/api/tasks/{task_id}/download")
    with open("output_masked.mp4", "wb") as f:
        f.write(response.content)
    print("下载完成: output_masked.mp4")

# 4. 删除任务（可选）
response = requests.delete(f"{API_BASE}/api/tasks/{task_id}")
print(response.json()["message"])
```

#### 服务器配置

默认配置：
- **主机**: `0.0.0.0`（允许外部访问）
- **端口**: `8000`
- **工作线程数**: 1（可在 `task_queue.py` 中修改 `max_workers` 参数）

默认存储目录：
- **数据根目录**: `./api-data/`
- **上传文件**: `./api-data/uploads/`
- **输出文件**: `./api-data/outputs/`
- **任务数据**: `./api-data/tasks/tasks.json`

CORS 配置：API 服务器已配置 CORS，允许所有来源的跨域请求。生产环境建议在 `src/server.py` 中修改配置。

### 4. Python 模块运行

如果未使用 `pip install -e .` 安装，可以使用 `python -m` 命令运行：

```bash
# 单个视频处理
python -m src.main input.mp4 output.mp4 --mode smart

# 批量处理
python -m src.batch input_dir/ output_dir/ --mode smart --device gpu:0

# 启动 API 服务器
python -m src.server --port 8000
```

> **注意**: 请使用 `python -m` 命令运行，不能直接运行 `python src/main.py`。

## 📁 项目结构

```
VideoPhoneMask/
├── src/                          # 源代码目录
│   ├── __init__.py
│   ├── main.py                   # 命令行工具入口
│   ├── batch.py                  # 批量处理入口
│   ├── server.py                 # API 服务器入口
│   │
│   ├── core/                     # 核心功能模块
│   │   ├── __init__.py
│   │   ├── video_processor.py   # 统一视频处理器（逐帧/智能模式）
│   │   ├── ocr_detector.py      # OCR 文本检测与识别（PaddleOCR 3.x）
│   │   ├── phone_detector.py    # 手机号识别与验证
│   │   ├── precise_locator.py   # 精确定位（迭代优化边界框）
│   │   ├── blur.py              # 打码效果实现（高斯/像素化/黑色）
│   │   └── bbox_calculator.py   # 边界框计算工具
│   │
│   ├── api/                      # API 服务模块
│   │   ├── __init__.py
│   │   └── task_queue.py        # 异步任务队列管理
│   │
│   ├── ui/                       # 用户界面模块
│   │   ├── __init__.py
│   │   ├── rich_ui.py           # Rich 终端 UI（进度条、统计、日志）
│   │   ├── progress.py          # 进度回调接口
│   │   └── visualizer.py        # 可视化调试窗口
│   │
│   ├── config/                   # 配置模块
│   │   ├── __init__.py
│   │   └── args.py              # 命令行参数解析和配置管理
│   │
│   └── test/                     # 测试模块
│       ├── __init__.py
│       ├── test_batch.py
│       ├── test_ocr_and_detector.py
│       ├── test_phone_filter.py
│       └── ...
│
├── pyproject.toml                # 项目配置和依赖定义
├── requirements.txt              # Python 依赖列表
├── README.md                     # 项目说明文档
├── INSTALL.md                    # 安装指南
└── .gitignore                    # Git 忽略文件配置
```

### 核心模块说明

#### `src/core/` - 核心功能

- **`video_processor.py`**: 统一的视频处理器
  - 支持逐帧模式和智能采样模式
  - 集成 OCR 检测、手机号识别、精确定位和打码
  - 提供进度回调接口

- **`ocr_detector.py`**: OCR 文本检测
  - 基于 PaddleOCR 3.x 实现
  - 支持 CPU 和 GPU 设备
  - 返回文本框坐标、内容和置信度

- **`phone_detector.py`**: 手机号检测
  - 使用正则表达式匹配中国大陆手机号（`1[3-9]\d{9}`）
  - 智能过滤长数字串和误识别
  - 上下文验证

- **`precise_locator.py`**: 精确定位
  - 迭代优化手机号边界框
  - 避免打码其他文字
  - 可配置最大迭代次数

- **`blur.py`**: 打码效果
  - 高斯模糊（`cv2.GaussianBlur`）
  - 像素化（降采样后放大）
  - 黑色遮挡

#### `src/api/` - API 服务

- **`task_queue.py`**: 异步任务队列
  - 基于线程池的任务处理
  - 任务状态管理（pending/processing/completed/failed）
  - 任务持久化（JSON 存储）
  - 自动清理过期任务

#### `src/ui/` - 用户界面

- **`rich_ui.py`**: Rich 终端界面
  - 实时进度条
  - 视频信息和统计面板
  - 滚动日志显示
  - 多阶段处理支持

- **`visualizer.py`**: 可视化调试
  - 实时显示检测结果
  - 支持暂停/继续
  - 快捷键控制

## 🏗 技术架构

### 核心技术栈

- **PaddleOCR 3.x**: 文本检测和识别
  - 基于深度学习的高精度 OCR
  - 支持中英文混合识别
  - GPU 加速支持

- **OpenCV**: 视频处理和打码效果实现
  - 视频读取和写入
  - 图像处理和打码

- **FastAPI**: RESTful API 框架
  - 异步支持
  - 自动生成 API 文档
  - 高性能

- **Rich**: 终端美化
  - 实时进度显示
  - 表格和面板布局
  - 颜色和样式

### 处理流程

#### 逐帧模式 (frame-by-frame)

```
视频输入 → 逐帧读取 → OCR 检测 → 手机号识别 → 精确定位（可选）→ 打码 → 写入输出
```

**特点**:
- 每一帧都进行 OCR 检测
- 识别最准确，不会遗漏
- 处理速度较慢

#### 智能采样模式 (smart)

```
视频输入 → 定期采样 → OCR 检测 → 手机号识别 → 记录时间段 → 批量打码 → 写入输出
```

**特点**:
- 定期采样检测（默认每 1 秒）
- 检测到的手机号应用到时间段内的所有帧
- 速度快 10-30 倍
- 适合大部分静态或慢速变化场景

### 手机号识别流程

1. **文本检测**: PaddleOCR 检测图像中的所有文本区域
2. **文本识别**: OCR 识别文本内容和置信度
3. **手机号匹配**: 正则表达式匹配 11 位手机号（`1[3-9]\d{9}`）
4. **上下文验证**: 检查是否是超长数字串的一部分
5. **精确定位** (可选): 迭代优化边界框，确保只包含手机号
6. **打码**: 应用选定的打码效果

### 打码方法

- **高斯模糊 (gaussian)**: 使用 `cv2.GaussianBlur()` 实现自然模糊效果
- **像素化 (pixelate)**: 降采样后放大，产生马赛克效果
- **黑色遮挡 (black)**: 纯黑色矩形覆盖，完全遮挡

## 🚀 性能优化

### 推荐配置

1. **使用 GPU 加速**:
   ```bash
   videophone-mask input.mp4 output.mp4 --device gpu:0
   ```
   GPU 可提升 OCR 处理速度 3-10 倍。

2. **使用智能采样模式**:
   ```bash
   videophone-mask input.mp4 output.mp4 --mode smart
   ```
   适合大部分场景，速度快 10-30 倍。

3. **调整采样间隔**:
   ```bash
   # 低动态视频（手机号位置变化慢）
   videophone-mask input.mp4 output.mp4 --mode smart --sample-interval 2.0

   # 高动态视频（手机号位置变化快）
   videophone-mask input.mp4 output.mp4 --mode smart --sample-interval 0.5
   ```

4. **视频预处理**:
   - 超高分辨率视频建议先降低分辨率
   - 使用 H.264 编码以提高处理速度

5. **API 并发处理**:
   修改 `src/api/task_queue.py` 中的 `max_workers` 参数增加并发数：
   ```python
   # 在 src/server.py 的 startup_event() 中
   get_task_queue(storage_dir=TASKS_DIR, max_workers=2)  # 增加并发数
   ```

## 🔧 常见问题

### Q1: 如何验证 GPU 是否可用？

```bash
# 检查 CUDA
nvidia-smi

# 检查 GPU 支持
python -c "import paddle; print('GPU available:', paddle.device.is_compiled_with_cuda())"
```

如果输出 `GPU available: True`，表示 GPU 可用。

### Q2: 为什么不能直接运行 `python src/main.py`？

由于导入语句使用了 `src.xxx` 格式（如 `from src.config import parse_args`），Python 需要将 `src` 作为包来导入。

**解决方案**:
- 使用 `python -m src.main` 运行
- 或使用 `pip install -e .` 安装后直接使用 `videophone-mask` 命令

### Q3: 首次运行很慢？

首次运行会自动下载模型文件（约 100-200 MB），需要网络连接。下载完成后会缓存在本地，后续运行会直接使用缓存。

### Q4: 处理速度慢怎么办？

1. 使用 GPU 加速：`--device gpu:0`
2. 使用智能采样模式：`--mode smart`
3. 增加采样间隔：`--sample-interval 2.0`
4. 降低视频分辨率

### Q5: 识别准确率不高？

1. 确保视频清晰度足够
2. 复杂字体或背景会影响 OCR 效果
3. 尝试使用 `--precise-phone-location` 精确定位模式
4. 使用逐帧模式而非智能采样模式

### Q6: API 任务一直处于 pending 状态？

1. 检查服务器日志
2. 确认视频文件格式正确
3. 确认 PaddleOCR 模型已下载
4. 检查任务队列是否正常（查看 `api-data/tasks/tasks.json`）

### Q7: 如何自定义 API 服务的数据目录？

```bash
videophone-server --data-dir /path/to/data
```

### Q8: 如何在生产环境部署 API 服务？

1. 使用反向代理（如 Nginx）
2. 配置 HTTPS
3. 修改 CORS 设置（在 `src/server.py` 中）
4. 使用进程管理工具（如 systemd、supervisor）

### Q9: 支持哪些视频格式？

支持所有 OpenCV 支持的格式，包括：`.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`, `.webm`

输出格式当前仅支持 MP4。

## 🛠 开发指南

### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/0xyk3r/VideoPhoneMask.git
cd VideoPhoneMask

# 安装开发依赖
pip install -e ".[dev]"
```

### 运行测试

```bash
# 运行所有测试
pytest src/test/

# 运行特定测试
python -m src.test.test_phone_filter
python -m src.test.test_ocr_and_detector
```

### 代码结构设计

项目采用模块化设计：

- **分离关注点**: 核心功能、API、UI 和配置分别独立
- **配置驱动**: 使用 `ProcessConfig` 统一管理配置
- **接口抽象**: `ProgressCallback` 接口解耦业务逻辑和 UI
- **可扩展性**: 易于添加新的打码方法、检测器或 UI

### 添加新的打码方法

1. 在 `src/core/blur.py` 中添加新的打码函数
2. 在 `apply_blur()` 函数中添加新的分支
3. 更新 `ProcessConfig` 中的 `blur_method` 类型提示
4. 更新命令行参数解析

### 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。

## 🙏 致谢

- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - 优秀的开源 OCR 工具
- [OpenCV](https://opencv.org/) - 强大的计算机视觉库
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Web 框架
- [Rich](https://github.com/Textualize/rich) - 终端美化库

## 📧 联系方式

- 作者: 0xyk3r
- GitHub: [https://github.com/0xyk3r/VideoPhoneMask](https://github.com/0xyk3r/VideoPhoneMask)
- Issues: [https://github.com/0xyk3r/VideoPhoneMask/issues](https://github.com/0xyk3r/VideoPhoneMask/issues)

---

**注意**: 本工具仅用于合法的隐私保护用途，请勿用于非法目的。使用本工具处理的视频内容，用户需自行承担相关法律责任。
