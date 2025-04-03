from flask import Flask, request, jsonify, send_file, render_template, abort
import threading
import time
import os
import sys
import json
from datetime import datetime

# 将项目根目录添加到模块搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import BiliProcessor
from src.config import *
import src.log as log
from src.webserver.db.service import DatabaseService

app = Flask(__name__, 
            static_folder="static",
            template_folder="templates")

# 初始化数据库服务
db_service = DatabaseService(DATABASE_PATH)

# 初始化处理器
processor = BiliProcessor()

# 存储后台运行的任务
active_tasks = {}

# 处理阶段及其进度权重
processing_stages = {
    "downloading": {"name": "正在下载视频", "weight": 0.3},
    "extracting": {"name": "正在提取音频", "weight": 0.1},
    "transcribing": {"name": "正在转录音频", "weight": 0.6},
    "metadata": {"name": "正在处理元数据", "weight": 0.0}  # 元数据阶段权重较小
}

# API路由 - 视频转录
@app.route('/api/transcribe', methods=['POST'])
def transcribe_video():
    """提交视频转录任务"""
    data = request.json
    
    if not data or 'bv_number' not in data:
        return jsonify({"success": False, "error": "缺少BV号"}), 400
    
    bv_number = data['bv_number']
    engine = data.get('engine', DEFAULT_ENGINE)
    model_size = data.get('model_size', DEFAULT_MODEL)
    
    # 检查是否已经存在该BV号的记录
    existing_video = db_service.get_video(bv_number=bv_number)
    if existing_video and existing_video.get('status') == 'transcribed':
        return jsonify({
            "success": True, 
            "message": "该视频已经转录过", 
            "video_id": existing_video['id'],
            "status": "completed"
        }), 200
    
    # 创建任务ID
    task_id = f"{bv_number}_{int(time.time())}"
    
    # 在数据库中创建一个处理中的记录
    video_id = db_service.add_video(
        bv_number=bv_number,
        video_path="", # 暂时为空，稍后更新
        title=f"转录中... ({bv_number})",
        status="processing"
    )
    
    # 初始化任务状态
    active_tasks[task_id] = {
        "status": "processing",
        "stage": "downloading",  # 初始阶段为下载
        "stage_name": processing_stages["downloading"]["name"],
        "stage_start_time": time.time(),
        "start_time": time.time(),
        "progress": 0.0,
        "video_id": video_id,
        "message": "任务初始化中",
        "details": {}
    }
    
    # 启动异步处理任务
    thread = threading.Thread(
        target=process_video_async,
        args=(bv_number, engine, model_size, task_id, video_id)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "success": True, 
        "message": "转录任务已提交", 
        "task_id": task_id,
        "video_id": video_id,
        "status": "processing",
        "stage": "downloading",
        "stage_name": processing_stages["downloading"]["name"]
    }), 202

@app.route('/api/task/<task_id>', methods=['GET'])
def check_task_status(task_id):
    """检查任务状态"""
    if task_id not in active_tasks:
        # 如果任务不在活动列表中，检查数据库
        # 可能是已完成的任务
        if "_" in task_id:
            bv_number = task_id.split("_")[0]
            video = db_service.get_video(bv_number=bv_number)
            if video:
                return jsonify({
                    "success": True,
                    "status": video['status'],
                    "video_id": video['id'],
                    "progress": 1.0 if video['status'] == 'transcribed' else 0.0
                }), 200
        
        return jsonify({"success": False, "error": "任务不存在"}), 404
    
    # 返回当前任务状态，不再需要计算模拟进度
    task = active_tasks[task_id]
    elapsed_time = time.time() - task["start_time"]
    
    response_data = {
        "success": True,
        "status": task["status"],
        "stage": task["stage"],
        "stage_name": task["stage_name"],
        "message": task["message"],
        "elapsed_time": elapsed_time,
        "progress": task["progress"],
        "video_id": task["video_id"]
    }
    
    # 添加详细信息（如果有）
    if task.get("details"):
        response_data["details"] = task["details"]
    
    return jsonify(response_data), 200

@app.route('/api/transcriptions', methods=['GET'])
def get_all_transcriptions():
    """获取所有转录记录，支持标签过滤"""
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    tag_id = request.args.get('tag_id', type=int)
    
    # 获取视频列表
    videos, total_count = db_service.get_all_videos(limit=limit, offset=offset, tag_id=tag_id)
    
    formatted_videos = []
    for video in videos:
        # 获取视频对应的最新转录
        transcription = db_service.get_transcription(video_id=video['id'], latest=True)
        
        # 整理返回数据
        formatted_video = {
            "id": video['id'],
            "bv_number": video['bv_number'],
            "title": video['title'],
            "author": video['author'],
            "thumbnail_path": video['thumbnail_path'],
            "download_date": video['download_date'],
            "status": video['status'],
            "duration": video['duration'],
            "resolution": video['resolution'],
            "tags": video.get('tags', []),
            "model_size": video.get('metadata', {}).get("transcription", {}).get("model_size", ""),
            "transcription": {
                "id": transcription['id'] if transcription else None,
                "engine": transcription['engine'] if transcription else None,
                "date": transcription['transcription_date'] if transcription else None,
                "excerpt": transcription['text'][:100] + "..." if transcription and len(transcription['text']) > 100 else transcription['text'] if transcription else None
            } if transcription else None
        }
        formatted_videos.append(formatted_video)
    
    return jsonify({
        "success": True,
        "total": total_count,
        "videos": formatted_videos
    }), 200

@app.route('/api/transcriptions/recent', methods=['GET'])
def get_recent_transcriptions():
    """获取最近的转录记录"""
    limit = request.args.get('limit', 5, type=int)
    
    # 获取最近的视频
    videos, _ = db_service.get_all_videos(limit=limit, order_by="download_date DESC")
    
    formatted_videos = []
    for video in videos:
        # 获取视频对应的最新转录
        transcription = db_service.get_transcription(video_id=video['id'], latest=True)
        
        # 整理返回数据
        formatted_video = {
            "id": video['id'],
            "bv_number": video['bv_number'],
            "title": video['title'],
            "author": video['author'],
            "thumbnail_path": video['thumbnail_path'],
            "download_date": video['download_date'],
            "status": video['status'],
            "tags": video.get('tags', []),
            "model_size": video.get('metadata', {}).get("transcription", {}).get("model_size", ""),
            "transcription": {
                "id": transcription['id'] if transcription else None,
                "engine": transcription['engine'] if transcription else None,
                "date": transcription['transcription_date'] if transcription else None,
                "excerpt": transcription['text'][:100] + "..." if transcription and len(transcription['text']) > 100 else transcription['text'] if transcription else None
            } if transcription else None
        }
        formatted_videos.append(formatted_video)
    
    return jsonify({
        "success": True,
        "videos": formatted_videos
    }), 200

@app.route('/api/transcription/<int:video_id>', methods=['GET'])
def get_transcription_detail(video_id):
    """获取特定转录详情"""
    # 获取视频记录
    video = db_service.get_video(video_id=video_id)
    if not video:
        return jsonify({"success": False, "error": "视频不存在"}), 404
    
    # 获取最新转录
    transcription = db_service.get_transcription(video_id=video_id, latest=True)
    if not transcription and video['status'] == 'transcribed':
        return jsonify({"success": False, "error": "转录记录不存在"}), 404
    
    # 解析元数据JSON
    metadata = {}
    if video.get('metadata') and isinstance(video['metadata'], str):
        try:
            metadata = json.loads(video['metadata'])
        except json.JSONDecodeError:
            pass
    
    # 获取视频标签
    tags = db_service.get_video_tags(video_id)
    
    # 整理视频详情
    video_detail = {
        "id": video['id'],
        "bv_number": video['bv_number'],
        "title": video['title'],
        "author": video['author'],
        "url": f"https://www.bilibili.com/video/{video['bv_number']}",
        "thumbnail_path": video['thumbnail_path'],
        "video_path": video['video_path'],
        "audio_path": video['audio_path'],
        "download_date": video['download_date'],
        "status": video['status'],
        "duration": video['duration'],
        "formatted_duration": format_duration(video['duration']) if video['duration'] else None,
        "resolution": video['resolution'],
        "tags": tags,
        "metadata": metadata
    }
    
    # 获取模型大小信息
    model_size = None
    if metadata and 'transcription' in metadata and 'model_size' in metadata['transcription']:
        model_size = metadata['transcription']['model_size']
    elif metadata and 'transcription' in metadata and 'parameters' in metadata['transcription'] and 'model_size' in metadata['transcription']['parameters']:
        model_size = metadata['transcription']['parameters']['model_size']
    
    # 整理转录详情
    transcription_detail = None
    if transcription:
        transcription_detail = {
            "id": transcription['id'],
            "engine": transcription['engine'],
            "model_size": model_size,
            "date": transcription['transcription_date'],
            "confidence": transcription['confidence'],
            "text": transcription['text']
        }
    
    return jsonify({
        "success": True,
        "video": video_detail,
        "transcription": transcription_detail
    }), 200

@app.route('/api/transcription/<int:video_id>/content', methods=['PUT'])
def update_transcription_content(video_id):
    """更新转录内容"""
    data = request.json
    
    if not data or 'text' not in data:
        return jsonify({"success": False, "error": "缺少转录内容"}), 400
    
    # 获取视频记录
    video = db_service.get_video(video_id=video_id)
    if not video:
        return jsonify({"success": False, "error": "视频不存在"}), 404
    
    # 获取最新转录
    transcription = db_service.get_transcription(video_id=video_id, latest=True)
    if not transcription:
        # 如果没有转录记录，创建一个新的
        transcription_id = db_service.add_transcription(
            video_id=video_id,
            text=data['text'],
            engine="manual",
        )
    else:
        # 更新现有记录 (当前数据库设计不支持直接更新，所以添加新记录)
        transcription_id = db_service.add_transcription(
            video_id=video_id,
            text=data['text'],
            engine=transcription['engine'],
            confidence=transcription['confidence']
        )
    
    return jsonify({
        "success": True,
        "message": "转录内容已更新",
        "transcription_id": transcription_id
    }), 200

@app.route('/api/transcription/<int:video_id>', methods=['DELETE'])
def delete_transcription(video_id):
    """删除转录记录"""
    # 获取视频记录
    video = db_service.get_video(video_id=video_id)
    if not video:
        return jsonify({"success": False, "error": "视频不存在"}), 404
    
    # 删除视频及其所有转录
    success = db_service.delete_video(video_id)
    
    if success:
        # TODO: 如果有相关文件，也一并删除
        return jsonify({
            "success": True,
            "message": "转录记录已删除"
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": "删除失败"
        }), 500

# 新增API路由 - 标签管理
@app.route('/api/tags', methods=['GET'])
def get_all_tags():
    """获取所有标签"""
    tags = db_service.get_all_tags()
    return jsonify({
        "success": True,
        "tags": tags
    }), 200

@app.route('/api/tags', methods=['POST'])
def create_tag():
    """创建新标签"""
    data = request.json
    
    if not data or 'name' not in data:
        return jsonify({"success": False, "error": "缺少标签名称"}), 400
    
    name = data['name']
    color = data.get('color', '#3498db')  # 默认蓝色
    
    tag_id = db_service.add_tag(name, color)
    
    if tag_id:
        return jsonify({
            "success": True,
            "message": "标签创建成功",
            "tag_id": tag_id
        }), 201
    else:
        return jsonify({
            "success": False,
            "error": "标签创建失败，可能已存在同名标签"
        }), 400

@app.route('/api/transcription/<int:video_id>/tags', methods=['GET'])
def get_video_tags(video_id):
    """获取视频的所有标签"""
    # 检查视频是否存在
    video = db_service.get_video(video_id=video_id)
    if not video:
        return jsonify({"success": False, "error": "视频不存在"}), 404
    
    tags = db_service.get_video_tags(video_id)
    
    return jsonify({
        "success": True,
        "video_id": video_id,
        "tags": tags
    }), 200

@app.route('/api/transcription/<int:video_id>/tags', methods=['PUT'])
def update_video_tags(video_id):
    """为视频添加或更新标签"""
    data = request.json
    
    if not data or 'tags' not in data:
        return jsonify({"success": False, "error": "缺少标签数据"}), 400
    
    # 检查视频是否存在
    video = db_service.get_video(video_id=video_id)
    if not video:
        return jsonify({"success": False, "error": "视频不存在"}), 404
    
    tag_ids = data['tags']  # 应该是标签ID列表
    
    # 获取当前视频的标签
    current_tags = db_service.get_video_tags(video_id)
    current_tag_ids = [tag['id'] for tag in current_tags]
    
    # 要添加的标签
    tags_to_add = [tag_id for tag_id in tag_ids if tag_id not in current_tag_ids]
    
    # 要移除的标签
    tags_to_remove = [tag_id for tag_id in current_tag_ids if tag_id not in tag_ids]
    
    # 添加新标签
    for tag_id in tags_to_add:
        db_service.add_tag_to_video(video_id, tag_id)
    
    # 移除旧标签
    for tag_id in tags_to_remove:
        db_service.remove_tag_from_video(video_id, tag_id)
    
    return jsonify({
        "success": True,
        "message": "视频标签已更新",
        "video_id": video_id
    }), 200

@app.route('/api/transcription/<int:video_id>/tag/<int:tag_id>', methods=['POST'])
def add_tag_to_video(video_id, tag_id):
    """为视频添加特定标签"""
    # 检查视频是否存在
    video = db_service.get_video(video_id=video_id)
    if not video:
        return jsonify({"success": False, "error": "视频不存在"}), 404
    
    success = db_service.add_tag_to_video(video_id, tag_id)
    
    if success:
        return jsonify({
            "success": True,
            "message": "标签已添加到视频",
            "video_id": video_id,
            "tag_id": tag_id
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": "添加标签失败，标签可能不存在或已添加"
        }), 400

@app.route('/api/transcription/<int:video_id>/tag/<int:tag_id>', methods=['DELETE'])
def remove_tag_from_video(video_id, tag_id):
    """从视频中移除特定标签"""
    # 检查视频是否存在
    video = db_service.get_video(video_id=video_id)
    if not video:
        return jsonify({"success": False, "error": "视频不存在"}), 404
    
    success = db_service.remove_tag_from_video(video_id, tag_id)
    
    if success:
        return jsonify({
            "success": True,
            "message": "标签已从视频中移除",
            "video_id": video_id,
            "tag_id": tag_id
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": "移除标签失败，标签可能不存在或未添加到视频"
        }), 400

# 内容导出API
@app.route('/api/transcription/<int:video_id>/export', methods=['GET'])
def export_transcription(video_id):
    """导出转录内容为不同格式"""
    format_type = request.args.get('format', 'txt')  # 默认txt格式
    
    # 获取视频信息
    video = db_service.get_video(video_id=video_id)
    if not video:
        return jsonify({"success": False, "error": "视频不存在"}), 404
    
    # 获取转录内容
    transcription = db_service.get_transcription(video_id=video_id, latest=True)
    if not transcription:
        return jsonify({"success": False, "error": "转录内容不存在"}), 404
    
    text = transcription['text']
    filename = f"{video['bv_number']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    if format_type == 'txt':
        # 纯文本格式
        response = app.response_class(
            response=text,
            status=200,
            mimetype='text/plain'
        )
        response.headers.set('Content-Disposition', f'attachment; filename={filename}.txt')
        return response
        
    elif format_type == 'md':
        # Markdown格式
        md_content = f"""# {video['title']}

## 视频信息

- **作者:** {video['author']}
- **BV号:** {video['bv_number']}
- **链接:** https://www.bilibili.com/video/{video['bv_number']}
- **时长:** {format_duration(video['duration'])}
- **转录引擎:** {transcription['engine']}
- **转录时间:** {transcription['transcription_date']}

## 转录内容

{text}

---

由 Bili2Text 生成
"""
        response = app.response_class(
            response=md_content,
            status=200,
            mimetype='text/markdown'
        )
        response.headers.set('Content-Disposition', f'attachment; filename={filename}.md')
        return response
        
    elif format_type == 'json':
        # JSON格式
        json_data = {
            "video": {
                "bv_number": video['bv_number'],
                "title": video['title'],
                "author": video['author'],
                "url": f"https://www.bilibili.com/video/{video['bv_number']}",
                "duration": video['duration'],
                "formatted_duration": format_duration(video['duration']) if video['duration'] else None
            },
            "transcription": {
                "engine": transcription['engine'],
                "date": transcription['transcription_date'],
                "text": text
            },
            "exported_at": datetime.now().isoformat(),
            "exported_by": "Bili2Text"
        }
        
        response = app.response_class(
            response=json.dumps(json_data, ensure_ascii=False, indent=2),
            status=200,
            mimetype='application/json'
        )
        response.headers.set('Content-Disposition', f'attachment; filename={filename}.json')
        return response
    
    else:
        return jsonify({
            "success": False,
            "error": f"不支持的导出格式: {format_type}"
        }), 400

# 工具函数
def process_video_async(bv_number, engine, model_size, task_id, video_id):
    """异步处理视频转录"""
    try:
        # 转录参数
        transcription_kwargs = {
            "model_size": model_size,
            "prompt": DEFAULT_PROMPT
        }
        
        # 定义处理器的进度回调
        def progress_callback(progress_info):
            # 更新任务状态
            if task_id in active_tasks:
                stage = progress_info.get("stage", "unknown")
                message = progress_info.get("message", "处理中...")
                progress = progress_info.get("progress", 0.0)
                
                # 更新任务信息
                if stage != active_tasks[task_id]["stage"]:
                    # 阶段变更，更新阶段开始时间
                    active_tasks[task_id]["stage_start_time"] = time.time()
                
                # 更新基本信息
                active_tasks[task_id]["stage"] = stage
                active_tasks[task_id]["stage_name"] = processing_stages.get(stage, {}).get("name", stage)
                active_tasks[task_id]["message"] = message
                stage_progress = progress
                
                # 计算整体进度
                if stage == "downloading":
                    # 下载阶段的整体进度 = 下载权重 * 下载进度
                    active_tasks[task_id]["progress"] = processing_stages["downloading"]["weight"] * stage_progress
                elif stage == "extracting":
                    # 提取阶段的整体进度 = 下载权重 + 提取权重 * 提取进度
                    active_tasks[task_id]["progress"] = (
                        processing_stages["downloading"]["weight"] + 
                        processing_stages["extracting"]["weight"] * stage_progress
                    )
                elif stage == "transcribing":
                    # 转录阶段的整体进度 = 下载权重 + 提取权重 + 转录权重 * 转录进度
                    active_tasks[task_id]["progress"] = (
                        processing_stages["downloading"]["weight"] + 
                        processing_stages["extracting"]["weight"] + 
                        processing_stages["transcribing"]["weight"] * stage_progress
                    )
                elif stage == "metadata":
                    # 元数据阶段几乎完成了
                    active_tasks[task_id]["progress"] = min(0.95, 
                        processing_stages["downloading"]["weight"] + 
                        processing_stages["extracting"]["weight"] + 
                        processing_stages["transcribing"]["weight"] + 
                        processing_stages["metadata"]["weight"] * stage_progress
                    )
                elif stage == "completed":
                    # 全部完成
                    active_tasks[task_id]["progress"] = 1.0
                    active_tasks[task_id]["status"] = "completed"
                elif stage == "failed":
                    # 处理失败
                    active_tasks[task_id]["status"] = "failed"
                
                # 保存详细信息，但移除可能过大的数据
                details = {k: v for k, v in progress_info.items() 
                           if k not in ["stage", "message", "progress"] and not isinstance(v, (dict, list))}
                active_tasks[task_id]["details"] = details
        
        # 处理视频
        result = processor.process_video(
            bv_number,
            engine=engine,
            save_metadata=True,
            progress_callback=progress_callback,
            **transcription_kwargs
        )
        
        if not result["success"]:
            # 更新任务状态
            if task_id in active_tasks:
                active_tasks[task_id]["status"] = "failed"
                active_tasks[task_id]["message"] = result.get("error", "处理失败")
            
            # 更新数据库记录
            db_service.update_video(
                video_id=video_id,
                status="failed",
                title=f"转录失败 ({bv_number})"
            )
            
            log.error(f"视频转录失败: {result.get('error')}")
            return
        
        # 更新任务状态为完成
        if task_id in active_tasks:
            active_tasks[task_id]["status"] = "completed"
            active_tasks[task_id]["progress"] = 1.0
            active_tasks[task_id]["message"] = "处理完成"
        
        # 解析元数据
        metadata = None
        if result.get("metadata_path") and os.path.exists(result["metadata_path"]):
            try:
                with open(result["metadata_path"], 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except Exception as e:
                log.error(f"解析元数据出错: {str(e)}")
        
        # 获取转录文本
        text = None
        if result["transcription_result"] and result["transcription_result"].get("text_file_path"):
            text_file = result["transcription_result"]["text_file_path"]
            try:
                with open(text_file, 'r', encoding='utf-8') as f:
                    text = f.read()
            except Exception as e:
                log.error(f"读取转录文本出错: {str(e)}")
        
        # 更新数据库记录
        db_service.update_video(
            video_id=video_id,
            title=metadata.get("title") if metadata else f"转录完成 ({bv_number})",
            author=metadata.get("author"),
            video_path=result["download_result"]["video_path"],
            audio_path=result["audio_result"]["audio_path"],
            thumbnail_path=result["download_result"]["thumbnail_path"],
            duration=metadata.get("duration") if metadata else None,
            resolution=metadata.get("video_tech_info", {}).get("resolution"),
            status="transcribed",
            metadata=metadata
        )
        
        # 添加转录记录
        if text:
            db_service.add_transcription(
                video_id=video_id,
                text=text,
                engine=engine
            )
        
        log.success(f"视频转录完成: {bv_number}")
        
    except Exception as e:
        log.error(f"处理视频异步任务出错: {str(e)}")
        
        # 更新任务状态
        if task_id in active_tasks:
            active_tasks[task_id]["status"] = "failed"
            active_tasks[task_id]["message"] = f"处理出错: {str(e)}"
        
        # 更新数据库记录
        db_service.update_video(
            video_id=video_id,
            status="failed",
            title=f"转录失败 ({bv_number})"
        )
    finally:
        # 一段时间后从活动任务列表中移除
        def remove_task():
            time.sleep(3600)  # 1小时后移除
            if task_id in active_tasks:
                del active_tasks[task_id]
                
        cleanup_thread = threading.Thread(target=remove_task)
        cleanup_thread.daemon = True
        cleanup_thread.start()

def format_duration(seconds):
    """格式化秒数为时长字符串"""
    if not seconds:
        return "未知"
        
    seconds = int(float(seconds))
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    
    if h > 0:
        return f"{h}小时{m}分{s}秒"
    elif m > 0:
        return f"{m}分{s}秒"
    else:
        return f"{s}秒"

# 主页和前端路由
@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/transcriptions')
def transcriptions_page():
    """转录列表页"""
    return render_template('transcriptions.html')

@app.route('/transcription/<int:video_id>')
def transcription_detail_page(video_id):
    """转录详情页"""
    # 检查视频是否存在
    video = db_service.get_video(video_id=video_id)
    if not video:
        abort(404)  # 返回404页面
        
    return render_template('detail.html', video_id=video_id)

# 创建静态资源路由，用于访问输出文件夹中的文件
@app.route('/output/<path:filename>')
def serve_output_file(filename):
    """提供对输出文件夹中文件的访问"""
    # 构建完整的文件路径
    output_dir = os.path.abspath(OUTPUT_DIR)
    # 安全地拼接路径，防止目录遍历攻击
    try:
        path = os.path.join(output_dir, filename)
        # 检查路径是否仍在输出目录内
        if not os.path.abspath(path).startswith(output_dir):
            abort(403)  # 禁止访问输出目录之外的文件
        # 检查文件是否存在
        if not os.path.exists(path) or not os.path.isfile(path):
            abort(404)
        # 提供文件下载
        return send_file(path)
    except:
        abort(404)  # 文件不存在或发生错误时返回404

# 启动服务器
if __name__ == '__main__':
    app.run(
        host=SERVER_HOST,
        port=SERVER_PORT,
        debug=DEBUG_MODE
    )