#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
组件测试脚本 - 用于分别测试下载、音频提取和转录功能
"""

import os
import sys
import argparse
import time

# 将项目根目录添加到模块搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.download import DownloadManager
from src.transcription import TranscriptionManager
from src.config import *
import src.log as log
from src.selfcheck import SelfCheck

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="B站视频处理组件测试")
    
    # 测试模式选择
    parser.add_argument("mode", choices=["download", "audio", "transcribe", "all"],
                        help="测试模式: download=仅下载视频, audio=提取音频, transcribe=转录音频, all=全流程测试")
    
    # BV号参数 - 下载视频时需要
    parser.add_argument("--bv", help="B站视频的BV号 (download和all模式必需)")
    
    # 视频路径 - 提取音频时需要
    parser.add_argument("--video", help="视频文件路径 (audio模式必需)")
    
    # 音频路径 - 转录时需要
    parser.add_argument("--audio", help="音频文件路径 (transcribe模式必需)")
    
    # 转录相关参数
    parser.add_argument("--engine", choices=["whisper", "xunfei"], default=DEFAULT_ENGINE,
                         help="转录引擎: whisper 或 xunfei")
    parser.add_argument("--model", choices=["tiny", "base", "small", "medium", "large"], default=DEFAULT_MODEL,
                         help="Whisper模型大小 (仅当使用whisper引擎时有效)")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT,
                         help="转录提示词")
    
    # 讯飞API参数
    parser.add_argument("--xf-appid", help="讯飞API的应用ID")
    parser.add_argument("--xf-secret", help="讯飞API的密钥")
    
    return parser.parse_args()

def validate_args(args):
    """验证命令行参数"""
    if args.mode in ["download", "all"] and not args.bv:
        log.error("下载模式需要提供BV号 (--bv)")
        return False
        
    if args.mode == "audio" and not args.video:
        log.error("音频提取模式需要提供视频路径 (--video)")
        return False
        
    if args.mode == "transcribe" and not args.audio:
        log.error("转录模式需要提供音频路径 (--audio)")
        return False
        
    if (args.mode == "transcribe" or args.mode == "all") and args.engine == "xunfei":
        if not (args.xf_appid and args.xf_secret) and not (XUNFEI_APP_ID and XUNFEI_SECRET_KEY):
            log.error("使用讯飞引擎需要提供应用ID和密钥")
            log.info("您可以在命令行使用 --xf-appid 和 --xf-secret 参数提供")
            log.info("或者在config.py文件中配置XUNFEI_APP_ID和XUNFEI_SECRET_KEY")
            return False
    
    return True

def test_download(bv_number):
    """测试下载功能"""
    log.info("=" * 50)
    log.info(f"测试视频下载功能 - BV号: {bv_number}")
    
    download_manager = DownloadManager()
    start_time = time.time()
    
    result = download_manager.download_video(bv_number)
    
    elapsed_time = time.time() - start_time
    
    if result["success"]:
        log.success(f"下载成功! 用时: {elapsed_time:.2f}秒")
        log.success(f"视频保存到: {result['video_path']}")
        
        if result.get("video_info"):
            log.info("视频信息:")
            for key, value in result["video_info"].items():
                log.info(f"  {key}: {value}")
                
        if result.get("thumbnail_path"):
            log.info(f"视频缩略图已提取到: {result['thumbnail_path']}")
            
        return result
    else:
        log.error(f"下载失败: {result.get('error')}")
        return None

def test_audio_extraction(video_path):
    """测试音频提取功能"""
    log.info("=" * 50)
    log.info(f"测试音频提取功能 - 视频: {video_path}")
    
    transcription_manager = TranscriptionManager()
    start_time = time.time()
    
    result = transcription_manager.extract_audio(video_path)
    
    elapsed_time = time.time() - start_time
    
    if result["success"]:
        log.success(f"音频提取成功! 用时: {elapsed_time:.2f}秒")
        log.success(f"音频保存到: {result['audio_path']}")
        return result
    else:
        log.error(f"音频提取失败: {result.get('error')}")
        return None

def test_transcription(audio_path, engine, **kwargs):
    """测试转录功能"""
    log.info("=" * 50)
    log.info(f"测试音频转录功能 - 音频: {audio_path}")
    log.info(f"使用引擎: {engine}")
    
    transcription_manager = TranscriptionManager()
    start_time = time.time()
    
    result = transcription_manager.transcribe_audio(audio_path, engine=engine, **kwargs)
    
    elapsed_time = time.time() - start_time
    
    if result["success"]:
        log.success(f"转录成功! 用时: {elapsed_time:.2f}秒")
        log.success(f"文本保存到: {result['text_file_path']}")
        
        if result.get("summary"):
            log.info("文本摘要:")
            log.info(result["summary"])
            
        return result
    else:
        log.error(f"转录失败: {result.get('error')}")
        return None

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 验证参数
    if not validate_args(args):
        return 1
    
    # 执行系统自检
    checker = SelfCheck()
    if not checker.run():
        return 1
    
    # 准备转录参数
    transcription_kwargs = {
        "prompt": args.prompt
    }
    
    if args.engine == "whisper":
        transcription_kwargs["model_size"] = args.model
    elif args.engine == "xunfei":
        if args.xf_appid:
            transcription_kwargs["appid"] = args.xf_appid
        if args.xf_secret:
            transcription_kwargs["secret_key"] = args.xf_secret
    
    # 根据测试模式执行不同的测试
    if args.mode == "download":
        result = test_download(args.bv)
        return 0 if result else 1
        
    elif args.mode == "audio":
        result = test_audio_extraction(args.video)
        return 0 if result else 1
        
    elif args.mode == "transcribe":
        result = test_transcription(args.audio, args.engine, **transcription_kwargs)
        return 0 if result else 1
        
    elif args.mode == "all":
        # 完整流程测试
        total_start_time = time.time()
        
        # 1. 下载视频
        download_result = test_download(args.bv)
        if not download_result:
            return 1
            
        # 2. 提取音频
        audio_result = test_audio_extraction(download_result["video_path"])
        if not audio_result:
            return 1
            
        # 3. 转录音频
        transcription_result = test_transcription(audio_result["audio_path"], args.engine, **transcription_kwargs)
        if not transcription_result:
            return 1
            
        # 计算总时间
        total_elapsed_time = time.time() - total_start_time
        minutes, seconds = divmod(total_elapsed_time, 60)
        
        log.success("=" * 50)
        log.success(f"完整流程测试成功! 总用时: {int(minutes)}分{int(seconds)}秒")
        
        return 0

if __name__ == "__main__":
    sys.exit(main())