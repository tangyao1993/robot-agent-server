"""
配置文件
"""

import os

def get_google_config():
    """
    获取 Google Gemini 服务的配置。
    """
    return {
        "api_key": os.getenv("GOOGLE_API_KEY"),
        "model_name": "gemini-1.5-pro-latest"
    }

def get_tts_config():
    """
    获取TTS服务的配置（例如API地址）。
    """
    # 优先从环境变量获取，如果未设置则使用默认的URL
    api_url = os.getenv("MINDCRaft_API_URL", "https://api.mindcraft.com.cn/v1/audio/speech")
    api_key = os.getenv("MINDCRaft_API_KEY","MC-035DD5C8CA1141E19009DB0AD9881F17")
    return {
        "api_url": api_url,
        "api_key": api_key
    }

def get_tts_model_config():
    """
    获取TTS模型的具体参数。
    """
    return {
        "model": "ZJ_TTSL_realtime",
        "voice_id": "zh_female_wanwanxiaohe_moon_bigtts",
        "output_format": "pcm",
        "audio_sample_rate": 16000,
        "speed": 0
    }
