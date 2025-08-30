import os
import subprocess
import time

from moviepy import VideoFileClip
from pydub import AudioSegment


def check_video_integrity(file_path):
    """使用 FFmpeg 验证视频文件完整性"""
    result = subprocess.run(
        ['ffmpeg', '-v', 'error', '-i', file_path, '-f', 'null', '-'],
        stderr=subprocess.PIPE,
        text=True
    )
    if result.stderr:
        print(f"视频文件可能损坏: {file_path}")
        print(f"FFmpeg 错误信息: {result.stderr}")
        return False
    return True

def convert_flv_to_mp3(input_path, out_folder = "audio/conv"):
    basename = os.path.basename(input_path)
    name, _ = os.path.splitext(basename)
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"视频文件不存在: {input_path}")
    if not check_video_integrity(input_path):
        raise ValueError(f"视频文件损坏: {input_path}")
    # 提取视频中的音频并保存为 MP3 到 audio/conv 目录
    clip = VideoFileClip(input_path)
    audio = clip.audio
    os.makedirs(out_folder, exist_ok=True)
    out_path = os.path.join(out_folder, f"{name}.mp3")
    #check if file exists
    if not os.path.exists(out_path):
        print(f"正在转换视频为音频: {input_path} -> {out_path}")
        audio.write_audiofile(out_path)
    else:
        print(f"音频文件已存在: {out_path}")
    return out_path

def split_mp3(filename, folder_name, slice_length=45000, target_folder="audio/slice"):
    audio = AudioSegment.from_mp3(filename)
    total_slices = (len(audio)+ slice_length - 1) // slice_length
    target_dir = os.path.join(target_folder, folder_name)
    if os.path.exists(target_dir):
        #check whether .mp3 files exist
        existing_files = [f for f in os.listdir(target_dir) if f.endswith(".mp3")]
        if existing_files:
            print(f"已存在音频切片: {existing_files}")
            return existing_files
    else:
        os.makedirs(target_dir, exist_ok=True)
        for i in range(total_slices):
            start = i * slice_length
            end = start + slice_length
            slice_audio = audio[start:end]
            slice_path = os.path.join(target_dir, f"{i+1}.mp3")
            slice_audio.export(slice_path, format="mp3")
            print(f"Slice {i+1} saved: {slice_path}")
        existing_files = [f for f in os.listdir(target_dir) if f.endswith(".mp3")]
        return existing_files

def process_audio_split(name):
    # 生成唯一文件夹名，并依次调用转换和分割函数
    basename = os.path.basename(name)
    out_name, _ = os.path.splitext(basename)
    audio_file = convert_flv_to_mp3(name)
    slice_list = split_mp3(audio_file, out_name, slice_length= 25000)
    return out_name 

