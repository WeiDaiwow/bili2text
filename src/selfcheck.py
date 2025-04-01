"""
系统依赖检查模块
"""
import importlib
import subprocess
import sys
import os
import src.log as log

# output/
#  - tmp：储存下载的视频/转换的音频等临时文件
#    - videos：储存下载的视频
#    - audios：储存转换的音频
#  - result：输出的稿件位置
#  - meta：储存一个转换的元数据（标题、地址、时长、作者、BV号，视频文件地址、文字稿件地址）

def ensure_folders_exist():
    try:
        if not os.path.exists("output"):
            os.makedirs("output")
        if not os.path.exists("output/tmp"):
            os.makedirs("output/tmp")
        if not os.path.exists("output/tmp/videos"):
            os.makedirs("output/tmp/videos")
        if not os.path.exists("output/tmp/audios"):
            os.makedirs("output/tmp/audios")
        if not os.path.exists("output/result"):
            os.makedirs("output/result")
        if not os.path.exists("output/meta"):
            os.makedirs("output/meta")
        log.info("所有必要的文件夹已创建。")
        return True
    except Exception as e:
        log.error(f"创建文件夹失败：{str(e)}，请检查权限并重试。")
        return False

def check_dependency(module_name):
    """检查Python模块依赖是否已安装"""
    try:
        importlib.import_module(module_name)
        log.info(f"模块 {module_name} 已安装。")
        return True
    except ImportError:
        log.error(f"模块 {module_name} 未安装。")
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
            "ffmpeg",
            "you-get"  # 可选依赖，用于you-get下载方式
        ]
    }
    
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
            log.warning("缺失的Python模块:")
            for module in missing_modules:
                log.warning(f"  - {module}")
            log.info("可以使用以下命令安装:")
            log.info(f"  pip install {' '.join(missing_modules)}")
        
        if missing_tools:
            log.warning("缺失的外部工具:")
            for tool in missing_tools:
                log.warning(f"  - {tool}")
            log.info("请参考项目文档了解如何安装这些工具。")
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