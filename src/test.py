import asyncio
import os
import logging
import wave
from tts_processor import VolcanoTTSProcessor, VOLCANO_SAMPLE_RATE

# 配置基本的日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def save_pcm_as_wav(pcm_data: bytes, file_path: str, channels: int = 1, sample_width: int = 2, frame_rate: int = VOLCANO_SAMPLE_RATE):
    """
    将原始PCM数据保存为WAV文件。

    Args:
        pcm_data (bytes): 原始PCM音频数据。
        file_path (str): 保存WAV文件的路径。
        channels (int): 通道数 (1 for mono, 2 for stereo)。
        sample_width (int): 样本宽度（字节数），例如16-bit为2。
        frame_rate (int): 采样率 (例如 16000)。
    """
    if not pcm_data:
        logging.error("没有PCM数据可供保存。")
        return
    try:
        with wave.open(file_path, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(frame_rate)
            wf.writeframes(pcm_data)
        logging.info(f"已成功将音频保存为WAV文件: {file_path}")
    except Exception as e:
        logging.error(f"保存WAV文件时出错: {e}", exc_info=True)

async def run_tts_test():
    """运行VolcanoTTSProcessor的测试，并将结果保存为WAV文件。"""
    logging.info("--- 开始测试 VolcanoTTSProcessor (保存为WAV) ---")

    # 确保 'test_output' 文件夹存在
    output_dir = "test_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 定义输出文件路径
    output_file_path = os.path.join(output_dir, "volcano_tts_output.wav")

    # 1. 实例化TTS处理器
    try:
        tts_processor = VolcanoTTSProcessor()
    except Exception as e:
        logging.error(f"实例化 VolcanoTTSProcessor 失败: {e}")
        return
        
    # 2. 定义要合成的测试文本
    test_text = "你好，这是一个火山引擎语音合成的测试。如果能听到我说话，说明测试成功。"

    # 3. 执行TTS合成
    logging.info(f"正在合成文本: '{test_text}'")
    try:
        # 调用新的 synthesize 方法获取完整的音频数据
        pcm_audio_data = await tts_processor.synthesize(test_text)
        
        # 将返回的PCM数据保存为WAV文件
        if pcm_audio_data:
            save_pcm_as_wav(pcm_audio_data, output_file_path, frame_rate=VOLCANO_SAMPLE_RATE)
        else:
            logging.error("合成失败，未收到任何音频数据。")

    except Exception as e:
        logging.error(f"在测试过程中发生错误: {e}", exc_info=True)
    
    logging.info("--- 测试完成 ---")
    if os.path.exists(output_file_path) and os.path.getsize(output_file_path) > 0:
        logging.info(f"您可以直接播放文件 '{output_file_path}' 来验证结果。")
    else:
        logging.error("测试失败，未能生成有效的音频文件。")

if __name__ == "__main__":
    asyncio.run(run_tts_test())
