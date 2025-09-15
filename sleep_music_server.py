import asyncio
import websockets
from pydub import AudioSegment
import opuslib_next as opuslib
import os
import time

# 配置
WAV_FILE_PATH = "sleep.wav"  # 本地WAV文件路径
SAMPLE_RATE = 24000  # 采样率 - 24kHz
CHANNELS = 2  # 声道数
FRAME_DURATION_MS = 60  # 帧时长，单位ms
OPUS_COMPLEXITY = 0  # Opus复杂度

class AudioStreamer:
    """实时音频流处理器"""
    
    def __init__(self, wav_file_path: str):
        self.wav_file_path = wav_file_path
        self.audio_data = None
        self.frame_length = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # 每帧的样本数
        self.frame_size_bytes = self.frame_length * CHANNELS * 2  # 每帧字节数
        self.current_position = 0
        self.encoder = None
        self.total_original_bytes = 0  # 原始音频总字节数
        self.total_encoded_bytes = 0   # 编码后总字节数
        self.frame_count = 0           # 编码帧数
        self._load_audio()
    
    def _load_audio(self):
        """加载音频文件"""
        try:
            if not os.path.exists(self.wav_file_path):
                print(f"Error: 音频文件不存在: {self.wav_file_path}")
                return
            
            print(f"正在加载音频文件: {self.wav_file_path}")
            
            # 加载WAV文件
            audio = AudioSegment.from_wav(self.wav_file_path)
            
            # 转换为指定采样率和声道数
            audio = audio.set_frame_rate(SAMPLE_RATE).set_channels(CHANNELS)
            
            # 获取原始音频数据
            self.audio_data = audio.raw_data
            
            # 初始化Opus编码器
            self.encoder = opuslib.Encoder(SAMPLE_RATE, CHANNELS, opuslib.APPLICATION_AUDIO)
            self.encoder.complexity = OPUS_COMPLEXITY
            
            print(f"音频加载完成，总长度: {len(self.audio_data)} 字节")
            print(f"帧大小: {self.frame_size_bytes} 字节，总帧数: {len(self.audio_data) // self.frame_size_bytes}")
            
        except Exception as e:
            print(f"Error: 音频加载失败: {e}")
            self.audio_data = None
    
    def get_next_frame(self):
        """获取下一帧音频数据并编码"""
        if not self.audio_data or not self.encoder:
            return None
        
        # 检查是否到达音频末尾
        if self.current_position >= len(self.audio_data):
            # 循环播放
            self.current_position = 0
            print("音频播放完毕，重新开始")
        
        # 获取当前帧数据
        end_pos = min(self.current_position + self.frame_size_bytes, len(self.audio_data))
        frame_data = self.audio_data[self.current_position:end_pos]
        
        # 如果帧数据不足，用静音填充
        if len(frame_data) < self.frame_size_bytes:
            silence = b'\x00' * (self.frame_size_bytes - len(frame_data))
            frame_data += silence
        
        # 更新位置
        self.current_position = end_pos
        
        try:
            # 编码帧数据 - opuslib_next 需要指定 frame_size
            encoded_data = self.encoder.encode(frame_data, self.frame_length)
            
            # 统计压缩率
            self.total_original_bytes += len(frame_data)
            self.total_encoded_bytes += len(encoded_data)
            self.frame_count += 1
            
            # 每100帧打印一次压缩率
            if self.frame_count % 100 == 0:
                compression_ratio = self.total_original_bytes / self.total_encoded_bytes if self.total_encoded_bytes > 0 else 0
                compression_percent = (1 - self.total_encoded_bytes / self.total_original_bytes) * 100 if self.total_original_bytes > 0 else 0
                print(f"压缩统计 - 帧数: {self.frame_count}, 压缩比: {compression_ratio:.2f}:1, 压缩率: {compression_percent:.1f}%")
            
            return encoded_data
        except Exception as e:
            print(f"Error: 编码失败: {e}")
            return None
    
    def reset(self):
        """重置播放位置"""
        self.current_position = 0

# 全局音频流处理器
audio_streamer = None

# WebSocket处理
async def handle_client(websocket):
    global audio_streamer
    
    client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
    print(f"新客户端连接: {client_ip}")
    
    try:
        # 为每个新连接创建新的音频流处理器
        audio_streamer = AudioStreamer(WAV_FILE_PATH)
        
        if not audio_streamer.audio_data:
            print("Error: 音频数据未加载，无法提供服务")
            await websocket.close(code=1000, reason="Audio not loaded")
            return
        
        print(f"开始向客户端 {client_ip} 实时传输音频（从头开始）")
        
        # 实时传输音频帧
        frame_count = 0
        while True:
            try:
                # 获取下一帧编码数据
                encoded_frame = audio_streamer.get_next_frame()
                
                if encoded_frame is None:
                    print("Error: 无法获取音频帧")
                    break
                
                # 发送编码后的帧数据
                await websocket.send(encoded_frame)
                frame_count += 1
                
                # 连续发送，每帧间隔60ms（与帧时长一致）
                await asyncio.sleep(FRAME_DURATION_MS / 1000.0)
                
                # 每20帧打印一次状态
                if frame_count % 20 == 0:
                    print(f"已发送 {frame_count} 帧到客户端 {client_ip}")
                
            except websockets.exceptions.ConnectionClosed:
                print(f"客户端 {client_ip} 断开连接")
                break
            except Exception as e:
                print(f"Error: 发送音频帧时出错: {e}")
                break
        
        print(f"音频传输结束，共发送 {frame_count} 帧，客户端: {client_ip}")
        
    except Exception as e:
        print(f"Error: 处理客户端 {client_ip} 时出错: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass

# 启动WebSocket服务器
async def start_server():
    global audio_streamer
    
    # 预加载音频数据
    print("正在初始化音频流处理器...")
    audio_streamer = AudioStreamer(WAV_FILE_PATH)
    
    if not audio_streamer.audio_data:
        print("Error: 音频初始化失败，服务器无法启动")
        return
    
    # 启动WebSocket服务器
    server = await websockets.serve(handle_client, "localhost", 8765)
    print("WebSocket服务器已启动: ws://localhost:8765")
    print(f"音频文件: {WAV_FILE_PATH}")
    print(f"采样率: {SAMPLE_RATE}Hz, 声道数: {CHANNELS}, 帧时长: {FRAME_DURATION_MS}ms")
    
    try:
        await server.wait_closed()
    except KeyboardInterrupt:
        print("服务器正在关闭...")
        server.close()
        await server.wait_closed()

# 启动服务
if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("服务器已停止")