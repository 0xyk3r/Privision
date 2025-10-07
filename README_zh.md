# Privision - 视频内容智能脱敏工具

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

> **通用视频内容脱敏解决方案** - 基于 OCR 的智能信息识别与打码系统

> 中文 | [English](README.md)

Privision 是一款强大的视频内容脱敏工具，采用先进的 OCR 技术自动识别并打码视频中的敏感信息。支持**手机号、身份证号、自定义关键字**等多种检测模式，提供命令行、批量处理和 RESTful API 三种使用方式。

## 🌟 核心亮点

### 🎯 多场景检测支持

- **📱 手机号检测**: 精确识别中国大陆 11 位手机号，智能过滤误报
- **🆔 身份证号检测**: 识别中国大陆 18 位身份证号，包含基础有效性验证
- **🔑 关键字检测**: 自定义关键字列表，灵活检测任意敏感词汇
- **🔌 可扩展架构**: 基于工厂模式设计，轻松添加新的检测器类型

### ⚡ 高性能处理

- **🚀 双模式处理**:
  - **逐帧模式**: 精确识别，适合高精度要求场景
  - **智能采样模式**: 速度提升 10-30 倍，适合大多数场景
- **💎 GPU 加速**: 支持 CUDA 加速，大幅提升处理速度
- **🎯 精确定位**: 迭代优化算法，确保只打码目标内容，避免误伤

### 🎨 灵活的打码方式

- **高斯模糊 (Gaussian)**: 自然柔和的模糊效果
- **像素化 (Pixelate)**: 经典马赛克效果
- **黑色遮挡 (Black)**: 完全遮盖，强力保护

### 🛠 多种使用方式

- **命令行工具**: 简单易用，适合单个视频处理
- **批量处理**: 目录级批量处理，支持递归子目录
- **RESTful API**: 完整的 HTTP API，支持异步任务队列
- **可视化调试**: 实时预览检测结果和打码效果

## 📋 目录

- [快速开始](#-快速开始)
- [安装部署](#-安装部署)
- [使用指南](#-使用指南)
  - [命令行工具](#1-命令行工具)
  - [批量处理](#2-批量处理)
  - [API 服务](#3-api-服务)
- [检测器说明](#-检测器说明)
- [项目架构](#-项目架构)
- [性能优化](#-性能优化)
- [常见问题](#-常见问题)

## ⚡ 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/0xyk3r/Privision.git
cd Privision

# 开发模式安装（推荐）
pip install -e .
```

### 基本使用

```bash
# 1. 检测并打码手机号
privision input.mp4 output.mp4

# 2. 检测身份证号
privision input.mp4 output.mp4 --detector idcard

# 3. 检测自定义关键字
privision input.mp4 output.mp4 --detector keyword --keywords 密码 账号 姓名

# 4. 智能采样模式（快速）
privision input.mp4 output.mp4 --mode smart

# 5. GPU 加速
privision input.mp4 output.mp4 --device gpu:0 --mode smart
```

## 🚀 安装部署

### 环境要求

- Python 3.8+
- pip
- (可选) NVIDIA GPU + CUDA Toolkit

### 安装步骤

#### 方式 1: 开发模式安装（推荐）

```bash
# 克隆项目
git clone https://github.com/0xyk3r/Privision.git
cd Privision

# 安装项目（开发模式）
pip install -e .

# 验证安装
privision --help
```

安装后可直接使用以下命令：
- `privision` - 单个视频处理
- `privision-batch` - 批量处理
- `privision-server` - API 服务器

#### 方式 2: 仅安装依赖

```bash
cd Privision
pip install -r requirements.txt
```

> 使用此方式需通过 `python -m privision.main` 运行程序

### GPU 加速安装

**检查 CUDA 版本**:
```bash
nvidia-smi  # 查看右上角 "CUDA Version: xx.x"
```

**安装 GPU 依赖**:

```bash
# 先安装通用依赖
pip install -r requirements.txt

# 根据 CUDA 版本选择安装
# CUDA 11.8
python -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/

# CUDA 12.6
python -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/

# CUDA 12.9
python -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu129/
```

**验证 GPU 安装**:
```bash
python -c "import paddle; print('GPU available:', paddle.device.is_compiled_with_cuda())"
```

### 核心依赖

- `paddlepaddle` >= 3.0.0 - 深度学习框架
- `paddleocr` >= 3.0.0 - OCR 识别引擎
- `opencv-python` >= 4.8.0 - 视频处理
- `numpy` >= 1.24.0 - 数值计算
- `fastapi` >= 0.104.0 - API 框架
- `rich` >= 13.0.0 - 终端美化

## 📖 使用指南

### 1. 命令行工具

#### 基本用法

```bash
# 检测手机号（默认）
privision input.mp4 output.mp4

# 检测身份证号
privision input.mp4 output.mp4 --detector idcard

# 检测自定义关键字
privision input.mp4 output.mp4 --detector keyword --keywords 密码 账号 用户名

# 智能采样模式（推荐）
privision input.mp4 output.mp4 --mode smart

# GPU 加速
privision input.mp4 output.mp4 --device gpu:0
```

#### 高级选项

**选择打码方式**:
```bash
# 高斯模糊（默认）
privision input.mp4 output.mp4 --blur-method gaussian

# 像素化（马赛克）
privision input.mp4 output.mp4 --blur-method pixelate

# 黑色遮挡
privision input.mp4 output.mp4 --blur-method black
```

**精确定位模式**:
```bash
# 启用精确定位，尽可能避免打码无关内容
privision input.mp4 output.mp4 --precise-location
```

**可视化调试**:
```bash
# 显示实时处理窗口
privision input.mp4 output.mp4 --visualize
```

#### 完整参数

```
位置参数:
  input                         输入视频文件路径
  output                        输出视频文件路径

检测器设置:
  --detector {phone,keyword,idcard}
                                检测器类型 [默认: phone]
                                  phone   - 手机号检测
                                  keyword - 关键字检测
                                  idcard  - 身份证号检测

  --keywords WORD [WORD ...]    关键字列表（仅 keyword 检测器）
  --case-sensitive              关键字区分大小写（仅 keyword 检测器）

处理模式:
  --mode {frame-by-frame,smart}
                                处理模式 [默认: frame-by-frame]
                                  frame-by-frame - 逐帧处理
                                  smart          - 智能采样

打码设置:
  --blur-method {gaussian,pixelate,black}
                                打码方式 [默认: gaussian]
  --blur-strength INT           模糊强度（必须为奇数）[默认: 51]

设备设置:
  --device DEVICE               计算设备 (cpu, gpu:0, gpu:1, ...) [默认: cpu]

采样设置（仅 smart 模式）:
  --sample-interval FLOAT       采样间隔（秒）[默认: 1.0]
  --buffer-time FLOAT           缓冲时间（秒）

精确定位:
  --precise-location            启用精确定位模式
  --precise-max-iterations INT  最大迭代次数 [默认: 3]

界面设置:
  --visualize                   启用可视化窗口
  --no-rich                     禁用 Rich UI

其他:
  -h, --help                    显示帮助信息
```

### 2. 批量处理

使用 `privision-batch` 命令批量处理目录中的所有视频。

#### 基本用法

```bash
# 批量处理目录
privision-batch input_dir/ output_dir/

# 递归处理子目录
privision-batch input_dir/ output_dir/ --recursive

# 使用身份证检测器批量处理
privision-batch input_dir/ output_dir/ --detector idcard

# 智能模式 + GPU 加速
privision-batch input_dir/ output_dir/ --mode smart --device gpu:0
```

#### 参数说明

```
位置参数:
  input_dir                     输入视频目录
  output_dir                    输出视频目录

检测器设置:
  --detector {phone,keyword,idcard}
                                检测器类型 [默认: phone]
  --keywords WORD [WORD ...]    关键字列表（仅 keyword 检测器）
  --case-sensitive              关键字区分大小写

可选参数:
  --blur-method {gaussian,pixelate,black}
                                打码方式 [默认: gaussian]
  --device DEVICE               计算设备 [默认: cpu]
  --mode {frame-by-frame,smart}
                                处理模式 [默认: frame-by-frame]
  --recursive                   递归处理子目录
  --output-suffix SUFFIX        输出文件后缀 [默认: _masked]
```

支持的视频格式：`.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`, `.webm`

### 3. API 服务

使用 `privision-server` 启动 FastAPI 服务器，提供 RESTful API 接口。

#### 启动服务器

```bash
# 默认配置启动
privision-server

# 自定义端口
privision-server --port 9000

# 自定义数据目录
privision-server --data-dir /path/to/data
```

服务器启动后：
- API 服务地址: http://localhost:8000
- 交互式文档: http://localhost:8000/docs
- API 文档: http://localhost:8000/redoc

#### API 接口

**1. 创建任务**

`POST /api/tasks`

```bash
curl -X POST "http://localhost:8000/api/tasks" \
  -F "file=@test.mp4" \
  -F "detector_type=phone" \
  -F "blur_method=gaussian" \
  -F "device=cpu"
```

支持的参数：
- `file`: 要处理的视频文件（必需）
- `detector_type`: 检测器类型 (phone/keyword/idcard)
- `keywords`: 关键字列表（仅 keyword 检测器）
- `case_sensitive`: 是否区分大小写（仅 keyword 检测器）
- `blur_method`: 打码方式: (gaussian/pixelate/black)
- `blur_strength`: 模糊强度（仅高斯模糊，奇数，默认 51）
- `device`: 计算设备: (cpu, gpu:0, gpu:1, etc.)
- `sample_interval`: 采样间隔（秒）
- `buffer_time`: 缓冲时间（秒）
- `precise_location`: 是否启用精确定位
- `precise_max_iterations`: 精确定位最大迭代次数（默认 3）

响应:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "任务创建成功"
}
```

**2. 查询任务进度**

`GET /api/tasks/{task_id}`

```bash
curl "http://localhost:8000/api/tasks/{task_id}"
```

**3. 下载处理结果**

`GET /api/tasks/{task_id}/download`

```bash
curl -O -J "http://localhost:8000/api/tasks/{task_id}/download"
```

**4. 获取任务列表**

`GET /api/tasks?status={status}&limit={limit}`

支持的参数:
- `status` (可选): 按状态过滤（pending/processing/completed/failed）
- `limit` (可选): 返回的最大任务数，默认 100

**5. 删除任务**

`DELETE /api/tasks/{task_id}`

#### Python 客户端示例

```python
import requests
import time

API_BASE = "http://localhost:8000"

# 1. 上传视频
with open("test.mp4", "rb") as f:
    files = {"file": f}
    data = {
        "detector_type": "phone",
        "blur_method": "gaussian",
        "device": "cpu"
    }
    response = requests.post(f"{API_BASE}/api/tasks", files=files, data=data)
    task_id = response.json()["task_id"]

# 2. 轮询进度
while True:
    response = requests.get(f"{API_BASE}/api/tasks/{task_id}")
    status = response.json()

    if status['status'] == 'completed':
        break
    time.sleep(2)

# 3. 下载结果
response = requests.get(f"{API_BASE}/api/tasks/{task_id}/download")
with open("output.mp4", "wb") as f:
    f.write(response.content)
```

## 🎯 检测器说明

### 1. 手机号检测器 (phone)

**功能**: 识别中国大陆 11 位手机号

**特点**:
- 正则匹配：`1[3-9]\d{9}`
- 智能过滤长数字串和误报
- 上下文验证，避免误识别

**使用**:
```bash
privision input.mp4 output.mp4 --detector phone
```

### 2. 身份证号检测器 (idcard)

**功能**: 识别中国大陆 18 位身份证号

**特点**:
- 正则匹配：`\d{17}[\dXx]`
- 日期有效性验证
- 排除无效号码

**使用**:
```bash
privision input.mp4 output.mp4 --detector idcard
```

### 3. 关键字检测器 (keyword)

**功能**: 检测自定义关键字

**特点**:
- 支持自定义关键字列表
- 支持中英文混合
- 可选大小写敏感
- 智能边界匹配

**使用**:
```bash
# 默认关键字（密码、账号、用户名等）
privision input.mp4 output.mp4 --detector keyword

# 自定义关键字
privision input.mp4 output.mp4 --detector keyword --keywords 姓名 电话 地址

# 区分大小写
privision input.mp4 output.mp4 --detector keyword --keywords Password --case-sensitive
```

### 扩展自定义检测器

项目采用工厂模式设计，可轻松扩展新的检测器：

1. 继承 `BaseDetector` 基类
2. 实现必需的抽象方法
3. 在 `DetectorFactory` 中注册

详见 `src/privision/core/detector_base.py` 和 `src/privision/core/detector_factory.py`

## 🏗 项目架构

### 目录结构

```
Privision/
├── src/                          # 源代码
│   ├── privision/                # 主包
│   │  ├── main.py                   # CLI 入口
│   │  ├── batch.py                  # 批量处理入口
│   │  ├── server.py                 # API 服务器入口
│   │  │
│   │  ├── core/                     # 核心功能
│   │  │   ├── video_processor.py   # 视频处理器（逐帧/智能）
│   │  │   ├── ocr_detector.py      # OCR 检测
│   │  │   ├── detector_base.py     # 检测器基类
│   │  │   ├── detector_factory.py  # 检测器工厂
│   │  │   ├── detectors/           # 检测器实现
│   │  │   │   ├── phone_detector.py
│   │  │   │   ├── idcard_detector.py
│   │  │   │   └── keyword_detector.py
│   │  │   ├── precise_locator.py   # 精确定位
│   │  │   ├── blur.py              # 打码效果
│   │  │   └── bbox_calculator.py   # 边界框计算
│   │  │
│   │  ├── api/                      # API 服务
│   │  │   └── task_queue.py        # 任务队列管理
│   │  │
│   │  ├── ui/                       # 用户界面
│   │  │   ├── rich_ui.py           # Rich 终端 UI
│   │  │   ├── progress.py          # 进度回调接口
│   │  │   └── visualizer.py        # 可视化窗口
│   │  │
│   │  ├── config/                   # 配置管理
│   │  │   └── args.py              # 参数解析
│   │  │
│   │  └── test/                     # 测试模块
│
├── pyproject.toml                # 项目配置
├── requirements.txt              # 依赖列表
├── README.md                     # 本文档
```

### 核心模块

#### 检测器架构

```
BaseDetector (抽象基类)
    ├── PhoneDetector (手机号)
    ├── IDCardDetector (身份证号)
    └── KeywordDetector (关键字)

DetectorFactory (工厂)
    └── create_detector()
```

#### 处理流程

**逐帧模式**:
```
视频输入 → 逐帧读取 → OCR → 检测器 → 精确定位(可选) → 打码 → 输出
```

**智能采样模式**:
```
视频输入 → 定期采样 → OCR → 检测器 → 记录区域 → 批量打码 → 输出
```

### 技术栈

- **PaddleOCR**: 文本检测和识别
- **OpenCV**: 视频处理和打码
- **FastAPI**: RESTful API 框架
- **Rich**: 终端美化
- **NumPy**: 数值计算

## 🚀 性能优化

### 推荐配置

**1. 使用 GPU 加速**
```bash
privision input.mp4 output.mp4 --device gpu:0
```
GPU 可提升 OCR 速度 3-10 倍

**2. 使用智能采样模式**
```bash
privision input.mp4 output.mp4 --mode smart
```
速度提升 10-30 倍，适合大部分场景

**3. 调整采样间隔**
```bash
# 静态场景（手机号位置变化慢）
privision input.mp4 output.mp4 --mode smart --sample-interval 2.0

# 动态场景（手机号位置变化快）
privision input.mp4 output.mp4 --mode smart --sample-interval 0.5
```

**4. 视频预处理**
- 超高分辨率视频建议先降低分辨率
- 使用 H.264 编码提高处理速度

**5. API 并发处理**

修改 `src/privision/api/task_queue.py` 中的 `max_workers` 参数：
```python
get_task_queue(storage_dir=TASKS_DIR, max_workers=2)  # 增加并发数
```

## 🔧 常见问题

### Q1: 如何验证 GPU 是否可用？

```bash
# 检查 CUDA
nvidia-smi

# 检查 PaddlePaddle GPU 支持
python -c "import paddle; print('GPU available:', paddle.device.is_compiled_with_cuda())"
```

### Q2: 为什么不能直接运行 `python privision/main.py`？

由于导入语句使用了 `privision.xxx` 格式，Python 需要将 `privision` 作为包导入。

**解决方案**:
- 使用 `python -m privision.main` 运行
- 或使用 `pip install -e .` 安装后直接使用 `privision` 命令

### Q3: 首次运行很慢？

首次运行会自动下载 PaddleOCR 模型文件（约 100-200 MB），需要网络连接。下载后会缓存在本地。

### Q4: 如何提高识别准确率？

1. 确保视频清晰度足够
2. 使用逐帧模式而非智能采样
3. 启用精确定位模式：`--precise-location`
4. 复杂字体或背景会影响 OCR 效果

### Q5: 如何添加新的检测器？

1. 在 `src/privision/core/detectors/` 创建新的检测器类
2. 继承 `BaseDetector` 并实现必需方法
3. 在 `DetectorFactory._detectors` 中注册
4. 更新命令行参数和文档

### Q6: 支持哪些视频格式？

支持所有 OpenCV 支持的格式：`.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`, `.webm`

输出格式当前仅支持 MP4。

### Q7: 如何在生产环境部署 API 服务？

1. 使用反向代理（如 Nginx）
2. 配置 HTTPS
3. 修改 CORS 设置（在 `src/privision/server.py` 中）
4. 使用进程管理工具（如 systemd、supervisor）
5. 配置日志和监控

## 🛠 开发指南

### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/0xyk3r/Privision.git
cd Privision

# 安装开发依赖
pip install -e ".[dev]"
```

### 运行测试

```bash
# 运行所有测试
pytest src/privision/test/

# 运行特定测试
python -m privision.test.test_phone_filter
python -m privision.test.test_ocr_and_detector
```

### 代码结构设计

- **分离关注点**: 核心功能、API、UI 和配置独立模块化
- **配置驱动**: 使用 `ProcessConfig` 统一管理配置
- **接口抽象**: `ProgressCallback` 接口解耦业务和 UI
- **工厂模式**: `DetectorFactory` 管理检测器创建
- **可扩展性**: 易于添加新的检测器、打码方法和 UI

### 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/YourFeature`)
3. 提交更改 (`git commit -m 'Add some YourFeature'`)
4. 推送到分支 (`git push origin feature/YourFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。

## 🙏 致谢

- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - OCR 工具
- [OpenCV](https://opencv.org/) - 计算机视觉库
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Web 框架
- [Rich](https://github.com/Textualize/rich) - 终端美化库

## 📧 联系方式

- 作者: 0xyk3r
- GitHub: [https://github.com/0xyk3r/Privision](https://github.com/0xyk3r/Privision)
- Issues: [https://github.com/0xyk3r/Privision/issues](https://github.com/0xyk3r/Privision/issues)

---

**注意**: 本工具仅用于合法的隐私保护用途，请勿用于非法目的。使用本工具处理的视频内容，用户需自行承担相关法律责任。
