

# 克隆官方仓库
git clone https://github.com/FunAudioLLM/SenseVoice.git
cd SenseVoice

# 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
pip install --user fastapi-cli

# 在SenseVoice目录下
export SENSEVOICE_DEVICE=cuda:0  # 设置使用的GPU设备
fastapi run --port 50000  # 启动服务在50000端口

# 在SenseVoice目录下
python webui.py
