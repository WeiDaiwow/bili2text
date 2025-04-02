"""
系统依赖检查模块
"""
import importlib
import subprocess
import sys
import os
import src.log as log
from src.config import *
# output/
#  - tmp：储存下载的视频/转换的音频等临时文件
#    - videos：储存下载的视频
#    - audios：储存转换的音频
#  - result：输出的稿件位置
#  - meta：储存一个转换的元数据（标题、地址、时长、作者、BV号，视频文件地址、文字稿件地址）

def ensure_folders_exist():
    """确保所有必要的文件夹存在"""
    try:
        # 创建所有必需的目录
        for directory in [
            DATA_DIR,
            OUTPUT_DIR,
            f"{OUTPUT_DIR}/tmp",
            DOWNLOAD_DIR,
            AUDIO_DIR,
            f"{OUTPUT_DIR}/result",
            TRANSCRIPT_DIR,
            THUMBNAIL_DIR,
            f"{OUTPUT_DIR}/meta"
        ]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        log.info("所有必要的文件夹已创建。")
        return True
    except Exception as e:
        log.error(f"创建文件夹失败: {str(e)}，请检查权限并重试。")
        return False

def check_dependency(module_name):
    """检查Python模块依赖是否已安装"""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def check_external_tool(tool_name):
    """检查外部工具是否已安装并可在PATH中找到"""
    try:
        subprocess.run([tool_name, "--version"], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def check_dependencies():
    """检查所有项目依赖"""
    dependencies = {
        "python_modules": [
            "requests", 
            "whisper", 
            "moviepy", 
            "pydub", 
            "torch"
        ],
        "external_tools": [
            "ffmpeg"
        ]
    }
    
    # 检查下载工具
    if DOWNLOAD_TOOL == "you-get" and not check_external_tool("you-get"):
        log.warning("未检测到you-get工具，但配置中指定使用you-get下载视频")
    
    if DOWNLOAD_TOOL == "yt-dlp" and not check_external_tool("yt-dlp"):
        log.warning("未检测到yt-dlp工具，但配置中指定使用yt-dlp下载视频")
    
    # 检查Python模块
    missing_modules = []
    for module in dependencies["python_modules"]:
        if not check_dependency(module):
            missing_modules.append(module)
    
    # 检查外部工具
    missing_tools = []
    for tool in dependencies["external_tools"]:
        if not check_external_tool(tool):
            missing_tools.append(tool)
    
    # 报告缺失的依赖
    if missing_modules or missing_tools:
        log.warning("检测到缺失的依赖")
        
        if missing_modules:
            log.warning(f"缺失的Python模块: {', '.join(missing_modules)}")
            log.info(f"可以使用命令安装: pip install {' '.join(missing_modules)}")
        
        if missing_tools:
            log.warning(f"缺失的外部工具: {', '.join(missing_tools)}")
        return False
    
    return True

class SelfCheck:
    def __init__(self):
        self.checks = [
            ensure_folders_exist,
            check_dependencies
        ]
        
    def run(self):
        log.info("开始自检...")
        for check in self.checks:
            if not check():
                log.error("自检失败，请检查错误信息并修复后再试。")
                return False
        log.success("自检通过！")
        return True