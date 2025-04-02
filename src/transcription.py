import os
import time
import json
from datetime import datetime

from src.config import *
from src.utils.audioTools import extract_audio_from_video
from src.utils.textTools import transcribe_file, get_transcriber
import src.log as log

class TranscriptionManager:
    """音频提取和转录管理器"""
    
    def __init__(self, audio_dir=AUDIO_DIR, transcript_dir=TRANSCRIPT_DIR):
        """
        初始化转录管理器
        
        参数:
            audio_dir: 音频文件目录
            transcript_dir: 文本转录结果目录
        """
        self.audio_dir = audio_dir
        self.transcript_dir = transcript_dir
        
        # 确保目录存在
        os.makedirs(os.path.join(audio_dir, "conv"), exist_ok=True)
        os.makedirs(transcript_dir, exist_ok=True)
    
    def extract_audio(self, video_path, output_name=None):
        """
        从视频中提取音频
        
        参数:
            video_path: 视频文件路径
            output_name: 输出音频的文件名(不含扩展名)
            
        返回:
            包含结果的字典
        """
        result = {
            "success": False,
            "video_path": video_path,
            "audio_path": None,
            "error": None
        }
        
        if not os.path.exists(video_path):
            result["error"] = f"视频文件不存在: {video_path}"
            return result
        
        try:
            # 生成输出文件名
            if not output_name:
                # 从视频路径提取文件名，并添加时间戳
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                timestamp = time.strftime('%Y%m%d%H%M%S')
                output_name = f"{base_name}_{timestamp}"
            
            log.info(f"开始从视频提取音频: {os.path.basename(video_path)}")
            
            # 获取视频所在目录
            video_dir = os.path.dirname(video_path)
            
            # 提取音频
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            video_folder = video_dir
            
            audio_path = extract_audio_from_video(video_name, output_name, video_folder)
            
            if not audio_path or not os.path.exists(audio_path):
                result["error"] = "音频提取失败"
                return result
            
            result["audio_path"] = audio_path
            result["success"] = True
            log.success(f"音频提取成功: {audio_path}")
            return result
            
        except Exception as e:
            error_msg = f"音频提取过程中发生错误: {str(e)}"
            log.error(error_msg)
            result["error"] = error_msg
            return result
    
    def transcribe_audio(self, audio_path, engine=DEFAULT_ENGINE, prompt=DEFAULT_PROMPT, **kwargs):
        """
        将音频转录为文本
        
        参数:
            audio_path: 音频文件路径
            engine: 转录引擎 ('whisper' 或 'xunfei')
            prompt: 转录提示词
            **kwargs: 额外的转录参数
            
        返回:
            包含结果的字典
        """
        result = {
            "success": False,
            "audio_path": audio_path,
            "text_file_path": None,
            "json_file_path": None,
            "summary": None,
            "engine": engine,
            "error": None
        }
        
        if not os.path.exists(audio_path):
            result["error"] = f"音频文件不存在: {audio_path}"
            return result
        
        try:
            # 设置转录引擎参数
            log.info(f"开始使用 {engine} 引擎转录音频: {os.path.basename(audio_path)}")
            transcription_args = {"prompt": prompt}
            transcription_args.update(kwargs)
            
            if engine == "whisper":
                # Whisper特有参数
                if "model_size" not in transcription_args:
                    transcription_args["model_size"] = DEFAULT_MODEL
                log.info(f"使用Whisper模型: {transcription_args.get('model_size', DEFAULT_MODEL)}")
            elif engine == "xunfei":
                # 讯飞特有参数
                if "appid" not in transcription_args and XUNFEI_APP_ID:
                    transcription_args["appid"] = XUNFEI_APP_ID
                if "secret_key" not in transcription_args and XUNFEI_SECRET_KEY:
                    transcription_args["secret_key"] = XUNFEI_SECRET_KEY
                
                if not (transcription_args.get("appid") and transcription_args.get("secret_key")):
                    result["error"] = "使用讯飞API需要提供appid和secret_key"
                    return result
                log.info("使用讯飞API进行转录")
            
            # 执行转录
            log.info("开始转录过程，请耐心等待...")
            text = transcribe_file(audio_path, engine=engine, **transcription_args)
            
            if not text:
                result["error"] = "转录失败，未获得文本"
                return result
            
            # 生成输出文件名
            base_name = os.path.splitext(os.path.basename(audio_path))[0]
            timestamp = time.strftime('%Y%m%d%H%M%S')
            
            # 确保输出目录存在
            os.makedirs(self.transcript_dir, exist_ok=True)
            
            # 保存为文本文件
            text_filename = f"{base_name}_{timestamp}.txt"
            text_file_path = os.path.join(self.transcript_dir, text_filename)
            
            with open(text_file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            log.info(f"转录文本已保存到: {text_file_path}")
            
            # 保存为JSON文件
            json_data = {
                "audio": audio_path,
                "engine": engine,
                "timestamp": datetime.now().isoformat(),
                "parameters": transcription_args,
                "text": text
            }
            
            json_filename = f"{base_name}_{timestamp}.json"
            json_file_path = os.path.join(self.transcript_dir, json_filename)
            
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            
            log.info(f"转录JSON数据已保存到: {json_file_path}")
            
            # 创建摘要
            summary = text[:50] + "..." if len(text) > 50 else text
            
            # 设置结果
            result["success"] = True
            result["text_file_path"] = text_file_path
            result["json_file_path"] = json_file_path
            result["summary"] = summary
            
            log.success("音频转录完成")
            return result
            
        except Exception as e:
            error_msg = f"转录过程中发生错误: {str(e)}"
            log.error(error_msg)
            result["error"] = error_msg
            return result