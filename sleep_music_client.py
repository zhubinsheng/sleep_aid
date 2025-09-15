import asyncio
import websockets
import pyaudio
import opuslib_next as opuslib
import sys
from collections import deque
import threading
import time
import wave
import os

# 配置
SERVER_URL = "ws://180.76.190.230:8765"
SAMPLE_RATE = 24000  # 采样率 - 24kHz
CHANNELS = 2
FRAME_DURATION_MS = 60

# PyAudio配置
CHUNK = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
FORMAT = pyaudio.paInt16

class AudioPlayerRecorder:
    """边播边录的音频处理器"""
    
    def __init__(self, output_file="recorded_audio.wav"):
        self.output_file = output_file
        self.audio_data = []
        self.frame_count = 0
        self.play_count = 0
        
        # 初始化PyAudio
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            output=True,
            frames_per_buffer=CHUNK
        )
        
        # 播放缓冲区
        self.audio_buffer = deque()
        self.is_playing = False
        self.play_thread = None
        
    def start_playing(self):
        """开始播放"""
        if not self.is_playing:
            self.is_playing = True
            self.play_thread = threading.Thread(target=self._play_loop)
            self.play_thread.daemon = True
            self.play_thread.start()
            print("音频播放线程启动")
    
    def stop_playing(self):
        """停止播放"""
        self.is_playing = False
        if self.play_thread:
            self.play_thread.join()
        print("音频播放线程停止")
    
    def add_audio_frame(self, pcm_data):
        """添加音频帧到播放缓冲区和录制"""
        # 添加到播放缓冲区
        self.audio_buffer.append(pcm_data)
        
        # 录制音频
        self.audio_data.append(pcm_data)
        self.frame_count += 1
        if self.frame_count % 200 == 0:
            print(f"已处理 {self.frame_count} 帧，播放缓冲区: {len(self.audio_buffer)} 帧")
    
    def _play_loop(self):
        """播放循环"""
        while self.is_playing:
            if len(self.audio_buffer) > 0:
                try:
                    pcm_data = self.audio_buffer.popleft()
                    
                    # 播放音频帧
                    self.stream.write(pcm_data)
                    self.play_count += 1
                    
                    # 每100帧打印一次状态
                    if self.play_count % 20 == 0:
                        print(f"已播放 {self.play_count} 帧")
                    
                except Exception as e:
                    print(f"播放错误: {e}")
            else:
                time.sleep(0.01)  # 缓冲区为空时等待
    
    def save_to_file(self):
        """保存到WAV文件"""
        if not self.audio_data:
            print("没有音频数据")
            return
            
        print(f"正在保存音频到文件: {self.output_file}")
        
        # 合并所有音频数据
        all_audio = b''.join(self.audio_data)
        
        # 保存为WAV文件
        with wave.open(self.output_file, 'wb') as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(2)  # 16位
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(all_audio)
        
        duration = len(all_audio) / (SAMPLE_RATE * CHANNELS * 2)
        print(f"音频已保存: {self.output_file}")
        print(f"总帧数: {self.frame_count}")
        print(f"总时长: {duration:.2f} 秒")
        print(f"文件大小: {len(all_audio)} 字节")
    
    def close(self):
        """关闭播放器"""
        self.stop_playing()
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        

async def stream_audio_client():
    """连接到WebSocket服务器并边播边录"""
    
    # 初始化播放录制器和解码器
    player_recorder = AudioPlayerRecorder()
    decoder = opuslib.Decoder(SAMPLE_RATE, CHANNELS)
    
    print(f"正在尝试连接到服务器: {SERVER_URL}")
    
    try:
        # 连接WebSocket
        async with websockets.connect(SERVER_URL) as websocket:
            print("连接成功，开始边播边录...")
            
            # 开始播放
            player_recorder.start_playing()
            
            print("开始接收和播放音频...")
            
            while True:
                try:
                    # 接收Opus编码的音频帧
                    encoded_frame = await websocket.recv()
                    
                    if not encoded_frame:
                        print("警告: 接收到空帧，连接可能已关闭")
                        break
                    
                    # 解码Opus数据 - 使用正确的帧大小
                    pcm_data = decoder.decode(encoded_frame, CHUNK)
                    
                    # 添加到播放缓冲区和录制
                    player_recorder.add_audio_frame(pcm_data)
                    
                except websockets.exceptions.ConnectionClosed:
                    print("服务器断开连接")
                    break
                except Exception as e:
                    print(f"错误: 处理音频帧时出错: {e}")
                    break
    
    except ConnectionRefusedError:
        print("错误: 连接失败，请确保服务器已启动并在监听")
    except Exception as e:
        print(f"错误: 发生错误: {e}")
        
    finally:
        # 保存录制的音频
        print("正在保存录制的音频...")
        player_recorder.save_to_file()
        player_recorder.close()

# 启动客户端
if __name__ == "__main__":
    try:
        asyncio.run(stream_audio_client())
    except KeyboardInterrupt:
        print("客户端已停止")