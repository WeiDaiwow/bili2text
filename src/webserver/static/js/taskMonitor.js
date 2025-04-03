/**
 * taskMonitor.js
 * 任务监控模块
 */

import { checkTaskStatus } from './api.js';
import { showNotification, hideTaskModal } from './ui.js';

/**
 * 监控转录任务并更新进度
 * @param {string} taskId 任务ID
 * @param {string} videoId 视频ID
 * @param {function} navigateCallback 导航回调函数
 */
export function monitorTask(taskId, videoId, navigateCallback) {
    // 上次获取的进度值，用于平滑过渡
    let lastProgress = 0;
    let animationFrame = null;
    let currentStageName = '正在处理';
    
    // 进度条动画函数
    const animateProgress = (targetProgress) => {
        const progressBar = document.getElementById('task-progress');
        if (!progressBar) return;
        
        // 当前进度
        const currentWidth = parseFloat(progressBar.style.width || '5%');
        // 目标宽度（百分比）
        const targetWidth = Math.max(5, Math.min(100, targetProgress * 100));
        
        // 如果差异太小，直接设置
        if (Math.abs(targetWidth - currentWidth) < 0.5) {
            progressBar.style.width = `${targetWidth}%`;
            return;
        }
        
        // 计算新宽度（逐渐接近目标值）
        const newWidth = currentWidth + (targetWidth - currentWidth) * 0.1;
        progressBar.style.width = `${newWidth}%`;
        
        // 继续动画直到接近目标值
        if (Math.abs(newWidth - targetWidth) > 0.5) {
            animationFrame = requestAnimationFrame(() => animateProgress(targetProgress));
        }
    };
    
    // 检查任务状态的间隔时间（毫秒）
    // 开始时频繁检查，随后逐渐减少频率
    let checkInterval = 1000;
    let checkCount = 0;
    
    const checkStatus = async () => {
        try {
            const data = await checkTaskStatus(taskId);
            
            if (data.success) {
                const status = data.status;
                
                if (status === 'processing') {
                    // 获取进度信息
                    const progress = data.progress || 0;
                    const stageName = data.stage_name || currentStageName;
                    currentStageName = stageName;
                    
                    // 更新进度条（使用平滑动画）
                    if (progress > lastProgress || progress >= 0.99) {
                        // 取消之前的动画
                        if (animationFrame) {
                            cancelAnimationFrame(animationFrame);
                        }
                        // 启动新的进度动画
                        animateProgress(progress);
                        lastProgress = progress;
                    }
                    
                    // 更新状态文本
                    const elapsedTime = Math.floor(data.elapsed_time);
                    const minutes = Math.floor(elapsedTime / 60);
                    const seconds = elapsedTime % 60;
                    const timeStr = `${minutes}分${seconds.toString().padStart(2, '0')}秒`;
                    
                    // 使用服务器返回的阶段名称
                    document.getElementById('task-status').textContent = 
                        `${stageName}，已用时: ${timeStr}`;
                    
                    // 调整检查间隔（随时间逐渐增加间隔）
                    checkCount++;
                    if (checkCount > 10 && checkInterval < 3000) {
                        checkInterval = 2000; // 10次检查后，间隔增加到2秒
                    }
                    if (checkCount > 30 && checkInterval < 5000) {
                        checkInterval = 3000; // 30次检查后，间隔增加到3秒
                    }
                    
                    // 安排下一次检查
                    setTimeout(checkStatus, checkInterval);
                } else if (status === 'completed') {
                    // 任务完成，显示100%进度
                    animateProgress(1.0);
                    
                    // 更新状态文本
                    document.getElementById('task-status').textContent = '处理完成，即将跳转到详情页...';
                    
                    // 延迟关闭对话框并导航到详情页
                    setTimeout(() => {
                        hideTaskModal();
                        showNotification('处理完成', '视频转录已完成，正在跳转到详情页', 'success');
                        setTimeout(() => {
                            navigateCallback(`transcription/${videoId}`);
                        }, 1000);
                    }, 1500);
                } else if (status === 'failed') {
                    // 任务失败
                    document.getElementById('task-status').textContent = '转录失败，请稍后重试...';
                    
                    // 显示错误提示，延迟关闭对话框
                    setTimeout(() => {
                        hideTaskModal();
                        showNotification('处理失败', '视频转录失败，请稍后重试', 'error');
                    }, 1500);
                }
            } else {
                // API错误
                setTimeout(() => {
                    hideTaskModal();
                    showNotification('状态检查失败', data.error || '无法获取任务状态', 'error');
                }, 1000);
            }
        } catch (error) {
            console.error('Error in task monitoring:', error);
            // 错误后继续尝试检查（最多尝试5次）
            if (checkCount < 5) {
                setTimeout(checkStatus, 3000);
                checkCount++;
            } else {
                hideTaskModal();
                showNotification('连接失败', '无法连接到服务器，请检查网络连接', 'error');
            }
        }
    };
    
    // 立即开始第一次检查
    checkStatus();
}