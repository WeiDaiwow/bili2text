import os
import time
import json
import requests
import subprocess
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
    
    def get_video_metadata_from_api(self, bv_number):
        """
        从API获取B站视频的元数据
        
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
            log.error(f"从API获取视频元数据时出错: {str(e)}")
            return None
            
    def get_video_metadata_from_yt_dlp(self, bv_number):
        """
        使用yt-dlp获取B站视频的元数据
        
        参数:
            bv_number: 视频的BV号
            
        返回:
            包含视频元数据的字典，失败返回None
        """
        if not bv_number.startswith("BV"):
            bv_number = "BV" + bv_number
            
        video_url = f"https://www.bilibili.com/video/{bv_number}"
        
        try:
            log.info("使用yt-dlp获取视频元数据...")
            
            # 使用yt-dlp --dump-json获取视频详细信息
            command = ["yt-dlp", "--dump-json", video_url]
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode != 0:
                log.error(f"使用yt-dlp获取视频信息失败: {result.stderr}")
                return None
                
            # 解析JSON输出
            video_info = json.loads(result.stdout)
            
            # 提取有用信息
            metadata = {
                "bv_number": bv_number,
                "title": video_info.get("title"),
                "author": video_info.get("uploader"),
                "url": video_info.get("webpage_url") or video_url,
                "duration": video_info.get("duration"),
                "description": video_info.get("description"),
                "upload_date": video_info.get("upload_date"),
                "uploader_id": video_info.get("uploader_id"),
                "uploader_url": video_info.get("uploader_url"),
                "view_count": video_info.get("view_count"),
                "like_count": video_info.get("like_count"),
                "comment_count": video_info.get("comment_count"),
                "tags": video_info.get("tags"),
                "categories": video_info.get("categories"),
                "thumbnail": video_info.get("thumbnail"),
                "formats": [
                    {
                        "format_id": f.get("format_id"),
                        "height": f.get("height"),
                        "width": f.get("width"), 
                        "ext": f.get("ext"),
                        "filesize": f.get("filesize")
                    } for f in video_info.get("formats", []) if f.get("format_id")
                ],
                "source": "yt-dlp"
            }
            
            log.success("成功获取视频元数据")
            return metadata
            
        except Exception as e:
            log.error(f"使用yt-dlp获取视频元数据时出错: {str(e)}")
            return None
    
    def get_video_metadata(self, bv_number):
        """
        获取B站视频的元数据，首先尝试使用yt-dlp，如果失败再尝试使用API
        
        参数:
            bv_number: 视频的BV号
            
        返回:
            包含视频元数据的字典，失败返回None
        """
        # 首先尝试使用yt-dlp获取更详细的信息
        metadata = self.get_video_metadata_from_yt_dlp(bv_number)
        
        # 如果yt-dlp失败，尝试使用API
        if not metadata:
            log.info("从API获取视频元数据...")
            metadata = self.get_video_metadata_from_api(bv_number)
            
        return metadata
    
    def download_video(self, bv_number, progress_callback=None):
        """
        下载B站视频
        
        参数:
            bv_number: 视频的BV号
            progress_callback: 进度回调函数，用于更新下载进度
            
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
            # 调用回调函数报告开始获取元数据
            if progress_callback:
                progress_callback({
                    "message": "正在获取视频元数据...",
                    "progress": 0.05,
                    "stage": "metadata"
                })
                
            # 获取视频元数据（标题、作者等）
            video_metadata = self.get_video_metadata(bv_number)
            if video_metadata:
                result["metadata"] = video_metadata
                log.info(f"视频标题: {video_metadata.get('title')}")
                log.info(f"视频作者: {video_metadata.get('author')}")
                
                # 调用回调函数报告元数据获取完成
                if progress_callback:
                    progress_callback({
                        "message": f"元数据获取完成: {video_metadata.get('title')}",
                        "progress": 0.1,
                        "title": video_metadata.get('title'),
                        "author": video_metadata.get('author')
                    })
            else:
                log.warning("无法获取视频元数据，将继续下载但元数据可能不完整")
                
                # 调用回调函数报告元数据获取失败但继续下载
                if progress_callback:
                    progress_callback({
                        "message": "无法获取元数据，继续下载视频...",
                        "progress": 0.1
                    })
            
            # 调用回调函数报告开始下载
            if progress_callback:
                progress_callback({
                    "message": "开始下载视频...",
                    "progress": 0.15
                })
            
            # 下载视频
            download_result = download_video(bv_number, self.download_dir)
            
            # 模拟下载进度
            if progress_callback:
                # 假设下载需要一段时间，分多次报告进度
                for progress in [0.3, 0.5, 0.7, 0.9]:
                    time.sleep(0.5)  # 模拟下载延迟
                    progress_callback({
                        "message": f"视频下载中... {int(progress * 100)}%",
                        "progress": progress
                    })
                    
            if not download_result:
                result["error"] = "视频下载失败"
                if progress_callback:
                    progress_callback({
                        "message": "视频下载失败",
                        "progress": 0.0,
                        "error": True
                    })
                return result
                
            video_path = os.path.join(self.download_dir, f"{bv_number}.mp4")
            
            if not os.path.exists(video_path):
                result["error"] = f"下载完成但找不到视频文件: {video_path}"
                if progress_callback:
                    progress_callback({
                        "message": f"下载完成但找不到视频文件: {video_path}",
                        "progress": 0.0,
                        "error": True
                    })
                return result
                
            result["video_path"] = video_path
            result["success"] = True
            
            # 调用回调函数报告下载完成
            if progress_callback:
                progress_callback({
                    "message": "视频下载完成，正在获取视频信息...",
                    "progress": 0.95,
                    "video_path": video_path
                })
            
            # 获取视频技术信息（时长、分辨率等）
            video_tech_info = get_video_info(video_path)
            result["video_info"] = video_tech_info
            
            # 提取缩略图
            thumbnail_path = extract_video_thumbnail(
                video_path,
                output_path=os.path.join(self.thumbnail_dir, f"{bv_number}_thumbnail.jpg")
            )
            result["thumbnail_path"] = thumbnail_path
            
            # 调用回调函数报告全部完成
            if progress_callback:
                progress_callback({
                    "message": "视频下载和处理完成",
                    "progress": 1.0,
                    "video_path": video_path,
                    "thumbnail_path": thumbnail_path,
                    "video_info": video_tech_info
                })
            
            return result
            
        except Exception as e:
            error_message = f"下载过程中发生错误: {str(e)}"
            result["error"] = error_message
            
            # 报告错误
            if progress_callback:
                progress_callback({
                    "message": error_message,
                    "progress": 0.0,
                    "error": True,
                    "exception": str(e)
                })
                
            return result