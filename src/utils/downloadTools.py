import os
import subprocess
import glob
import requests
import sys
import time
from src.config import DOWNLOAD_DIR, DOWNLOAD_TOOL
import src.log as log

# 用于向B站API发送HTTP请求的请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/55.0.2883.87 Safari/537.36'
}

def ensure_folders_exist(folders):
    """创建必要的文件夹（如果不存在）。"""
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)

def download_video_you_get(bv_number, output_dir=DOWNLOAD_DIR):
    """
    使用you-get工具下载B站视频。
    
    参数:
        bv_number: B站视频BV号（可以带或不带"BV"前缀）
        output_dir: 视频保存目录
        
    返回:
        BV号（用于后续处理）
    """
    if not bv_number.startswith("BV"):
        bv_number = "BV" + bv_number
        
    video_url = f"https://www.bilibili.com/video/{bv_number}"
    ensure_folders_exist([output_dir])
    log.info(f"使用you-get下载视频: {video_url}")
    
    try:
        result = subprocess.run(["you-get", "-o", output_dir, video_url], capture_output=True, text=True)
        if result.returncode != 0:
            log.error(f"下载失败: {result.stderr}")
        else:
            log.info(result.stdout)
            log.success(f"视频成功下载到目录: {output_dir}")
            # 重命名下载的视频文件，假设是最新的.mp4文件
            video_files = glob.glob(os.path.join(output_dir, "*.mp4"))
            if video_files:
                latest_file = max(video_files, key=os.path.getmtime)
                file_path = f"{output_dir}/{bv_number}.mp4"
                os.rename(latest_file, file_path)
                # 删除xml文件
                xml_files = glob.glob(os.path.join(output_dir, "*.xml"))
                for xml_file in xml_files:
                    os.remove(xml_file)
            else:
                log.error("下载后未找到视频文件")
    except Exception as e:
        log.error(f"发生错误: {str(e)}")
        
    return bv_number

def download_video_api(bv_number, output_dir=DOWNLOAD_DIR):
    """
    使用直接API请求下载B站视频。
    
    参数:
        bv_number: B站视频BV号（可以带或不带"BV"前缀）
        output_dir: 视频保存目录
        
    返回:
        BV号（用于后续处理）
    """
    if not bv_number.startswith("BV"):
        bv_number = "BV" + bv_number
        
    try:
        # 获取视频元数据
        meta_url = f"https://bili.zhouql.vip/meta/{bv_number}"
        meta_response = requests.get(meta_url)
        meta_data = meta_response.json()
        
        if meta_data.get("code") != 0:
            log.error(f"元数据请求失败: {meta_data.get('message')}")
            return None
            
        cid = meta_data["data"]["cid"]
        aid = meta_data["data"]["aid"]
        log.info(f"获取到的cid: {cid}, aid: {aid}")

        # 获取下载URL
        download_url = f"https://bili.zhouql.vip/download/{aid}/{cid}"
        download_response = requests.get(download_url)
        download_data = download_response.json()
        
        if download_data.get("code") != 0:
            log.error(f"下载链接请求失败: {download_data.get('message')}")
            return None
            
        video_url = download_data["data"]["durl"][0]["url"]
        log.info(f"视频下载链接: {video_url}")

        # 下载视频文件
        ensure_folders_exist([output_dir])
        file_path = f"{output_dir}/{bv_number}.mp4"
        video_response = requests.get(video_url, stream=True, headers=HEADERS)
        total_size = int(video_response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(file_path, "wb") as wf:
            for chunk in video_response.iter_content(chunk_size=1024):
                if chunk:
                    wf.write(chunk)
                    downloaded_size += len(chunk)
                    percent_complete = downloaded_size / total_size * 100
                    progress = int(percent_complete // 2)
                    sys.stdout.write(f"\r下载进度: [{'#' * progress}{' ' * (50 - progress)}] {percent_complete:.2f}%")
                    sys.stdout.flush()
                    
        log.success(f"\n视频成功下载到: {file_path}")
        return bv_number
        
    except Exception as e:
        log.error(f"发生错误: {str(e)}")
        return None


def download_video_yt_dlp(bv_number, output_dir=DOWNLOAD_DIR):
    """
    使用yt-dlp工具下载B站视频。
    
    参数:
        bv_number: B站视频BV号（可以带或不带"BV"前缀）
        output_dir: 视频保存目录
        
    返回:
        BV号（用于后续处理）
    """
    if not bv_number.startswith("BV"):
        bv_number = "BV" + bv_number
        
    video_url = f"https://www.bilibili.com/video/{bv_number}"
    ensure_folders_exist([output_dir])
    file_path = f"{output_dir}/{bv_number}.mp4"
    
    log.info(f"使用yt-dlp下载视频: {video_url}")
    
    try:
        # 使用yt-dlp下载视频，指定输出文件名和格式
        command = [
            "yt-dlp", 
            "-o", file_path,
            "--merge-output-format", "mp4",
            video_url
        ] # TODO: 其实yt-dlp可以直接下载音频，但为了保持一致性，先不做特殊处理，还是从视频中分割
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            log.error(f"下载失败: {result.stderr}")
        else:
            log.success(f"视频成功下载到: {file_path}")
            
    except Exception as e:
        log.error(f"发生错误: {str(e)}")
        
    return bv_number

# 默认视频下载函数，使用首选方法
if DOWNLOAD_TOOL == "api":
    download_video = download_video_api
elif DOWNLOAD_TOOL == "you-get":
    download_video = download_video_you_get
elif DOWNLOAD_TOOL == "yt-dlp":
    download_video = download_video_yt_dlp
else:
    log.warning(f"未知下载工具: {DOWNLOAD_TOOL}，使用默认的YT-DLP下载")
    download_video = download_video_yt_dlp