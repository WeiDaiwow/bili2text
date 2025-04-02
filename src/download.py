import os
import time
import json
import requests
from datetime import datetime

from src.config import *
from src.utils.downloadTools import download_video
from src.utils.videoTools import get_video_info, extract_video_thumbnail
import src.log as log

class DownloadManager:
    """视频下载管理器"""
    
    def __init__(self, download_dir=DOWNLOAD_DIR, thumbnail_dir=THUMBNAIL_DIR):
        """
        初始化下载管理器
        
        参数:
            download_dir: 视频下载目录
            thumbnail_dir: 缩略图存储目录
        """
        self.download_dir = download_dir
        self.thumbnail_dir = thumbnail_dir
        
        # 确保目录存在
        os.makedirs(download_dir, exist_ok=True)
        os.makedirs(thumbnail_dir, exist_ok=True)
    
    def get_video_metadata(self, bv_number):
        """
        获取B站视频的元数据（标题、作者等信息）
        
        参数:
            bv_number: 视频的BV号
            
        返回:
            包含视频元数据的字典，失败返回None
        """
        if not bv_number.startswith("BV"):
            bv_number = "BV" + bv_number
            
        try:
            # 通过API获取视频信息
            meta_url = f"https://bili.zhouql.vip/meta/{bv_number}"
            response = requests.get(meta_url)
            data = response.json()
            
            if data.get("code") != 0:
                log.error(f"获取视频元数据失败: {data.get('message')}")
                return None
                
            # 提取需要的信息
            video_data = data.get("data", {})
            return {
                "bv_number": bv_number,
                "title": video_data.get("title"),
                "author": video_data.get("owner", {}).get("name"),
                "url": f"https://www.bilibili.com/video/{bv_number}",
                "duration": video_data.get("duration"),
                "cid": video_data.get("cid"),
                "aid": video_data.get("aid"),
                "created_at": datetime.fromtimestamp(video_data.get("pubdate", 0)).isoformat() if video_data.get("pubdate") else None,
                "description": video_data.get("desc"),
                "view_count": video_data.get("stat", {}).get("view"),
                "danmaku_count": video_data.get("stat", {}).get("danmaku"),
                "reply_count": video_data.get("stat", {}).get("reply"),
                "favorite_count": video_data.get("stat", {}).get("favorite"),
                "coin_count": video_data.get("stat", {}).get("coin"),
                "share_count": video_data.get("stat", {}).get("share"),
                "like_count": video_data.get("stat", {}).get("like")
            }
        except Exception as e:
            log.error(f"获取视频元数据时出错: {str(e)}")
            return None
    
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
            "video_info": None,
            "metadata": None
        }
        
        if not bv_number:
            result["error"] = "BV号不能为空"
            return result
            
        # 规范化BV号格式
        if not bv_number.startswith("BV"):
            bv_number = "BV" + bv_number
            result["bv_number"] = bv_number
        
        try:
            # 获取视频元数据（标题、作者等）
            video_metadata = self.get_video_metadata(bv_number)
            if video_metadata:
                result["metadata"] = video_metadata
                log.info(f"视频标题: {video_metadata.get('title')}")
                log.info(f"视频作者: {video_metadata.get('author')}")
            
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
            
            # 获取视频技术信息（时长、分辨率等）
            video_tech_info = get_video_info(video_path)
            result["video_info"] = video_tech_info
            
            # 提取缩略图
            thumbnail_path = extract_video_thumbnail(
                video_path,
                output_path=os.path.join(self.thumbnail_dir, f"{bv_number}_thumbnail.jpg")
            )
            result["thumbnail_path"] = thumbnail_path
            
            return result
            
        except Exception as e:
            result["error"] = f"下载过程中发生错误: {str(e)}"
            return result