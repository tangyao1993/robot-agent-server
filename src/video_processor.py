import cv2
import os
import time
import asyncio
import logging
import struct
import random
import numpy as np
import websockets

logger = logging.getLogger("VideoProcessor")

# 协议常量
MAGIC_BYTE = 0xAA
PACKET_TYPE_CONFIG = 0x01
PACKET_TYPE_FRAME = 0x02
PACKET_TYPE_END = 0x03

class VideoProcessor:
    """视频处理类，负责视频流传输和相关处理"""
    
    def __init__(self, video_dir):
        """
        初始化视频处理器
        
        Args:
            video_dir: 视频文件目录
        """
        self.video_dir = video_dir
        os.makedirs(self.video_dir, exist_ok=True)
        logger.info(f"视频将从此目录加载: {self.video_dir}")
        
    def create_packet(self, packet_type, data):
        """
        创建与客户端匹配的网络协议包
        
        Args:
            packet_type: 数据包类型
            data: 数据包内容
            
        Returns:
            完整的二进制数据包
        """
        # 头部: Magic Byte(1) + 类型(1) + 长度(4, Big Endian)
        header = struct.pack('>BBI', MAGIC_BYTE, packet_type, len(data))
        return header + data
        
    def get_random_video(self):
        """
        从video_files目录中随机选择一个视频文件
        
        Returns:
            视频文件的完整路径，如果没有找到则返回None
        """
        try:
            videos = [f for f in os.listdir(self.video_dir) if f.lower().endswith(('.mp4', '.avi', '.mov'))]
            if not videos:
                logger.error(f"在 '{self.video_dir}' 目录中未找到任何视频文件。")
                return None
            return os.path.join(self.video_dir, random.choice(videos))
        except Exception as e:
            logger.error(f"查找视频文件时出错: {e}")
            return None
            
    async def send_video_stream(self, websocket, video_path):
        """
        向客户端流式传输视频
        
        Args:
            websocket: WebSocket连接
            video_path: 视频文件路径
        """
        try:
            if not os.path.exists(video_path):
                logger.error(f"视频文件不存在: {video_path}")
                return
                
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"无法打开视频文件: {video_path}")
                return

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            logger.info(f"开始推流视频: {os.path.basename(video_path)} ({width}x{height} @ {fps}fps为源视频帧率)")

            # 动态设置目标帧率：取源视频帧率和性能上限（15fps）中较小的一个
            MAX_ALLOWED_FPS = 10
            target_fps = min(fps, MAX_ALLOWED_FPS)
            if target_fps != fps:
                logger.info(f"源视频帧率 ({fps}fps) 过高, 已限制为 {target_fps}fps 进行推流。")
            
            # --- 发送配置包 ---
            try:
                # 目标尺寸是240x240
                config_data = struct.pack('>HHB', 240, 240, target_fps)
                config_packet = self.create_packet(PACKET_TYPE_CONFIG, config_data)
                await websocket.send(config_packet)
                logger.info(f"已发送视频配置包 (240x240 @ {target_fps}fps)")
            except Exception as e:
                logger.error(f"发送配置包失败: {e}")
                return # 如果配置失败，则不继续

            frame_interval = 1.0 / target_fps
            frame_count = 0

            while cap.isOpened():
                start_time = time.time()

                ret, frame = cap.read()
                if not ret:
                    logger.info("视频文件读取完毕.")
                    break
                
                # 调整帧大小
                resized_frame = cv2.resize(frame, (240, 240), interpolation=cv2.INTER_AREA)

                # 将帧编码为JPEG
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
                result, jpeg_bytes_np = cv2.imencode('.jpg', resized_frame, encode_param)

                if not result:
                    logger.warning("JPEG编码失败，跳过此帧")
                    continue
                
                jpeg_bytes = jpeg_bytes_np.tobytes()
                
                # 创建视频帧数据包
                video_packet = self.create_packet(PACKET_TYPE_FRAME, jpeg_bytes)
                await websocket.send(video_packet)
                
                frame_count += 1
                if frame_count > 0 and frame_count % 100 == 0:
                    logger.info(f"已发送 {frame_count} 帧JPEG数据")
                
                # --- 精确的帧率控制 ---
                elapsed_time = time.time() - start_time
                sleep_time = frame_interval - elapsed_time
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
        
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"连接在视频流传输期间关闭: {e.code} {e.reason}")
        except Exception as e:
            logger.error(f"视频流处理错误: {e}", exc_info=True)
        finally:
            if cap and cap.isOpened():
                cap.release()
            # 发送结束包
            try:
                end_packet = self.create_packet(PACKET_TYPE_END, b'')
                await websocket.send(end_packet)
                logger.info("视频流结束，已发送结束包.")
            except websockets.exceptions.ConnectionClosed:
                logger.info("无法发送结束包，连接已关闭。") 