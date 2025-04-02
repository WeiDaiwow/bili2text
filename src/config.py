# 目录配置
DATA_DIR = "data"
OUTPUT_DIR = "output"
DOWNLOAD_DIR = "output/tmp/videos"
AUDIO_DIR = "output/tmp/audio"
TRANSCRIPT_DIR = f"{OUTPUT_DIR}/result/transcripts"
THUMBNAIL_DIR = f"{OUTPUT_DIR}/result/thumbnails"
META_DIR = f"{OUTPUT_DIR}/meta"

# 下载工具
DOWNLOAD_TOOL = "yt-dlp"  # 可选: "api", "you-get", "yt-dlp"

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
