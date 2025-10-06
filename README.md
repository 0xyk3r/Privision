# 视频手机号脱敏工具 (VideoPhoneMask)

基于 PaddleOCR 的视频手机号自动识别与脱敏工具，可精确定位并打码视频中的中国大陆手机号。支持命令行和API两种使用方式。

## 功能特性

- **精确识别**: 使用 PaddleOCR 精确识别中国大陆 11 位手机号
- **智能过滤**: 过滤误识别的长数字串和编号，只保留真实手机号
- **精确定位**: 基于 OCR 返回的文本框坐标进行像素级精确打码
- **多种打码方式**: 支持高斯模糊、像素化、黑色遮挡三种打码效果
- **适应性强**: 支持不同分辨率、帧率、字体、颜色的视频
- **GPU 加速**: 可选 GPU 加速提升处理速度
- **实时进度**: 显示处理进度和统计信息
- **RESTful API**: 提供完整的 HTTP API 接口，支持任务队列和异步处理

## 技术方案

### 核心技术栈

- **PaddleOCR**: 文本检测和识别
- **OpenCV**: 视频处理和打码效果实现
- **FastAPI**: RESTful API 框架

### 处理流程

```
视频输入 → 逐帧读取 → OCR文本检测 → 文本识别 → 手机号匹配 → 精确定位 → 区域打码 → 视频输出
```

## 安装部署

### 1. 环境要求

- Python 3.8+
- pip

### 2. 安装依赖

#### CPU 版本

```bash
# 进入项目目录
cd VideoPhoneMask

# 安装 Python 依赖（CPU 版本）
pip install -r requirements.txt
```

#### GPU 版本（需要 NVIDIA GPU + CUDA）

**重要**: PaddlePaddle GPU 版本不能直接通过 `pip install paddlepaddle-gpu` 安装！

**Windows 系统**:

```bash
# 1. 先安装 CPU 版本的其他依赖
pip install -r requirements.txt

# 2. 检查 CUDA 版本
nvidia-smi

# 如果没有 CUDA，需要先安装 CUDA Toolkit
# 下载地址: https://developer.nvidia.com/cuda-downloads

# 3. 根据 CUDA 版本安装 PaddlePaddle GPU 版
# CUDA 11.8
python -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/

# CUDA 12.6
python -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/

# CUDA 12.9
python -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu129/
```

**Linux 系统**:

```bash
# CUDA 11.8
python3 -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/

# CUDA 12.6
python3 -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/

# CUDA 12.9
python3 -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu129/
```

**验证 GPU 安装**:

```bash
python -c "import paddle; print(paddle.device.get_device()); print('GPU available:', paddle.device.is_compiled_with_cuda())"
```

### 3. 依赖说明

主要依赖包：

- `paddlepaddle`: PaddlePaddle 深度学习框架
- `paddleocr`: PaddleOCR 文字识别库
- `opencv-python`: OpenCV 视频处理库
- `numpy`: 数值计算库
- `fastapi`: Web API 框架
- `uvicorn`: ASGI 服务器

## 使用方法

### 方式一：命令行模式

#### 智能采样模式（推荐，速度最快）

```bash
cd src

# 1秒采样一次，速度提升 10-30 倍（默认）
python main_smart.py input.mp4 output.mp4

# 效率更高的采样（2秒一次）
python main_smart.py input.mp4 output.mp4 --sample-interval 2.0

# 配置缓冲时间防止泄露
python main_smart.py input.mp4 output.mp4 --buffer-time 0.5
```

#### 默认模式（逐帧处理，最准确）

```bash
cd src
python main.py input.mp4 output.mp4
```

#### 高级选项

**1. 选择打码方式**

```bash
# 高斯模糊（默认，效果自然）
python main.py input.mp4 output.mp4 --blur-method gaussian

# 像素化（马赛克效果）
python main.py input.mp4 output.mp4 --blur-method pixelate

# 黑色遮挡（完全遮挡，适合高安全要求场景）
python main.py input.mp4 output.mp4 --blur-method black
```

**2. 调整模糊强度**

```bash
# 模糊强度（仅对高斯模糊有效，必须为奇数，越大越模糊）
python main.py input.mp4 output.mp4 --blur-strength 71
```

**3. 使用 GPU 加速**

```bash
# 需要安装 paddlepaddle-gpu
python main.py input.mp4 output.mp4 --use-gpu
```

**4. 可视化模式**

```bash
# 处理过程中显示视频窗口（调试用）
python main.py input.mp4 output.mp4 --visualize
```

**5. 精确定位模式**

```bash
# 通过多次迭代处理尽可能精确的识别手机号区域而不包含其他内容
python main_smart.py input.mp4 output.mp4 --precise-phone-location [--precise-max-iterations 3]
```

#### 多选项示例

```bash
# 使用像素化打码 + GPU 加速 + 精确定位模式
python main.py video/test.mp4 video/test_masked.mp4 --blur-method pixelate --use-gpu  --precise-phone-location
```

#### 命令行参数

```
位置参数:
  input                             输入视频文件路径
  output                            输出视频文件路径

可选参数:
  -h, --help                        显示帮助信息
  --blur-method                     打码方式 [默认: gaussian] {gaussian,pixelate,black}
  --blur-strength                   模糊强度（高斯模糊核大小，必须为奇数）[默认: 51]
  --use-gpu                         使用GPU加速OCR识别
  --sample-interval                 采样间隔（秒），默认 1.0
  --buffer-time                     缓冲时间（秒），默认等于采样间隔
  --visualize                       可视化处理过程
  --precise-phone-location          启用精确定位模式
  --precise-max-iterations          精确定位最大迭代次数 [默认: 3]
```

### 方式二：API 模式

#### 启动 API 服务器

```bash
cd src
python api_server.py
```

服务器启动后，访问：

- **API 服务地址**: http://localhost:8000
- **交互式 API 文档**: http://localhost:8000/docs
- **API 文档（备用）**: http://localhost:8000/redoc

#### API 接口说明

**1. 上传视频并创建任务**

接口: `POST /api/tasks`

请求参数（multipart/form-data）:

- `file` (必需): 视频文件
- `blur_method` (可选): 打码方式，默认 `gaussian`
- `blur_strength` (可选): 模糊强度，默认 `51`
- `use_gpu` (可选): 是否使用GPU，默认 `false`
- `sample_interval` (可选): 采样间隔（秒），默认 `1.0`
- `buffer_time` (可选): 缓冲时间（秒），默认等于 `sample_interval`
- `precise_phone_location` (可选): 是否启用精确定位模式，默认 `false`
- `precise_max_iterations` (可选): 精确定位最大迭代次数，默认 `3`

请求示例（curl）:

```bash
curl -X POST "http://localhost:8000/api/tasks" \
  -F "file=@test.mp4" \
  -F "blur_method=gaussian" \
  -F "use_gpu=false" \
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
    "use_gpu": False,
    "sample_interval": 1.0
}

response = requests.post(url, files=files, data=data)
result = response.json()
task_id = result["task_id"]
print(f"任务ID: {task_id}")
```

**2. 查询任务进度**

接口: `GET /api/tasks/{task_id}`

请求示例（Python）:

```python
import requests

task_id = "550e8400-e29b-41d4-a716-446655440000"
url = f"http://localhost:8000/api/tasks/{task_id}"

response = requests.get(url)
status = response.json()
print(f"状态: {status['status']}")
print(f"进度: {status['progress']}%")
```

任务状态说明:

- `pending`: 等待处理
- `processing`: 处理中
- `completed`: 已完成
- `failed`: 失败

**3. 下载处理后的视频**

接口: `GET /api/tasks/{task_id}/download`

请求示例（Python）:

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

接口: `GET /api/tasks`

请求参数:

- `status` (可选): 按状态过滤
- `limit` (可选): 返回的最大任务数，默认100

**5. 删除任务**

接口: `DELETE /api/tasks/{task_id}`

#### 完整工作流示例（Python）

```python
import requests
import time

API_BASE = "http://localhost:8000"

# 1. 上传视频
print("上传视频...")
with open("test.mp4", "rb") as f:
    files = {"file": f}
    data = {
        "blur_method": "gaussian",
        "use_gpu": False,
        "sample_interval": 1.0
    }
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

    time.sleep(2)  # 每2秒查询一次

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

#### API 配置说明

**服务器配置**

默认配置：

- **主机**: `0.0.0.0`（允许外部访问）
- **端口**: `8000`
- **工作线程数**: 2

**存储配置**

默认存储目录：

- **上传文件**: `./uploads/`
- **输出文件**: `./outputs/`
- **任务数据**: `./tasks/tasks.json`

**CORS 配置**

API 服务器已配置 CORS，允许所有来源的跨域请求。如有需求请在 `src/api_server.py` 中修改：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 指定允许的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 项目结构

```
VideoPhoneMask/
├── src/                      # Python 源代码
│   ├── main.py               # 命令行主程序入口
│   ├── main_smart.py         # 智能采样模式入口
│   ├── api_server.py         # API 服务器
│   ├── task_queue.py         # 任务队列管理
│   ├── video_processor.py    # 视频处理模块
│   ├── ocr_detector.py       # OCR 检测模块
│   └── phone_detector.py     # 手机号识别模块
├── requirements.txt          # Python 依赖
├── README.md                 # 项目说明文档
```

## 工作原理

### 1. 文本检测

使用 PaddleOCR 的检测模型识别视频帧中的所有文本区域，返回每个文本框的四个顶点坐标：

```
[[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
```

### 2. 文本识别

对检测到的文本区域进行 OCR 识别，获取文本内容和置信度。

### 3. 手机号匹配

使用正则表达式 `1[3-9]\d{9}` 匹配中国大陆 11 位手机号：

- 第 1 位：1
- 第 2 位：3-9
- 第 3-11 位：0-9
- 支持空格、横线等分隔符自动清理

### 4. 精确打码

基于 OCR 返回的精确坐标，在手机号区域应用打码效果：

- **高斯模糊**: `cv2.GaussianBlur()` - 自然模糊效果
- **像素化**: 降采样后放大 - 马赛克效果
- **黑色遮挡**: 纯黑色矩形覆盖

## 性能优化建议

1. **GPU 加速**: 如有 NVIDIA GPU，建议使用 `--use-gpu` 选项或 API 中设置 `use_gpu=true`
2. **分辨率优化**: 超高分辨率视频建议先降低分辨率再处理
3. **合理设置采样间隔**:
    - 低动态视频：可设置为 `2.0` 秒
    - 高动态视频：建议设置为 `0.5-1.0` 秒
4. **API 并发处理**: 修改 `TaskQueue` 的 `max_workers` 参数增加并发数

## 常见问题

### Q1: 安装 PaddleOCR 时遇到问题？

```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple paddleocr
```

### Q2: GPU 加速无法使用？

**步骤1: 检查是否有 NVIDIA GPU**

```bash
# Windows/Linux: 检查 GPU
nvidia-smi
```

如果提示命令不存在，说明没有安装 NVIDIA 驱动或没有 NVIDIA GPU。

**步骤2: 安装 CUDA Toolkit**

访问 [NVIDIA CUDA 下载页面](https://developer.nvidia.com/cuda-downloads)，选择操作系统和版本，下载并安装。

**步骤3: 检查 CUDA 版本**

```bash
# 方法1: 查看 CUDA 编译器版本
nvcc --version

# 方法2: 查看驱动支持的 CUDA 版本
nvidia-smi
# 看右上角 "CUDA Version: xx.x"
```

**步骤4: 安装对应版本的 PaddlePaddle GPU**

参阅上文的安装命令，根据你的 CUDA 版本选择合适的 PaddlePaddle GPU 版本进行安装。

**步骤5: 验证安装**

```bash
python -c "import paddle; print('GPU:', paddle.device.is_compiled_with_cuda())"
# 输出 "GPU: True" 表示成功
```

### Q3: 处理速度慢？

- 使用 GPU 加速
- PaddleOCR 首次运行会下载模型，后续会使用缓存
- 使用智能采样模式或适当增加采样间隔
- 考虑降低视频分辨率

### Q4: 识别准确率不高？

- 确保视频清晰度足够
- 复杂的手机号字体可能影响识别
- 复杂背景可能影响 OCR 效果

### Q5: API 任务一直处于 pending 状态？

- 检查服务器日志
- 确认视频文件格式正确
- 确认 PaddleOCR 模型已下载

### Q6: API 端口被占用？

修改 `api_server.py` 中的端口号，或停止占用 8000 端口的进程。

## 测试

### 测试手机号检测模块

```bash
cd src
python phone_detector.py
```

### 测试 OCR 检测模块

```bash
cd src
python ocr_detector.py
```

## 注意事项

1. **首次运行**: PaddleOCR 会自动下载模型文件，需要网络连接
2. **输出格式**: 当前仅支持 MP4 格式输出
3. **处理时长**: 取决于视频长度、分辨率和是否使用 GPU
4. **API 服务器**: 重启服务器会丢失处理中的任务（已完成的任务会持久化）
5. **文件管理**: 上传和输出的视频会保存在服务器上，建议定期清理
6. **生产环境**: 建议使用反向代理（如 Nginx）并配置 HTTPS

## 许可证

本项目采用 MIT 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 致谢

- [OpenCV](https://opencv.org/) - 强大的计算机视觉库
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - 优秀的 OCR 工具
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Web 框架
