import os
import subprocess
import re
from datetime import timedelta
from src.config import THUMBNAIL_DIR
import src.log as log

def get_video_info(video_path):
    """
    使用ffprobe获取视频文件信息。
    
    参数:
        video_path: 视频文件路径
        
    返回:
        包含视频元数据的字典（时长、分辨率等）
    """
    try:
        # 获取视频时长
        cmd = [
            'ffprobe', 
            '-v', 'error', 
            '-show_entries', 'format=duration', 
            '-of', 'default=noprint_wrappers=1:nokey=1', 
            video_path
        ]
        duration = float(subprocess.check_output(cmd).decode('utf-8').strip())
        
        # 获取视频分辨率
        cmd = [
            'ffprobe', 
            '-v', 'error', 
            '-select_streams', 'v:0', 
            '-show_entries', 'stream=width,height', 
            '-of', 'csv=s=x:p=0', 
            video_path
        ]
        resolution = subprocess.check_output(cmd).decode('utf-8').strip()
        
        # 获取视频编码
        cmd = [
            'ffprobe', 
            '-v', 'error', 
            '-select_streams', 'v:0', 
            '-show_entries', 'stream=codec_name', 
            '-of', 'default=noprint_wrappers=1:nokey=1', 
            video_path
        ]
        codec = subprocess.check_output(cmd).decode('utf-8').strip()
        
        # 格式化时长为 HH:MM:SS
        formatted_duration = str(timedelta(seconds=int(duration)))
        
        return {
            'duration': duration,
            'formatted_duration': formatted_duration,
            'resolution': resolution,
            'codec': codec,
            'file_size': os.path.getsize(video_path)
        }
    except Exception as e:
        log.error(f"获取视频信息出错: {str(e)}")
        return {}

def extract_video_thumbnail(video_path, output_path=None, time_offset=5):
    """
    在特定时间点从视频中提取缩略图。
    
    参数:
        video_path: 视频文件路径
        output_path: 保存缩略图的路径（默认为视频文件名加.jpg扩展名）
        time_offset: 提取缩略图的时间点（秒）
        
    返回:
        提取的缩略图路径
    """
    if output_path is None:
        # 默认缩略图路径
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(THUMBNAIL_DIR, f"{base_name}_thumbnail.jpg")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        # 格式化时间偏移
        time_str = str(timedelta(seconds=time_offset))
        if '.' not in time_str:
            time_str += '.0'
        
        # 提取缩略图
        cmd = [
            'ffmpeg',
            '-y',  # 如果文件存在则覆盖
            '-ss', time_str,  # 时间偏移
            '-i', video_path,  # 输入文件
            '-vframes', '1',  # 提取一帧
            '-q:v', '2',  # 质量级别（越低越好）
            output_path
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log.info(f"缩略图已提取到: {output_path}")
        
        return output_path
    except Exception as e:
        log.error(f"提取缩略图出错: {str(e)}")
        return None

def extract_subtitle(video_path, output_path=None, language='chi'):
    """
    从视频中提取字幕（如果有）。
    
    参数:
        video_path: 视频文件路径
        output_path: 保存字幕的路径（默认为视频文件名加.srt扩展名）
        language: 要提取的语言代码（默认：'chi'，中文）
        
    返回:
        提取的字幕文件路径，如果没有找到字幕则返回None
    """
    if output_path is None:
        # 默认字幕路径
        base_name = os.path.splitext(video_path)[0]
        output_path = f"{base_name}.srt"
    
    try:
        # 检查视频是否包含字幕
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 's',
            '-show_entries', 'stream=index:stream_tags=language',
            '-of', 'csv=p=0',
            video_path
        ]
        
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8')
        
        if not result.strip():
            log.info("视频中未找到字幕")
            return None
            
        # 提取字幕
        cmd = [
            'ffmpeg',
            '-y',  # 如果文件存在则覆盖
            '-i', video_path,  # 输入文件
            '-map', '0:s:0',  # 选择第一个字幕流
            output_path
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            log.info(f"字幕已提取到: {output_path}")
            return output_path
        else:
            return None
    except Exception as e:
        log.error(f"提取字幕出错: {str(e)}")
        return None

def cut_video(video_path, output_path, start_time, end_time=None, duration=None):
    """
    从视频文件中剪切片段。
    
    参数:
        video_path: 输入视频文件路径
        output_path: 保存输出视频的路径
        start_time: 开始时间（秒）或'HH:MM:SS'格式的字符串
        end_time: 结束时间（秒）或'HH:MM:SS'格式的字符串（与duration互斥）
        duration: 持续时间（秒）（与end_time互斥）
        
    返回:
        输出视频文件路径
    """
    # 如果开始时间是数字，格式化为时间字符串
    if isinstance(start_time, (int, float)):
        start_time = str(timedelta(seconds=start_time))
    
    try:
        cmd = [
            'ffmpeg',
            '-y',  # 如果文件存在则覆盖
            '-ss', start_time,  # 开始时间
            '-i', video_path,  # 输入文件
        ]
        
        # 添加结束时间或持续时间
        if end_time is not None:
            if isinstance(end_time, (int, float)):
                end_time = str(timedelta(seconds=end_time))
            cmd.extend(['-to', end_time])
        elif duration is not None:
            cmd.extend(['-t', str(duration)])
        
        # 添加输出文件
        cmd.extend([
            '-c', 'copy',  # 复制流而不重新编码
            output_path
        ])
        
        log.info(f"开始剪切视频: {video_path} -> {output_path}")
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log.success(f"视频剪切完成: {output_path}")
        
        return output_path if os.path.exists(output_path) else None
    except Exception as e:
        log.error(f"剪切视频出错: {str(e)}")
        return None