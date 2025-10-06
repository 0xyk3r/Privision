# 安装与使用指南

## 1. 安装项目

### 开发模式安装（推荐）

在项目根目录下运行：

```bash
# 安装项目为可编辑模式
pip install -e .
```

这会将项目安装到你的Python环境中，之后你可以：
- 使用命令行工具直接运行
- 在任何地方导入 `src` 包
- 修改代码后无需重新安装

### 生产模式安装

```bash
pip install .
```

## 2. 使用方法

### 方法 1: 使用命令行工具（推荐）

安装后，你可以直接使用以下命令：

```bash
# 处理单个视频
videophone-mask input.mp4 output.mp4

# 批量处理
videophone-batch input_dir/ output_dir/

# 启动API服务器
videophone-server
```

### 方法 2: 使用 Python 模块

```bash
# 处理单个视频
python -m src.main input.mp4 output.mp4

# 批量处理
python -m src.batch input_dir/ output_dir/

# 启动API服务器
python -m src.server
```

### 方法 3: 直接运行脚本（兼容旧方式）

```bash
# 需要确保在项目根目录
python src/main.py input.mp4 output.mp4
python src/batch.py input_dir/ output_dir/
python src/server.py
```

## 3. 验证安装

```bash
# 检查是否安装成功
pip show videophone-mask

# 测试命令行工具
videophone-mask --help
```

## 4. 包结构说明

```
VideoPhoneMask/
├── pyproject.toml          # 项目配置文件
├── requirements.txt        # 依赖列表
├── README.md              # 项目说明
├── INSTALL.md             # 安装指南（本文件）
└── src/                   # 源代码包
    ├── __init__.py        # 包初始化
    ├── main.py            # CLI入口
    ├── server.py          # API服务器
    ├── batch.py           # 批量处理
    ├── api/               # API模块
    ├── config/            # 配置模块
    ├── core/              # 核心处理模块
    ├── ui/                # UI模块
    └── test/              # 测试模块
```

## 5. 导入方式说明

### 在包内部
使用绝对导入：
```python
from src.config import ProcessConfig
from src.core import VideoProcessor
```

### 在外部使用
```python
from src.config import ProcessConfig
from src.core import VideoProcessor
```

## 6. 常见问题

### Q: 为什么要使用 `pip install -e .`？
A: 开发模式安装会创建一个链接到你的源代码，这样你可以修改代码而无需重新安装。

### Q: 我可以在虚拟环境中安装吗？
A: 强烈推荐！先创建虚拟环境：
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -e .
```

### Q: 如何更新依赖？
A: 编辑 `pyproject.toml` 中的 `dependencies` 部分，然后运行：
```bash
pip install -e .
```

## 7. 开发工具

安装开发依赖：
```bash
pip install -e ".[dev]"
```

这会安装额外的开发工具，如 pytest、black、flake8 等。
