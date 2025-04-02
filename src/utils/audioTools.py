from moviepy.editor import VideoFileClip
from pydub import AudioSegment
import os
import time
from src.config import AUDIO_DIR, DOWNLOAD_DIR
import src.log as log

def ensure_audio_dirs():
    """创建音频处理所需的目录。"""
    os.makedirs(os.path.join(AUDIO_DIR, "conv"), exist_ok=True)

def extract_audio_from_video(video_name, target_name=None, video_folder=DOWNLOAD_DIR):
    """
    从视频文件中提取音频并保存为MP3。
    
    参数:
        video_name: 不带扩展名的视频文件名
        target_name: 输出文件的可选名称（默认使用video_name）
        video_folder: 包含视频文件的文件夹
        
    返回:
        创建的MP3文件路径
    """
    ensure_audio_dirs()
    
    # 生成输出文件名
    output_name = target_name if target_name else video_name
    
    # 使用moviepy提取音频
    video_path = f'{video_folder}/{video_name}.mp4'
    log.info(f"从视频提取音频: {video_path}")
    
    try:
        clip = VideoFileClip(video_path)
        audio = clip.audio
        output_path = f"{AUDIO_DIR}/conv/{output_name}.mp3"
        audio.write_audiofile(output_path)
        log.info(f"音频已提取到: {output_path}")
        return output_path
    except Exception as e:
        log.error(f"提取音频时出错: {str(e)}")
        return None

def split_audio(mp3_file, folder_name, slice_length=45000, target_folder=None):
    """
    将MP3文件分割成较小的片段。
    
    参数:
        mp3_file: 要分割的MP3文件路径
        folder_name: 存储片段的文件夹名
        slice_length: 每个片段的长度（毫秒，默认：45秒）
        target_folder: 存储片段的基础文件夹
        
    返回:
        创建的音频片段路径列表
    """
    try:
        if target_folder is None:
            target_folder = os.path.join(AUDIO_DIR, "slice")
            
        # 创建目标目录
        target_dir = os.path.join(target_folder, folder_name)
        os.makedirs(target_dir, exist_ok=True)
        
        # 加载音频文件
        audio = AudioSegment.from_mp3(mp3_file)
        total_length = len(audio)
        total_slices = (total_length + slice_length - 1) // slice_length  # 向上取整
        
        log.info(f"将音频分割为 {total_slices} 个片段...")
        slice_paths = []
        
        # 创建片段
        for i in range(total_slices):
            start = i * slice_length
            end = min(start + slice_length, total_length)
            slice_audio = audio[start:end]
            slice_path = os.path.join(target_dir, f"{i+1}.mp3")
            slice_audio.export(slice_path, format="mp3")
            slice_paths.append(slice_path)
            log.info(f"创建片段 {i+1}/{total_slices}: {slice_path}")
            
        return slice_paths
    except Exception as e:
        log.error(f"分割音频时出错: {str(e)}")
        return []

def process_audio(bv_number):
    """
    处理视频文件：提取音频并分割成片段。
    
    参数:
        bv_number: 视频的BV号
        
    返回:
        包含音频片段的文件夹名
    """
    # 根据时间戳生成唯一的文件夹名
    folder_name = time.strftime('%Y%m%d%H%M%S')
    
    # 从视频中提取音频
    mp3_path = extract_audio_from_video(bv_number, target_name=folder_name)
    
    if mp3_path:
        # 将音频分割成片段
        slice_paths = split_audio(mp3_path, folder_name)
        if slice_paths:
            return folder_name
    
    return None