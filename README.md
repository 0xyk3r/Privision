# Privision - Video Content Privacy Masking Tool

> [中文文档](README_zh.md) | English

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

> **Universal Video Content Privacy Solution** - Intelligent Information Recognition and Masking System Based on OCR

Privision is a powerful video content privacy masking tool that uses advanced OCR technology to automatically identify and mask sensitive information in videos. It supports multiple detection modes including **phone numbers, ID card numbers, and custom keywords**, and provides three usage methods: command-line interface, batch processing, and RESTful API.

## 🌟 Key Features

### 🎯 Multi-Scenario Detection Support

- **📱 Phone Number Detection**: Accurately identifies 11-digit Chinese mainland phone numbers with smart false-positive filtering
- **🆔 ID Card Number Detection**: Recognizes 18-digit Chinese mainland ID card numbers with basic validity verification
- **🔑 Keyword Detection**: Custom keyword lists for flexible detection of any sensitive terms
- **🔌 Extensible Architecture**: Factory pattern design for easy addition of new detector types

### ⚡ High-Performance Processing

- **🚀 Dual Processing Modes**:
  - **Frame-by-Frame Mode**: Precise recognition for high-accuracy scenarios
  - **Smart Sampling Mode**: 10-30x speed improvement for most scenarios
- **💎 GPU Acceleration**: CUDA support for significantly improved processing speed
- **🎯 Precise Positioning**: Iterative optimization algorithm ensuring only target content is masked, avoiding false positives

### 🎨 Flexible Masking Methods

- **Gaussian Blur**: Natural and smooth blur effect
- **Pixelate**: Classic mosaic effect
- **Black Mask**: Complete coverage for strong protection

### 🛠 Multiple Usage Methods

- **Command-Line Tool**: Simple and easy to use for single video processing
- **Batch Processing**: Directory-level batch processing with recursive subdirectory support
- **RESTful API**: Complete HTTP API with asynchronous task queue
- **Visual Debugging**: Real-time preview of detection results and masking effects

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage Guide](#-usage-guide)
  - [Command-Line Tool](#1-command-line-tool)
  - [Batch Processing](#2-batch-processing)
  - [API Service](#3-api-service)
- [Detector Documentation](#-detector-documentation)
- [Project Architecture](#-project-architecture)
- [Performance Optimization](#-performance-optimization)
- [FAQ](#-faq)

## ⚡ Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/0xyk3r/Privision.git
cd Privision

# Install in development mode (recommended)
pip install -e .
```

### Basic Usage

```bash
# 1. Detect and mask phone numbers
privision input.mp4 output.mp4

# 2. Detect ID card numbers
privision input.mp4 output.mp4 --detector idcard

# 3. Detect custom keywords
privision input.mp4 output.mp4 --detector keyword --keywords password account name

# 4. Smart sampling mode (fast)
privision input.mp4 output.mp4 --mode smart

# 5. GPU acceleration
privision input.mp4 output.mp4 --device gpu:0 --mode smart
```

## 🚀 Installation

### System Requirements

- Python 3.8+
- pip
- (Optional) NVIDIA GPU + CUDA Toolkit

### Installation Steps

#### Method 1: Development Mode Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/0xyk3r/Privision.git
cd Privision

# Install project (development mode)
pip install -e .

# Verify installation
privision --help
```

After installation, you can directly use the following commands:
- `privision` - Single video processing
- `privision-batch` - Batch processing
- `privision-server` - API server

#### Method 2: Install Dependencies Only

```bash
cd Privision
pip install -r requirements.txt
```

> With this method, run the program using `python -m src.main`

### GPU Acceleration Installation

**Check CUDA Version**:
```bash
nvidia-smi  # Check "CUDA Version: xx.x" in the upper right corner
```

**Install GPU Dependencies**:

```bash
# Install common dependencies first
pip install -r requirements.txt

# Choose installation based on CUDA version
# CUDA 11.8
python -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/

# CUDA 12.6
python -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/

# CUDA 12.9
python -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu129/
```

**Verify GPU Installation**:
```bash
python -c "import paddle; print('GPU available:', paddle.device.is_compiled_with_cuda())"
```

### Core Dependencies

- `paddlepaddle` >= 3.0.0 - Deep learning framework
- `paddleocr` >= 3.0.0 - OCR recognition engine
- `opencv-python` >= 4.8.0 - Video processing
- `numpy` >= 1.24.0 - Numerical computing
- `fastapi` >= 0.104.0 - API framework
- `rich` >= 13.0.0 - Terminal beautification

## 📖 Usage Guide

### 1. Command-Line Tool

#### Basic Usage

```bash
# Detect phone numbers (default)
privision input.mp4 output.mp4

# Detect ID card numbers
privision input.mp4 output.mp4 --detector idcard

# Detect custom keywords
privision input.mp4 output.mp4 --detector keyword --keywords password account username

# Smart sampling mode (recommended)
privision input.mp4 output.mp4 --mode smart

# GPU acceleration
privision input.mp4 output.mp4 --device gpu:0
```

#### Advanced Options

**Choose Masking Method**:
```bash
# Gaussian blur (default)
privision input.mp4 output.mp4 --blur-method gaussian

# Pixelate (mosaic)
privision input.mp4 output.mp4 --blur-method pixelate

# Black mask
privision input.mp4 output.mp4 --blur-method black
```

**Precise Location Mode**:
```bash
# Enable precise location to avoid masking irrelevant content
privision input.mp4 output.mp4 --precise-location
```

**Visual Debugging**:
```bash
# Show real-time processing window
privision input.mp4 output.mp4 --visualize
```

#### Complete Parameters

```
Positional Arguments:
  input                         Input video file path
  output                        Output video file path

Detector Settings:
  --detector {phone,keyword,idcard}
                                Detector type [default: phone]
                                  phone   - Phone number detection
                                  keyword - Keyword detection
                                  idcard  - ID card number detection

  --keywords WORD [WORD ...]    Keyword list (keyword detector only)
  --case-sensitive              Keywords are case-sensitive (keyword detector only)

Processing Mode:
  --mode {frame-by-frame,smart}
                                Processing mode [default: frame-by-frame]
                                  frame-by-frame - Frame-by-frame processing
                                  smart          - Smart sampling

Masking Settings:
  --blur-method {gaussian,pixelate,black}
                                Masking method [default: gaussian]
  --blur-strength INT           Blur strength (must be odd) [default: 51]

Device Settings:
  --device DEVICE               Computing device (cpu, gpu:0, gpu:1, ...) [default: cpu]

Sampling Settings (smart mode only):
  --sample-interval FLOAT       Sampling interval (seconds) [default: 1.0]
  --buffer-time FLOAT           Buffer time (seconds)

Precise Location:
  --precise-location            Enable precise location mode
  --precise-max-iterations INT  Maximum iterations [default: 3]

Interface Settings:
  --visualize                   Enable visualization window
  --no-rich                     Disable Rich UI

Other:
  -h, --help                    Show help message
```

### 2. Batch Processing

Use the `privision-batch` command to batch process all videos in a directory.

#### Basic Usage

```bash
# Batch process directory
privision-batch input_dir/ output_dir/

# Process subdirectories recursively
privision-batch input_dir/ output_dir/ --recursive

# Use ID card detector for batch processing
privision-batch input_dir/ output_dir/ --detector idcard

# Smart mode + GPU acceleration
privision-batch input_dir/ output_dir/ --mode smart --device gpu:0
```

#### Parameters

```
Positional Arguments:
  input_dir                     Input video directory
  output_dir                    Output video directory

Detector Settings:
  --detector {phone,keyword,idcard}
                                Detector type [default: phone]
  --keywords WORD [WORD ...]    Keyword list (keyword detector only)
  --case-sensitive              Keywords are case-sensitive

Optional Arguments:
  --blur-method {gaussian,pixelate,black}
                                Masking method [default: gaussian]
  --device DEVICE               Computing device [default: cpu]
  --mode {frame-by-frame,smart}
                                Processing mode [default: frame-by-frame]
  --recursive                   Process subdirectories recursively
  --output-suffix SUFFIX        Output file suffix [default: _masked]
```

Supported video formats: `.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`, `.webm`

### 3. API Service

Use `privision-server` to start the FastAPI server, providing RESTful API endpoints.

#### Start Server

```bash
# Start with default configuration
privision-server

# Custom port
privision-server --port 9000

# Custom data directory
privision-server --data-dir /path/to/data
```

After server starts:
- API Service: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- API Documentation: http://localhost:8000/redoc

#### API Endpoints

**1. Create Task**

`POST /api/tasks`

```bash
curl -X POST "http://localhost:8000/api/tasks" \
  -F "file=@test.mp4" \
  -F "detector_type=phone" \
  -F "blur_method=gaussian" \
  -F "device=cpu"
```

Supported parameters:
- `file`: Video file to process (required)
- `detector_type`: Detector type (phone/keyword/idcard)
- `keywords`: Keyword list (keyword detector only)
- `case_sensitive`: Case-sensitive (keyword detector only)
- `blur_method`: Masking method (gaussian/pixelate/black)
- `blur_strength`: Blur strength (Gaussian blur only, odd number, default 51)
- `device`: Computing device (cpu, gpu:0, gpu:1, etc.)
- `sample_interval`: Sampling interval (seconds)
- `buffer_time`: Buffer time (seconds)
- `precise_location`: Enable precise location
- `precise_max_iterations`: Maximum iterations for precise location (default 3)

Response:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Task created successfully"
}
```

**2. Query Task Progress**

`GET /api/tasks/{task_id}`

```bash
curl "http://localhost:8000/api/tasks/{task_id}"
```

**3. Download Result**

`GET /api/tasks/{task_id}/download`

```bash
curl -O -J "http://localhost:8000/api/tasks/{task_id}/download"
```

**4. Get Task List**

`GET /api/tasks?status={status}&limit={limit}`

Supported parameters:
- `status` (optional): Filter by status (pending/processing/completed/failed)
- `limit` (optional): Maximum number of tasks to return, default 100

**5. Delete Task**

`DELETE /api/tasks/{task_id}`

#### Python Client Example

```python
import requests
import time

API_BASE = "http://localhost:8000"

# 1. Upload video
with open("test.mp4", "rb") as f:
    files = {"file": f}
    data = {
        "detector_type": "phone",
        "blur_method": "gaussian",
        "device": "cpu"
    }
    response = requests.post(f"{API_BASE}/api/tasks", files=files, data=data)
    task_id = response.json()["task_id"]

# 2. Poll for progress
while True:
    response = requests.get(f"{API_BASE}/api/tasks/{task_id}")
    status = response.json()

    if status['status'] == 'completed':
        break
    time.sleep(2)

# 3. Download result
response = requests.get(f"{API_BASE}/api/tasks/{task_id}/download")
with open("output.mp4", "wb") as f:
    f.write(response.content)
```

## 🎯 Detector Documentation

### 1. Phone Number Detector (phone)

**Function**: Identifies 11-digit Chinese mainland phone numbers

**Features**:
- Regex matching: `1[3-9]\d{9}`
- Smart filtering of long digit strings and false positives
- Context validation to avoid misidentification

**Usage**:
```bash
privision input.mp4 output.mp4 --detector phone
```

### 2. ID Card Number Detector (idcard)

**Function**: Identifies 18-digit Chinese mainland ID card numbers

**Features**:
- Regex matching: `\d{17}[\dXx]`
- Date validity verification
- Excludes invalid numbers

**Usage**:
```bash
privision input.mp4 output.mp4 --detector idcard
```

### 3. Keyword Detector (keyword)

**Function**: Detects custom keywords

**Features**:
- Custom keyword list support
- Chinese and English mixed support
- Optional case sensitivity
- Smart boundary matching

**Usage**:
```bash
# Default keywords (password, account, username, etc.)
privision input.mp4 output.mp4 --detector keyword

# Custom keywords
privision input.mp4 output.mp4 --detector keyword --keywords name phone address

# Case-sensitive
privision input.mp4 output.mp4 --detector keyword --keywords Password --case-sensitive
```

### Extending Custom Detectors

The project uses factory pattern design for easy extension of new detectors:

1. Inherit from `BaseDetector` base class
2. Implement required abstract methods
3. Register in `DetectorFactory`

See `src/core/detector_base.py` and `src/core/detector_factory.py` for details

## 🏗 Project Architecture

### Directory Structure

```
Privision/
├── src/                          # Source code
│   ├── main.py                   # CLI entry point
│   ├── batch.py                  # Batch processing entry
│   ├── server.py                 # API server entry
│   │
│   ├── core/                     # Core functionality
│   │   ├── video_processor.py   # Video processor (frame-by-frame/smart)
│   │   ├── ocr_detector.py      # OCR detection
│   │   ├── detector_base.py     # Detector base class
│   │   ├── detector_factory.py  # Detector factory
│   │   ├── detectors/           # Detector implementations
│   │   │   ├── phone_detector.py
│   │   │   ├── idcard_detector.py
│   │   │   └── keyword_detector.py
│   │   ├── precise_locator.py   # Precise location
│   │   ├── blur.py              # Masking effects
│   │   └── bbox_calculator.py   # Bounding box calculation
│   │
│   ├── api/                      # API service
│   │   └── task_queue.py        # Task queue management
│   │
│   ├── ui/                       # User interface
│   │   ├── rich_ui.py           # Rich terminal UI
│   │   ├── progress.py          # Progress callback interface
│   │   └── visualizer.py        # Visualization window
│   │
│   ├── config/                   # Configuration management
│   │   └── args.py              # Argument parsing
│   │
│   └── test/                     # Test modules
│
├── pyproject.toml                # Project configuration
├── requirements.txt              # Dependency list
├── README.md                     # This document
```

### Core Modules

#### Detector Architecture

```
BaseDetector (Abstract Base Class)
    ├── PhoneDetector (Phone numbers)
    ├── IDCardDetector (ID card numbers)
    └── KeywordDetector (Keywords)

DetectorFactory (Factory)
    └── create_detector()
```

#### Processing Flow

**Frame-by-Frame Mode**:
```
Video Input → Frame-by-Frame Read → OCR → Detector → Precise Location (optional) → Mask → Output
```

**Smart Sampling Mode**:
```
Video Input → Periodic Sampling → OCR → Detector → Record Areas → Batch Mask → Output
```

### Technology Stack

- **PaddleOCR**: Text detection and recognition
- **OpenCV**: Video processing and masking
- **FastAPI**: RESTful API framework
- **Rich**: Terminal beautification
- **NumPy**: Numerical computing

## 🚀 Performance Optimization

### Recommended Configuration

**1. Use GPU Acceleration**
```bash
privision input.mp4 output.mp4 --device gpu:0
```
GPU can improve OCR speed by 3-10x

**2. Use Smart Sampling Mode**
```bash
privision input.mp4 output.mp4 --mode smart
```
Speed improvement of 10-30x, suitable for most scenarios

**3. Adjust Sampling Interval**
```bash
# Static scenes (phone number position changes slowly)
privision input.mp4 output.mp4 --mode smart --sample-interval 2.0

# Dynamic scenes (phone number position changes quickly)
privision input.mp4 output.mp4 --mode smart --sample-interval 0.5
```

**4. Video Preprocessing**
- Ultra-high resolution videos should be downscaled first
- Use H.264 encoding for faster processing

**5. API Concurrent Processing**

Modify the `max_workers` parameter in `src/api/task_queue.py`:
```python
get_task_queue(storage_dir=TASKS_DIR, max_workers=2)  # Increase concurrency
```

## 🔧 FAQ

### Q1: How to verify GPU availability?

```bash
# Check CUDA
nvidia-smi

# Check PaddlePaddle GPU support
python -c "import paddle; print('GPU available:', paddle.device.is_compiled_with_cuda())"
```

### Q2: Why can't I directly run `python src/main.py`?

Because import statements use the `src.xxx` format, Python needs to import `src` as a package.

**Solutions**:
- Run using `python -m src.main`
- Or install using `pip install -e .` and directly use the `privision` command

### Q3: Why is the first run slow?

The first run automatically downloads PaddleOCR model files (about 100-200 MB), requiring network connection. After downloading, files are cached locally.

### Q4: How to improve recognition accuracy?

1. Ensure video clarity is sufficient
2. Use frame-by-frame mode instead of smart sampling
3. Enable precise location mode: `--precise-location`
4. Complex fonts or backgrounds affect OCR performance

### Q5: How to add new detectors?

1. Create a new detector class in `src/core/detectors/`
2. Inherit from `BaseDetector` and implement required methods
3. Register in `DetectorFactory._detectors`
4. Update command-line arguments and documentation

### Q6: What video formats are supported?

Supports all formats supported by OpenCV: `.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`, `.webm`

Output format currently only supports MP4.

### Q7: How to deploy API service in production?

1. Use reverse proxy (such as Nginx)
2. Configure HTTPS
3. Modify CORS settings (in `src/server.py`)
4. Use process management tools (such as systemd, supervisor)
5. Configure logging and monitoring

## 🛠 Development Guide

### Development Environment Setup

```bash
# Clone repository
git clone https://github.com/0xyk3r/Privision.git
cd Privision

# Install development dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest src/test/

# Run specific tests
python -m src.test.test_phone_filter
python -m src.test.test_ocr_and_detector
```

### Code Structure Design

- **Separation of Concerns**: Core functionality, API, UI, and configuration are independently modularized
- **Configuration-Driven**: Use `ProcessConfig` for unified configuration management
- **Interface Abstraction**: `ProgressCallback` interface decouples business logic from UI
- **Factory Pattern**: `DetectorFactory` manages detector creation
- **Extensibility**: Easy to add new detectors, masking methods, and UIs

### Contributing

Issues and Pull Requests are welcome!

1. Fork the project
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Commit changes (`git commit -m 'Add some YourFeature'`)
4. Push to branch (`git push origin feature/YourFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - OCR toolkit
- [OpenCV](https://opencv.org/) - Computer vision library
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Rich](https://github.com/Textualize/rich) - Terminal beautification library

## 📧 Contact

- Author: 0xyk3r
- GitHub: [https://github.com/0xyk3r/Privision](https://github.com/0xyk3r/Privision)
- Issues: [https://github.com/0xyk3r/Privision/issues](https://github.com/0xyk3r/Privision/issues)

---

**Note**: This tool is only for legal privacy protection purposes and should not be used for illegal purposes. Users are responsible for any legal liability related to videos processed with this tool.
