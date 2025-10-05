# 视频手机号脱敏工具 (VideoPhoneMask)

基于 PaddleOCR 的视频手机号自动识别与脱敏工具，可精确定位并打码视频中的中国大陆手机号。

## 功能特性

- **精确识别**: 使用 PaddleOCR 精确识别中国大陆 11 位手机号
- **智能过滤**: 过滤误识别的长数字串和编号，只保留真实手机号
- **精确定位**: 基于 OCR 返回的文本框坐标进行像素级精确打码
- **多种打码方式**: 支持高斯模糊、像素化、黑色遮挡三种打码效果
- **适应性强**: 支持不同分辨率、帧率、字体、颜色的视频
- **GPU 加速**: 可选 GPU 加速提升处理速度
- **实时进度**: 显示处理进度和统计信息

## 技术方案

### 核心技术栈

- **PaddleOCR**: 文本检测和识别（支持返回精确坐标）
- **OpenCV**: 视频处理和打码效果实现

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

## 使用方法

### 基本使用

#### 智能采样模式（推荐，速度最快）

```bash
cd src

# 1秒采样一次，速度提升 10-30 倍（默认）
python main_smart.py input.mp4 output.mp4

# 效率更高的采样（2秒一次）
python main_smart.py input.mp4 output.mp4 --sample-interval 2.0

# 配置缓冲时间防止泄露
python main_smart.py input.mp4 output.mp4 --buffer-time 0.5

# 配合 GPU 使用
python main_smart.py input.mp4 output.mp4 --use-gpu
```

#### 默认模式（逐帧处理，最准确）

```bash
cd src
python main.py input.mp4 output.mp4
```

### 高级选项

#### 1. 选择打码方式

```bash
# 高斯模糊（默认，效果自然）
python main.py input.mp4 output.mp4 --blur-method gaussian

# 像素化（马赛克效果）
python main.py input.mp4 output.mp4 --blur-method pixelate

# 黑色遮挡（完全遮挡，适合高安全要求场景）
python main.py input.mp4 output.mp4 --blur-method black
```

#### 2. 调整模糊强度

```bash
# 模糊强度（仅对高斯模糊有效，必须为奇数，越大越模糊）
python main.py input.mp4 output.mp4 --blur-strength 71
```

#### 3. 使用 GPU 加速

```bash
# 需要安装 paddlepaddle-gpu
python main.py input.mp4 output.mp4 --use-gpu
```

### 完整示例

```bash
# 使用像素化打码 + GPU 加速
python main.py video/test.mp4 video/test_masked.mp4 --blur-method pixelate --use-gpu
```

## 命令行参数

```
位置参数:
  input                 输入视频文件路径
  output                输出视频文件路径

可选参数:
  -h, --help            显示帮助信息
  --blur-method {gaussian,pixelate,black}
                        打码方式 [默认: gaussian]
  --blur-strength BLUR_STRENGTH
                        模糊强度（高斯模糊核大小，必须为奇数）[默认: 51]
  --use-gpu             使用GPU加速OCR识别
```

## 项目结构

```
VideoPhoneMask/
├── src/              # Python 源代码
│   ├── main.py             # 主程序入口
│   ├── video_processor.py  # 视频处理模块
│   ├── ocr_detector.py     # OCR 检测模块
│   └── phone_detector.py   # 手机号识别模块
├── requirements.txt         # Python 依赖
└── README.md               # 项目说明文档
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

1. **GPU 加速**: 如有 NVIDIA GPU，建议使用 `--use-gpu` 选项
2. **分辨率优化**: 超高分辨率视频建议先降低分辨率再处理
3. **合理设置采样间隔**: 根据视频内容动态调整采样间隔，平衡速度和准确率

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

1. 访问 [NVIDIA CUDA 下载页面](https://developer.nvidia.com/cuda-downloads)
2. 选择操作系统和版本
3. 下载并安装

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

- 使用 GPU 加速 (`--use-gpu`)
- PaddleOCR 首次运行会下载模型，后续会使用缓存
- 减少视频帧率或适当增加采样间隔
- 考虑降低视频分辨率

### Q4: 识别准确率不高？

- 确保视频清晰度足够
- 复杂的手机号字体可能影响识别
- 复杂背景可能影响 OCR 效果

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

## 许可证

本项目采用 MIT 许可证，详情请参阅 LICENSE 文件。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 致谢

- [OpenCV](https://opencv.org/) - 强大的计算机视觉库
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - 优秀的 OCR 工具
