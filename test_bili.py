#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试脚本 - 用于测试B站视频下载和转录功能
"""

import os
import sys
import argparse
import time

# 将项目根目录添加到模块搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import BiliProcessor
from src.config import *
import src.log as log
from src.selfcheck import SelfCheck

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="B站视频下载和转录测试")
    
    # 添加必要的参数
    parser.add_argument("bv_number", help="B站视频的BV号")
    
    # 添加可选参数
    parser.add_argument("--engine", choices=["whisper", "xunfei"], default=DEFAULT_ENGINE,
                         help="转录引擎: whisper 或 xunfei，默认使用配置文件中的设置")
    parser.add_argument("--model", choices=["tiny", "base", "small", "medium", "large"], default=DEFAULT_MODEL,
                         help="Whisper模型大小 (仅当使用whisper引擎时有效)")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT,
                         help="转录提示词，用于指导转录引擎")
    parser.add_argument("--no-metadata", action="store_true",
                         help="不保存处理元数据")
    
    # 讯飞API参数
    parser.add_argument("--xf-appid", help="讯飞API的应用ID (仅当使用xunfei引擎时必需)")
    parser.add_argument("--xf-secret", help="讯飞API的密钥 (仅当使用xunfei引擎时必需)")
    
    return parser.parse_args()

def validate_args(args):
    """验证命令行参数"""
    # 检查BV号格式
    if not args.bv_number:
        log.error("请提供有效的BV号")
        return False
        
    # 如果使用讯飞引擎，检查是否提供了API密钥
    if args.engine == "xunfei":
        if not (args.xf_appid and args.xf_secret) and not (XUNFEI_APP_ID and XUNFEI_SECRET_KEY):
            log.error("使用讯飞引擎需要提供应用ID和密钥")
            log.info("您可以在命令行使用 --xf-appid 和 --xf-secret 参数提供")
            log.info("或者在config.py文件中配置XUNFEI_APP_ID和XUNFEI_SECRET_KEY")
            return False
    
    return True

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
        
    # 初始化处理器
    processor = BiliProcessor()
    
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
    
    # 开始处理
    start_time = time.time()
    log.info(f"开始处理视频: {args.bv_number}")
    log.info(f"使用转录引擎: {args.engine}")
    
    # 执行处理
    result = processor.process_video(
        args.bv_number,
        engine=args.engine,
        save_metadata=not args.no_metadata,
        **transcription_kwargs
    )
    
    # 处理结果
    if result["success"]:
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(elapsed_time, 60)
        
        log.success("=" * 50)
        log.success(f"处理成功! 总用时: {int(minutes)}分{int(seconds)}秒")
        
        if result["transcription_result"] and result["transcription_result"].get("text_file_path"):
            text_file = result["transcription_result"]["text_file_path"]
            log.success(f"转录文本已保存到: {text_file}")
            
            # 显示摘要
            if result["transcription_result"].get("summary"):
                log.info("文本摘要:")
                log.info(result["transcription_result"]["summary"])
        
        if result.get("metadata_path"):
            log.success(f"元数据已保存到: {result['metadata_path']}")
            
        return 0
    else:
        log.error("=" * 50)
        log.error(f"处理失败: {result.get('error')}")
        log.error(f"已完成步骤: {', '.join(result['steps_completed']) if result['steps_completed'] else '无'}")
        return 1

if __name__ == "__main__":
    sys.exit(main())