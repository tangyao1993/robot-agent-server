import requests
import os
import time
import logging
from typing import Union, List, Dict, Any

# 添加性能日志记录器
# perf_logger = logging.getLogger("PerformanceLog")

class SpeechRecognizer:
    """
    语音识别器类，用于将音频转换为文本
    """
    
    def __init__(self, server_url: str = "http://192.168.1.4:50000/api/v1/asr"):
        """
        初始化语音识别器
        
        参数:
        server_url: ASR服务器URL
        """
        self.server_url = server_url
    
    def recognize(self, audio_path: Union[str, List[str]], language: str = "auto") -> str:
        """
        将音频文件转换为文本
        
        参数:
        audio_path: 音频文件路径，可以是单个文件路径或文件路径列表
        language: 语言选项 "auto", "zh", "en", "yue", "ja", "ko", "nospeech"
        
        返回:
        识别出的文本
        """
        # # 记录文件大小信息
        # if isinstance(audio_path, str):
        #     file_size = os.path.getsize(audio_path) / 1024  # KB
        #     file_name = os.path.basename(audio_path)
        #     perf_logger.info(f"[性能] [ASR详情] 处理文件 | 文件名: {file_name} | 大小: {file_size:.2f} KB")
        
        # # 记录请求开始时间
        # start_time = time.time()
        # perf_logger.info(f"[性能] [ASR详情] 开始ASR请求 | 服务器: {self.server_url}")
        
        response_data = self._send_request(audio_path, language)
        
        # # 记录请求结束时间
        # end_time = time.time()
        # request_duration = end_time - start_time
        
        # 处理返回结果，提取文本
        result_text = ""
        if isinstance(response_data, dict) and 'result' in response_data:
            if response_data['result'] and len(response_data['result']) > 0:
                result_text = response_data['result'][0]['text']
        
        # # 记录识别结果信息
        # perf_logger.info(f"[性能] [ASR详情] 请求完成 | 耗时: {request_duration:.2f}秒 | 识别文本长度: {len(result_text)}")
        
        # # 如果耗时超过2秒，记录警告信息
        # if request_duration > 2.0:
        #     perf_logger.warning(f"[性能] [ASR警告] ASR处理耗时较长 | 耗时: {request_duration:.2f}秒")
        
        return result_text if result_text else str(response_data)
    
    def recognize_multiple(self, audio_path: Union[str, List[str]], language: str = "auto") -> List[Dict[str, str]]:
        """
        将音频文件转换为文本，返回完整的结果列表
        
        参数:
        audio_path: 音频文件路径，可以是单个文件路径或文件路径列表
        language: 语言选项 "auto", "zh", "en", "yue", "ja", "ko", "nospeech"
        
        返回:
        识别结果列表，包含文件名和识别文本
        """
        response_data = self._send_request(audio_path, language)
        
        # 处理返回结果
        if isinstance(response_data, dict) and 'result' in response_data:
            return response_data['result']
        
        # 如果无法提取结果，则返回空列表
        return []
    
    def _send_request(self, audio_path: Union[str, List[str]], language: str) -> Any:
        """
        发送请求到ASR服务器
        
        参数:
        audio_path: 音频文件路径，可以是单个文件路径或文件路径列表
        language: 语言选项
        
        返回:
        服务器响应的JSON数据
        """
        # 处理单个文件和多个文件的情况
        if isinstance(audio_path, str):
            audio_paths = [audio_path]
        else:
            audio_paths = audio_path
        
        # 准备文件和键值
        files = []
        keys = []
        file_objects = []  # 存储文件对象以便后续关闭
        
        # 记录文件准备开始时间
        prep_start_time = time.time()
        
        for path in audio_paths:
            # 获取文件名作为key
            filename = os.path.basename(path)
            keys.append(filename)
            
            # 打开文件
            file_obj = open(path, 'rb')
            file_objects.append(file_obj)
            
            # 准备文件对象
            files.append(
                ('files', (filename, file_obj, 'audio/wav'))
            )
        
        # 记录文件准备结束时间
        prep_end_time = time.time()
        prep_duration = prep_end_time - prep_start_time
        
        # 构建请求数据
        data = {
            'keys': ','.join(keys),
            'lang': language
        }
        
        # 记录网络请求开始时间
        # request_start_time = time.time()
        # perf_logger.info(f"[性能] [ASR详情] 文件准备完成 | 文件数: {len(files)} | 耗时: {prep_duration:.2f}秒")
        
        try:
            # 发送请求
            response = requests.post(self.server_url, files=files, data=data)
            
            # 记录网络请求结束时间
            # request_end_time = time.time()
            # request_duration = request_end_time - request_start_time
            
            # 解析结果
            if response.status_code == 200:
                # perf_logger.info(f"[性能] [ASR详情] 网络请求完成 | 状态码: 200 | 耗时: {request_duration:.2f}秒 | 响应大小: {len(response.content)/1024:.2f} KB")
                return response.json()
            else:
                # perf_logger.error(f"[性能] [ASR详情] 请求失败 | 状态码: {response.status_code} | 耗时: {request_duration:.2f}秒")
                return f"错误: {response.status_code}, {response.text}"
        except Exception as e:
            # # 记录异常情况
            # error_time = time.time()
            # error_duration = error_time - request_start_time
            # perf_logger.error(f"[性能] [ASR详情] 请求异常 | 耗时: {error_duration:.2f}秒 | 错误: {str(e)}")
            return f"异常: {str(e)}"
        finally:
            # 确保所有文件都被关闭
            for file_obj in file_objects:
                file_obj.close()


# 使用示例
if __name__ == "__main__":
    # 创建语音识别器实例
    recognizer = SpeechRecognizer()
    
    # 识别单个文件
    text = recognizer.recognize("audio_files/test.wav")
    print(f"识别结果: {text}")
    
    # 识别多个文件并获取详细结果
    # results = recognizer.recognize_multiple(["audio_files/test1.wav", "audio_files/test2.wav"])
    # for result in results:
    #     print(f"文件: {result['key']}, 文本: {result['text']}")