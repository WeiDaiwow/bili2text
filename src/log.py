"""
日志管理模块
"""
import logging
import sys
import os
from datetime import datetime

# 配置日志格式
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 创建日志目录
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 配置日志文件名
log_file = os.path.join(LOG_DIR, f"bili2text_{datetime.now().strftime('%Y%m%d')}.log")

# # 配置日志处理器
# logging.basicConfig(
#     level=logging.INFO,
#     format=LOG_FORMAT,
#     datefmt=DATE_FORMAT,
#     handlers=[
#         logging.FileHandler(log_file, encoding="utf-8"),
#         logging.StreamHandler(sys.stdout)
#     ]
# )

# logger = logging.getLogger("bili2text")

def logger(message):
    ... # 不保存日志到文件

# 设置彩色输出
COLORS = {
    "RESET": "\033[0m",
    "INFO": "\033[34m",    # 蓝色
    "SUCCESS": "\033[32m", # 绿色
    "WARNING": "\033[33m", # 黄色
    "ERROR": "\033[31m",   # 红色
    "CRITICAL": "\033[41m", # 红底白字
}

def info(message):
    """输出信息日志"""
    print(f"{COLORS['INFO']}[INFO] {message}{COLORS['RESET']}")
    # logger.info(message)

def success(message):
    """输出成功日志"""
    print(f"{COLORS['SUCCESS']}[SUCCESS] {message}{COLORS['RESET']}")
    # logger.info(f"[SUCCESS] {message}")

def warning(message):
    """输出警告日志"""
    print(f"{COLORS['WARNING']}[WARNING] {message}{COLORS['RESET']}")
    # logger.warning(message)

def error(message):
    """输出错误日志"""
    print(f"{COLORS['ERROR']}[ERROR] {message}{COLORS['RESET']}")
    # logger.error(message)

def critical(message):
    """输出严重错误日志"""
    print(f"{COLORS['CRITICAL']}[CRITICAL] {message}{COLORS['RESET']}")
    # logger.critical(message)

def log_to_file(message, level=logging.INFO):
    """仅记录到文件，不输出到控制台"""
    # logger.log(level, message)

if __name__ == '__main__':
    info("这是一个信息日志\n带有换行测试")
    warning("警告！注意事项\n详细信息")
    error("错误出现了\n请检查代码")
    success("操作成功\n继续下一步")
    critical("严重错误！系统崩溃")