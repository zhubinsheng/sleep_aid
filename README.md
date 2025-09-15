# ESP32 睡眠音乐系统

一个基于 WebSocket 的实时音频流传输系统，支持 Opus 编码压缩，专为 ESP32 等嵌入式设备设计。

## 功能特性

- 🎵 **实时音频流传输**：基于 WebSocket 的低延迟音频传输
- 🗜️ **高效压缩**：使用 Opus 编码，压缩率达到 93%+
- 🔊 **边播边录**：客户端支持实时播放和录制
- 📊 **性能监控**：实时显示压缩率和传输统计
- 🔄 **循环播放**：服务器自动循环播放音频文件
- ⚡ **低延迟**：60ms 帧时长，适合实时应用

## 系统要求

### Python 环境
- Python 3.8+
- pip 包管理器

### 系统依赖库

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install portaudio19-dev libopus-dev python3-dev
```

#### CentOS/RHEL
```bash
sudo yum install portaudio-devel opus-devel python3-devel
```

#### macOS
```bash
brew install portaudio opus
```

#### Windows
- 安装 [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- 下载并安装 [PortAudio](http://www.portaudio.com/download.html)
- 下载并安装 [Opus](https://opus-codec.org/downloads/)

## 安装步骤

### 1. 克隆项目
```bash
git clone <repository-url>
cd sleep_aid
```

### 2. 创建虚拟环境（推荐）
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows
```

### 3. 安装 Python 依赖
```bash
pip install -r requirements.txt
```

### 4. 准备音频文件
将你的音频文件重命名为 `sleep.wav` 并放在项目根目录下。

## 使用方法

### 启动服务器
```bash
python3 sleep_music_server.py
```

服务器将在 `ws://localhost:8765` 上启动，开始循环播放 `sleep.wav` 文件。

### 启动客户端
```bash
python3 sleep_music_client.py
```

客户端将连接到服务器，开始接收和播放音频，同时录制到 `recorded_audio.wav` 文件。

## 配置参数

### 音频配置
- **采样率**：24kHz（CD 质量）
- **声道数**：2（立体声）
- **帧时长**：60ms
- **编码复杂度**：0（最低延迟）

### 压缩性能
- **压缩比**：约 15:1
- **压缩率**：约 93%
- **比特率**：动态调整

## 项目结构

```
sleep_aid/
├── sleep_music_server.py    # WebSocket 音频服务器
├── sleep_music_client.py    # 音频客户端（播放+录制）
├── sleep.wav               # 音频源文件
├── recorded_audio.wav      # 录制输出文件
├── requirements.txt        # Python 依赖
└── README.md              # 项目说明
```

## 技术架构

### 服务器端 (sleep_music_server.py)
- 使用 `pydub` 加载和处理音频文件
- 使用 `opuslib_next` 进行 Opus 编码
- 通过 WebSocket 实时传输编码后的音频帧
- 支持多客户端连接

### 客户端 (sleep_music_client.py)
- 接收 WebSocket 音频流
- 使用 `opuslib_next` 解码 Opus 数据
- 使用 `pyaudio` 实时播放音频
- 同时录制音频到 WAV 文件

## 故障排除

### 常见问题

#### 1. PyAudio 安装失败
```bash
# Ubuntu/Debian
sudo apt install portaudio19-dev python3-dev

# 然后重新安装
pip install pyaudio
```

#### 2. Opus 编码器初始化失败
```bash
# Ubuntu/Debian
sudo apt install libopus-dev

# 然后重新安装
pip install opuslib_next
```

#### 3. 音频播放无声音
- 检查系统音频设备是否正常
- 确认音频文件格式正确（WAV 格式）
- 检查采样率和声道数配置

#### 4. 连接失败
- 确认服务器已启动
- 检查端口 8765 是否被占用
- 确认防火墙设置

## 性能优化

### 服务器优化
- 调整 `FRAME_DURATION_MS` 减少延迟
- 修改 `OPUS_COMPLEXITY` 平衡音质和性能
- 使用 SSD 存储音频文件

### 客户端优化
- 调整播放缓冲区大小
- 优化音频设备配置
- 使用高性能音频接口

## 扩展功能

### 可能的改进方向
- 支持多种音频格式（MP3、FLAC 等）
- 添加音频均衡器和音效处理
- 实现多房间音频同步
- 添加 Web 控制界面
- 支持移动端客户端

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题，请通过以下方式联系：
- 提交 GitHub Issue
- 发送邮件至：[your-email@example.com]

---

**注意**：本项目专为 ESP32 等嵌入式设备设计，但也可在普通计算机上运行测试。
