import os
import json
from datetime import datetime

from src.config import *
from src.download import DownloadManager
from src.transcription import TranscriptionManager
from src.selfcheck import check_dependencies
import src.log as log

class BiliProcessor:
    """B站视频处理核心类，整合下载和转录功能"""
    
    def __init__(self):
        """初始化B站视频处理器"""
        # 检查依赖
        check_dependencies()
        
        # 创建下载和转录管理器
        self.download_manager = DownloadManager()
        self.transcription_manager = TranscriptionManager()
        
        # 确保所有必要的目录存在
        self._ensure_dirs()

        # 进度回调函数
        self.progress_callback = None
    
    def _ensure_dirs(self):
        """确保所有必要的目录存在"""
        dirs = [
            DATA_DIR,
            OUTPUT_DIR,
            DOWNLOAD_DIR,
            AUDIO_DIR,
            os.path.join(AUDIO_DIR, "conv"),
            TRANSCRIPT_DIR,
            THUMBNAIL_DIR,
            META_DIR  # 确保元数据目录存在
        ]
        
        for directory in dirs:
            os.makedirs(directory, exist_ok=True)
    
    def update_progress(self, stage, message, progress=0.0, **extra_info):
        """
        更新进度信息
        
        参数:
            stage: 当前处理阶段 (downloading, extracting, transcribing)
            message: 状态消息
            progress: 当前阶段的进度 (0.0-1.0)
            extra_info: 额外信息
        """
        # 仅在有回调函数时执行
        if self.progress_callback:
            progress_info = {
                "stage": stage,
                "message": message,
                "progress": progress
            }
            progress_info.update(extra_info)
            self.progress_callback(progress_info)
    
    def process_video(self, bv_number, engine=DEFAULT_ENGINE, save_metadata=True, progress_callback=None, **kwargs):
        """
        处理B站视频：下载、提取音频并转录
        
        参数:
            bv_number: 视频的BV号
            engine: 转录引擎 ('whisper' 或 'xunfei')
            save_metadata: 是否保存元数据
            progress_callback: 进度回调函数
            **kwargs: 额外参数传递给转录引擎
            
        返回:
            处理结果字典
        """
        # 设置进度回调
        self.progress_callback = progress_callback
        
        result = {
            "success": False,
            "bv_number": bv_number,
            "steps_completed": [],
            "download_result": None,
            "audio_result": None,
            "transcription_result": None,
            "metadata_path": None,
            "error": None
        }
        
        try:
            # 1. 下载视频
            log.info(f"开始处理视频 BV号: {bv_number}")
            log.info("步骤1: 下载视频")
            
            self.update_progress("downloading", "开始下载视频", 0.0)
            
            # 传递进度回调给下载管理器
            def download_progress_callback(progress_info):
                # 更新下载进度
                self.update_progress("downloading", progress_info.get("message", "下载中..."), 
                                    progress_info.get("progress", 0.0),
                                    download_info=progress_info)
            
            download_result = self.download_manager.download_video(
                bv_number, 
                progress_callback=download_progress_callback
            )
            result["download_result"] = download_result
            
            if not download_result["success"]:
                error_msg = f"视频下载失败: {download_result.get('error')}"
                log.error(error_msg)
                result["error"] = error_msg
                self.update_progress("failed", error_msg, 0.0)
                return result
                
            result["steps_completed"].append("download")
            video_path = download_result["video_path"]
            log.success(f"视频下载成功: {video_path}")
            self.update_progress("downloading", "视频下载完成", 1.0)
            
            # 2. 提取音频
            log.info("步骤2: 从视频中提取音频")
            self.update_progress("extracting", "开始提取音频", 0.0)
            
            # 提取音频进度回调
            def audio_extraction_progress_callback(progress_info):
                self.update_progress("extracting", progress_info.get("message", "提取音频中..."), 
                                    progress_info.get("progress", 0.0),
                                    extraction_info=progress_info)
            
            audio_result = self.transcription_manager.extract_audio(
                video_path,
                progress_callback=audio_extraction_progress_callback
            )
            result["audio_result"] = audio_result
            
            if not audio_result["success"]:
                error_msg = f"音频提取失败: {audio_result.get('error')}"
                log.error(error_msg)
                result["error"] = error_msg
                self.update_progress("failed", error_msg, 0.0)
                return result
                
            result["steps_completed"].append("extract_audio")
            audio_path = audio_result["audio_path"]
            log.success(f"音频提取成功: {audio_path}")
            self.update_progress("extracting", "音频提取完成", 1.0)
            
            # 3. 转录音频
            log.info(f"步骤3: 使用 {engine} 引擎转录音频")
            self.update_progress("transcribing", f"开始使用 {engine} 转录音频", 0.0, engine=engine)
            
            transcription_args = kwargs.copy()
            if "prompt" not in transcription_args:
                transcription_args["prompt"] = DEFAULT_PROMPT
                
            # 转录进度回调
            def transcription_progress_callback(progress_info):
                self.update_progress("transcribing", progress_info.get("message", "转录中..."), 
                                    progress_info.get("progress", 0.0),
                                    transcription_info=progress_info)
            
            transcription_result = self.transcription_manager.transcribe_audio(
                audio_path, 
                engine=engine,
                progress_callback=transcription_progress_callback,
                **transcription_args
            )
            result["transcription_result"] = transcription_result
            
            if not transcription_result["success"]:
                error_msg = f"音频转录失败: {transcription_result.get('error')}"
                log.error(error_msg)
                result["error"] = error_msg
                self.update_progress("failed", error_msg, 0.0)
                return result
                
            result["steps_completed"].append("transcribe")
            log.success("音频转录成功")
            self.update_progress("transcribing", "音频转录完成", 1.0)
            
            # 4. 保存元数据
            if save_metadata:
                log.info("步骤4: 保存处理元数据")
                self.update_progress("metadata", "保存元数据中", 0.5)
                
                # 获取B站视频元数据 - 确保即使元数据为空也能正常处理
                video_metadata = download_result.get("metadata") or {}
                
                # 创建完整的元数据
                metadata = {
                    # 基本视频信息
                    "bv_number": bv_number,
                    "title": video_metadata.get("title", "未知标题"),
                    "author": video_metadata.get("author", "未知作者"),
                    "url": video_metadata.get("url", f"https://www.bilibili.com/video/{bv_number}"),
                    "duration": video_metadata.get("duration") or download_result.get("video_info", {}).get("duration"),
                    "description": video_metadata.get("description", ""),
                    
                    # 处理时间
                    "process_date": datetime.now().isoformat(),
                    
                    # 视频统计信息（在元数据获取失败时使用空值）
                    "stats": {
                        "view_count": video_metadata.get("view_count"),
                        "danmaku_count": video_metadata.get("danmaku_count"),
                        "like_count": video_metadata.get("like_count"),
                        "favorite_count": video_metadata.get("favorite_count"),
                        "coin_count": video_metadata.get("coin_count"),
                        "share_count": video_metadata.get("share_count"),
                        "reply_count": video_metadata.get("reply_count")
                    },
                    
                    # 视频技术信息
                    "video_tech_info": download_result.get("video_info") or {},
                    
                    # 文件路径信息
                    "files": {
                        "video_path": video_path,
                        "audio_path": audio_path,
                        "thumbnail_path": download_result.get("thumbnail_path"),
                        "text_file": transcription_result.get("text_file_path"),
                        "json_file": transcription_result.get("json_file_path")
                    },
                    
                    # 转录信息
                    "transcription": {
                        "engine": engine,
                        "parameters": transcription_args,
                        "summary": transcription_result.get("summary", ""),
                        "model_size": kwargs.get("model_size", "")
                    }
                }
                
                # 保存元数据到指定位置
                metadata_path = os.path.join(META_DIR, f"{bv_number}.json")
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=4)
                
                result["metadata_path"] = metadata_path
                result["steps_completed"].append("save_metadata")
                log.success(f"元数据已保存到: {metadata_path}")
                self.update_progress("metadata", "元数据保存完成", 1.0)
            
            # 最终完成
            result["success"] = True
            log.success(f"视频 {bv_number} 处理完成!")
            self.update_progress("completed", "所有处理步骤已完成", 1.0)
            return result
            
        except Exception as e:
            error_msg = f"处理过程中发生错误: {str(e)}"
            log.error(error_msg)
            result["error"] = error_msg
            self.update_progress("failed", error_msg, 0.0, exception=str(e))
            return result
            
    def get_metadata(self, bv_number):
        """
        获取视频的元数据（如果存在）
        
        参数:
            bv_number: 视频的BV号
            
        返回:
            元数据字典，如果不存在则返回None
        """
        if not bv_number.startswith("BV"):
            bv_number = "BV" + bv_number
            
        metadata_path = os.path.join(META_DIR, f"{bv_number}.json")
        
        if not os.path.exists(metadata_path):
            return None
            
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log.error(f"读取元数据出错: {str(e)}")
            return None
            
    def get_transcription_text(self, bv_number):
        """
        获取视频的转录文本（如果存在）
        
        参数:
            bv_number: 视频的BV号
            
        返回:
            转录文本，如果不存在则返回None
        """
        metadata = self.get_metadata(bv_number)
        
        if not metadata or "files" not in metadata:
            return None
            
        text_file = metadata["files"].get("text_file")
        
        if not text_file or not os.path.exists(text_file):
            return None
            
        try:
            with open(text_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            log.error(f"读取转录文本出错: {str(e)}")
            return None