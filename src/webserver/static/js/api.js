/**
 * api.js
 * API请求处理模块
 */

// 获取最近转录列表
export async function fetchRecentTranscriptions(limit = 5) {
    try {
        const response = await fetch(`/api/transcriptions/recent?limit=${limit}`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching recent transcriptions:', error);
        throw error;
    }
}

// 获取所有转录列表（带分页和过滤）
export async function fetchTranscriptions(limit = 10, offset = 0, tagId = '', searchQuery = '') {
    try {
        const tagQuery = tagId ? `&tag_id=${tagId}` : '';
        const searchParam = searchQuery ? `&search=${encodeURIComponent(searchQuery)}` : '';
        
        const response = await fetch(`/api/transcriptions?limit=${limit}&offset=${offset}${tagQuery}${searchParam}`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching transcriptions:', error);
        throw error;
    }
}

// 获取转录详情
export async function fetchTranscriptionDetail(videoId) {
    try {
        const response = await fetch(`/api/transcription/${videoId}`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching transcription detail:', error);
        throw error;
    }
}

// 获取所有标签
export async function fetchAllTags() {
    try {
        const response = await fetch('/api/tags');
        return await response.json();
    } catch (error) {
        console.error('Error fetching tags:', error);
        throw error;
    }
}

// 获取视频的标签
export async function fetchVideoTags(videoId) {
    try {
        const response = await fetch(`/api/transcription/${videoId}/tags`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching video tags:', error);
        throw error;
    }
}

// 向视频添加标签
export async function addTagToVideo(videoId, tagId) {
    try {
        const response = await fetch(`/api/transcription/${videoId}/tag/${tagId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        return await response.json();
    } catch (error) {
        console.error('Error adding tag to video:', error);
        throw error;
    }
}

// 从视频移除标签
export async function removeTagFromVideo(videoId, tagId) {
    try {
        const response = await fetch(`/api/transcription/${videoId}/tag/${tagId}`, {
            method: 'DELETE'
        });
        return await response.json();
    } catch (error) {
        console.error('Error removing tag from video:', error);
        throw error;
    }
}

// 提交转录请求
export async function submitTranscriptionRequest(formData) {
    try {
        const response = await fetch('/api/transcribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        return await response.json();
    } catch (error) {
        console.error('Error submitting transcription request:', error);
        throw error;
    }
}

// 检查任务状态
export async function checkTaskStatus(taskId) {
    try {
        const response = await fetch(`/api/task/${taskId}`);
        return await response.json();
    } catch (error) {
        console.error('Error checking task status:', error);
        throw error;
    }
}

// 更新转录内容
export async function updateTranscriptionContent(videoId, text) {
    try {
        const response = await fetch(`/api/transcription/${videoId}/content`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text })
        });
        return await response.json();
    } catch (error) {
        console.error('Error updating transcription content:', error);
        throw error;
    }
}

// 导出转录内容
export function exportTranscription(videoId, format) {
    window.open(`/api/transcription/${videoId}/export?format=${format}`, '_blank');
}

// 删除转录记录
export async function deleteTranscription(videoId) {
    try {
        console.log(`正在发送删除请求，视频ID: ${videoId}`);
        const response = await fetch(`/api/transcription/${videoId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            console.error(`删除请求失败: ${response.status}`, data);
            throw new Error(data.error || `删除失败: ${response.statusText}`);
        }
        
        console.log(`删除成功，视频ID: ${videoId}`);
        return data;
    } catch (error) {
        console.error('删除转录记录失败:', error);
        return { 
            success: false, 
            error: error.message || "删除请求失败，请稍后重试" 
        };
    }
}