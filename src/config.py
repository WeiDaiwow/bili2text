# 目录配置
DATA_DIR = "data"
OUTPUT_DIR = "outputs"
DOWNLOAD_DIR = "bilibili_video"
AUDIO_DIR = "audio"
TRANSCRIPT_DIR = f"{OUTPUT_DIR}/transcripts"

# 转录配置
DEFAULT_ENGINE = "whisper"
DEFAULT_MODEL = "small"
DEFAULT_PROMPT = "以下是普通话的句子。"

# 讯飞API配置 (如需使用讯飞API，请填写您的应用ID和密钥)
XUNFEI_APP_ID = ""
XUNFEI_SECRET_KEY = ""

# Web服务器配置
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000
DEBUG_MODE = True

# 数据库配置
DATABASE_PATH = f"{DATA_DIR}/bili2text.db"
