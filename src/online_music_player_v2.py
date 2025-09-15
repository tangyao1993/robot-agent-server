import requests
import asyncio
from pydub import AudioSegment
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

# 客户端期望的音频参数
CLIENT_SAMPLE_RATE = 16000
CLIENT_CHANNELS = 1
CLIENT_SAMPLE_WIDTH = 2  # 16-bit

# 网易云音乐API
SEARCH_API_URL = 'http://music.163.com/api/search/get/web'
SONG_URL_TEMPLATE = 'http://music.163.com/song/media/outer/url?id={}.mp3'
HEADERS = {
    'Referer': 'http://music.163.com/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

async def search_music(keyword: str):
    """
    根据关键词在网易云音乐搜索音乐。
    
    Args:
        keyword (str): 搜索关键词，可以是歌名或歌名+歌手。
    
    Returns:
        dict: 包含歌曲信息的字典 (id, name, artist, url)，如果找不到则返回 None。
    """
    logger.info(f"Searching for music with keyword: '{keyword}' on NetEase Music API...")
    params = {'s': keyword, 'type': 1, 'limit': 1}
    
    try:
        # 在异步函数中运行同步的requests代码
        loop = asyncio.get_event_loop()
        search_response = await loop.run_in_executor(
            None, 
            lambda: requests.get(SEARCH_API_URL, params=params, headers=HEADERS, timeout=10)
        )
        search_response.raise_for_status()
        search_results = search_response.json()
        
        if search_results.get('result', {}).get('songCount', 0) > 0:
            song = search_results['result']['songs'][0]
            song_id = song['id']
            found_song_name = song['name']
            artist_name = song['artists'][0]['name']
            music_url = SONG_URL_TEMPLATE.format(song_id)
            
            logger.info(f"Found song: '{found_song_name}' by {artist_name} (ID: {song_id}).")
            return {
                "id": song_id,
                "name": found_song_name,
                "artist": artist_name,
                "url": music_url
            }
        else:
            logger.warning(f"No results found for keyword: '{keyword}'")
            return None
            
    except requests.RequestException as e:
        logger.error(f"Error searching for music: {e}")
        return None
    except (KeyError, IndexError):
         logger.error(f"Error parsing search results for '{keyword}'.")
         return None


async def get_music_stream(music_url: str):
    """
    从给定的音乐URL下载、解码并返回PCM音频流数据。
    
    Args:
        music_url (str): 音乐文件的URL (e.g., mp3 link)。
    
    Returns:
        bytes: 原始PCM音频数据。如果失败则返回 None。
    """
    # 1. 下载音乐文件
    try:
        logger.info(f"Downloading music from: {music_url}")
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.get(music_url, headers=HEADERS, timeout=20, allow_redirects=True)
        )
        response.raise_for_status()
        
        if 'audio' not in response.headers.get('Content-Type', ''):
            logger.warning(f"Downloaded content may not be a valid MP3. Content-Type: {response.headers.get('Content-Type')}. The song might be protected or unavailable.")
            if not response.content:
                return None
        
        music_data = BytesIO(response.content)
        logger.info("Music downloaded successfully.")
    except requests.RequestException as e:
        logger.error(f"Failed to download music: {e}")
        return None

    # 2. 解码并重采样音频
    try:
        logger.info("Decoding audio stream...")
        audio = AudioSegment.from_file(music_data, format="mp3")
        
        audio = audio.set_frame_rate(CLIENT_SAMPLE_RATE)
        audio = audio.set_channels(CLIENT_CHANNELS)
        audio = audio.set_sample_width(CLIENT_SAMPLE_WIDTH)
        
        pcm_data = audio.raw_data
        logger.info(f"Audio decoded. PCM data size: {len(pcm_data)} bytes.")
        return pcm_data

    except Exception as e:
        logger.error(f"Failed to decode audio: {e}", exc_info=True)
        return None 
    
async def get_music(keyword: str):
    music_info = await search_music(keyword)
    if music_info:
        return await get_music_stream(music_info["url"])
    else:
        return None
