# 视频手机号脱敏 API 使用指南

## 快速开始

### 1. 安装依赖

```bash
# 安装所有依赖（包括API依赖）
pip install -r requirements.txt
```

### 2. 启动API服务器

```bash
cd src
python api_server.py
```

服务器启动后，访问：
- **API服务地址**: http://localhost:8000
- **交互式API文档**: http://localhost:8000/docs
- **API文档（备用）**: http://localhost:8000/redoc

## API接口说明

### 1. 上传视频并创建任务

**接口**: `POST /api/tasks`

**功能**: 上传视频文件，创建脱敏处理任务，返回任务ID

**请求参数**（multipart/form-data）:
- `file` (必需): 视频文件
- `blur_method` (可选): 打码方式，默认 `gaussian`
  - `gaussian`: 高斯模糊（自然效果）
  - `pixelate`: 像素化（马赛克效果）
  - `black`: 黑色遮挡（完全遮挡）
- `blur_strength` (可选): 模糊强度，默认 `51`（必须为奇数）
- `use_gpu` (可选): 是否使用GPU，默认 `false`
- `sample_interval` (可选): 采样间隔（秒），默认 `1.0`
- `buffer_time` (可选): 缓冲时间（秒），默认等于 `sample_interval`

**请求示例（curl）**:
```bash
curl -X POST "http://localhost:8000/api/tasks" \
  -F "file=@test.mp4" \
  -F "blur_method=gaussian" \
  -F "use_gpu=false" \
  -F "sample_interval=1.0"
```

**请求示例（Python）**:
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

**响应示例**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "任务创建成功，已加入处理队列"
}
```

### 2. 查询任务进度

**接口**: `GET /api/tasks/{task_id}`

**功能**: 根据任务ID查询处理进度

**请求示例（curl）**:
```bash
curl "http://localhost:8000/api/tasks/550e8400-e29b-41d4-a716-446655440000"
```

**请求示例（Python）**:
```python
import requests

task_id = "550e8400-e29b-41d4-a716-446655440000"
url = f"http://localhost:8000/api/tasks/{task_id}"

response = requests.get(url)
status = response.json()
print(f"状态: {status['status']}")
print(f"进度: {status['progress']}%")
print(f"消息: {status['message']}")
```

**响应示例（处理中）**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 45.5,
  "message": "正在处理视频...",
  "created_at": "2025-10-05T10:30:00",
  "started_at": "2025-10-05T10:30:05",
  "completed_at": null,
  "error": null,
  "result": null
}
```

**响应示例（完成）**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "message": "处理完成",
  "created_at": "2025-10-05T10:30:00",
  "started_at": "2025-10-05T10:30:05",
  "completed_at": "2025-10-05T10:35:20",
  "error": null,
  "result": {
    "total_frames": 1500,
    "processed_frames": 1500,
    "ocr_calls": 30,
    "frames_with_phones": 450,
    "total_phones_detected": 450,
    "unique_phones": ["13812345678"]
  }
}
```

**任务状态说明**:
- `pending`: 等待处理
- `processing`: 处理中
- `completed`: 已完成
- `failed`: 失败

### 3. 下载处理后的视频

**接口**: `GET /api/tasks/{task_id}/download`

**功能**: 下载已完成的脱敏视频

**请求示例（curl）**:
```bash
curl -O -J "http://localhost:8000/api/tasks/550e8400-e29b-41d4-a716-446655440000/download"
```

**请求示例（Python）**:
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

### 4. 获取所有任务列表

**接口**: `GET /api/tasks`

**功能**: 获取所有任务列表，支持按状态过滤

**请求参数**:
- `status` (可选): 按状态过滤 (`pending`/`processing`/`completed`/`failed`)
- `limit` (可选): 返回的最大任务数，默认100

**请求示例（curl）**:
```bash
# 获取所有已完成的任务
curl "http://localhost:8000/api/tasks?status=completed&limit=10"
```

**请求示例（Python）**:
```python
import requests

url = "http://localhost:8000/api/tasks"
params = {"status": "completed", "limit": 10}

response = requests.get(url, params=params)
tasks = response.json()
print(f"总任务数: {tasks['total']}")
for task in tasks['tasks']:
    print(f"- {task['task_id']}: {task['status']}")
```

**响应示例**:
```json
{
  "total": 2,
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "progress": 100,
      "message": "处理完成",
      "created_at": "2025-10-05T10:30:00",
      "started_at": "2025-10-05T10:30:05",
      "completed_at": "2025-10-05T10:35:20",
      "error": null,
      "result": {...}
    }
  ]
}
```

### 5. 删除任务

**接口**: `DELETE /api/tasks/{task_id}`

**功能**: 删除已完成或失败的任务及其关联文件

**请求示例（curl）**:
```bash
curl -X DELETE "http://localhost:8000/api/tasks/550e8400-e29b-41d4-a716-446655440000"
```

**请求示例（Python）**:
```python
import requests

task_id = "550e8400-e29b-41d4-a716-446655440000"
url = f"http://localhost:8000/api/tasks/{task_id}"

response = requests.delete(url)
print(response.json()["message"])
```

## 完整工作流示例

### Python 完整示例

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
```

### JavaScript/Node.js 示例

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const API_BASE = 'http://localhost:8000';

async function processVideo() {
  // 1. 上传视频
  const form = new FormData();
  form.append('file', fs.createReadStream('test.mp4'));
  form.append('blur_method', 'gaussian');
  form.append('use_gpu', 'false');
  form.append('sample_interval', '1.0');

  const uploadResponse = await axios.post(`${API_BASE}/api/tasks`, form, {
    headers: form.getHeaders()
  });
  const taskId = uploadResponse.data.task_id;
  console.log(`任务ID: ${taskId}`);

  // 2. 轮询查询进度
  while (true) {
    const statusResponse = await axios.get(`${API_BASE}/api/tasks/${taskId}`);
    const status = statusResponse.data;

    console.log(`状态: ${status.status}, 进度: ${status.progress}%`);

    if (status.status === 'completed') {
      console.log('处理完成！');
      break;
    } else if (status.status === 'failed') {
      console.log(`处理失败: ${status.error}`);
      return;
    }

    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  // 3. 下载结果
  const downloadResponse = await axios.get(
    `${API_BASE}/api/tasks/${taskId}/download`,
    { responseType: 'stream' }
  );
  downloadResponse.data.pipe(fs.createWriteStream('output_masked.mp4'));
  console.log('下载完成: output_masked.mp4');
}

processVideo();
```

## CORS 配置

API 服务器已配置 CORS，允许所有来源的跨域请求。生产环境建议修改 `src/api_server.py` 中的 `allow_origins` 配置：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 指定允许的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 配置说明

### 服务器配置

默认配置：
- **主机**: `0.0.0.0`（允许外部访问）
- **端口**: `8000`
- **工作线程数**: 2（可在 `task_queue.py` 中修改）

修改端口：
```python
# 在 api_server.py 的 main 函数中
uvicorn.run(
    "api_server:app",
    host="0.0.0.0",
    port=8080,  # 修改为其他端口
    reload=False
)
```

### 存储配置

默认存储目录：
- **上传文件**: `./uploads/`
- **输出文件**: `./outputs/`
- **任务数据**: `./tasks/tasks.json`

可在 `api_server.py` 中修改：
```python
UPLOAD_DIR = Path("/path/to/uploads")
OUTPUT_DIR = Path("/path/to/outputs")
```

## 性能建议

1. **GPU 加速**: 如果有NVIDIA GPU，设置 `use_gpu=true` 可大幅提升速度
2. **采样间隔**:
   - 静态视频：可设置为 `2.0` 秒
   - 动态视频：建议设置为 `0.5-1.0` 秒
3. **并发处理**: 修改 `TaskQueue` 的 `max_workers` 参数增加并发数

## 故障排查

### 1. 端口被占用

```
Error: [Errno 98] Address already in use
```

**解决方法**: 修改 `api_server.py` 中的端口号，或停止占用8000端口的进程

### 2. 任务一直处于 pending 状态

**原因**: 工作线程未启动或处理失败

**解决方法**:
- 检查服务器日志
- 确认视频文件格式正确
- 确认PaddleOCR模型已下载

### 3. 下载失败

**原因**: 任务尚未完成或输出文件被删除

**解决方法**: 先查询任务状态，确认为 `completed` 后再下载

## 注意事项

1. API服务器在内存中维护任务队列，重启服务器会丢失处理中的任务（已完成的任务会持久化）
2. 上传的视频和处理后的视频会保存在服务器上，建议定期清理
3. 大文件上传可能需要调整服务器的最大请求大小限制
4. 生产环境建议使用反向代理（如Nginx）并配置HTTPS

## 许可证

本项目采用 MIT 许可证
