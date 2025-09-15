import os
import logging
import google.genai as genai
from concurrent.futures import ThreadPoolExecutor, as_completed


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class KeyManager:
    def __init__(self, key_file_path):
        self.key_file_path = key_file_path

    def _validate_key(self, key: str) -> bool:
        """使用一个简单的API调用来验证密钥的有效性"""
        try:
            # 使用提供的key创建一个临时的client
            genai.Client(api_key=key).models.generate_content(
                model='gemini-2.5-flash', contents='hello'
            )
            # print(response.text)
            logging.info(f"API 密钥 {key[:8]}... 验证通过。")
            return True
        except Exception as e:
            # 捕获所有异常，因为API可能因多种原因失败（如无效key、网络问题等）
            #logging.warning(f"API 密钥 {key[:8]}... 无效或已过期，已从池中移除。错误: {e}")
            return False

    def _load_and_validate_keys(self, key_file_path: str):
        """从指定文件中加载API密钥，并使用线程池并行验证后放入队列中"""
        try:
            with open(key_file_path, 'r', encoding='utf-8') as f:
                keys = [line.strip() for line in f if line.strip()]
            
            if not keys:
                raise ValueError(f"密钥文件 {key_file_path} 中没有找到可用的key。")
            
            logging.info(f"从 {key_file_path} 读取到 {len(keys)} 个API密钥，开始并行验证...")

            valid_keys = []
            # 使用线程池并行验证密钥
            with ThreadPoolExecutor(max_workers=min(20, len(keys))) as executor:
                # 提交所有密钥验证任务
                future_to_key = {executor.submit(self._validate_key, key): key for key in keys}
                
                for future in as_completed(future_to_key):
                    key = future_to_key[future]
                    try:
                        if future.result():
                            valid_keys.append(key)
                    except Exception as exc:
                        logging.warning(f"验证密钥 {key[:8]}... 时发生异常: {exc}")

            if not valid_keys:
                raise ValueError("密钥池中没有可用的有效API密钥。所有密钥都未能通过验证。")

            logging.info(f"成功加载并验证了 {len(valid_keys)}/{len(keys)} 个API密钥。")
            logging.info(f"可用key列表: {valid_keys}")

        except FileNotFoundError:
            logging.error(f"API密钥文件未找到：{key_file_path}")
            raise
        except Exception as e:
            logging.error(f"加载API密钥时发生错误: {e}")
            raise

    def load_keys_local(self):
        self._load_and_validate_keys(key_file)


# 密钥文件路径
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
key_file = os.path.join(script_dir,'gemini_key','gemini_keys.txt')

# 创建一个全局的KeyManager实例
key_manager = KeyManager(key_file)

def load_keys_local():
    """从 gemini_keys_back.txt 加载密钥用于本地测试"""
    key_manager.load_keys_local()



if __name__ == "__main__":
    # load_keys()
    # 本地测试
    load_keys_local()