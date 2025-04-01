import os
import time
import json
from datetime import datetime

from src.config import *
from src.utils.downloadTools import download_video
from src.utils.videoTools import get_video_info, extract_video_thumbnail

class DownloadManager:
    """视频下载管理器"""
    
    def __init__(self, download_dir=DOWNLOAD_DIR, data_dir=DATA_DIR):
        """
        初始化下载管理器
        
        参数:
            download_dir: 视频下载目录
            data_dir: 数据存储目录
        """
        self.download_dir = download_dir
        self.data_dir = data_dir
        
        # 确保目录存在
        os.makedirs(download_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)
    
    def download_video(self, bv_number):
        """
        下载B站视频
        
        参数:
            bv_number: 视频的BV号
            
        返回:
            包含下载结果的字典
        """
        result = {
            "success": False,
            "bv_number": bv_number,
            "video_path": None,
            "thumbnail_path": None,
            "error": None,
            "video_info": None
        }
        
        if not bv_number:
            result["error"] = "BV号不能为空"
            return result
            
        # 规范化BV号格式
        if not bv_number.startswith("BV"):
            bv_number = "BV" + bv_number
            result["bv_number"] = bv_number
        
        try:
            # 下载视频
            download_result = download_video(bv_number, self.download_dir)
                    
            if not download_result:
                result["error"] = "视频下载失败"
                return result
                
            video_path = os.path.join(self.download_dir, f"{bv_number}.mp4")
            
            if not os.path.exists(video_path):
                result["error"] = f"下载完成但找不到视频文件: {video_path}"
                return result
                
            result["video_path"] = video_path
            result["success"] = True
            
            # 获取视频信息
            video_info = get_video_info(video_path)
            result["video_info"] = video_info
            
            # 提取缩略图
            thumbnail_path = extract_video_thumbnail(
                video_path,
                output_path=os.path.join(self.data_dir, f"{bv_number}_thumbnail.jpg")
            )
            result["thumbnail_path"] = thumbnail_path
            
            return result
            
        except Exception as e:
            result["error"] = f"下载过程中发生错误: {str(e)}"
            return result