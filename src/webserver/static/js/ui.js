/**
 * ui.js
 * UI 组件与交互模块
 */

import { formatDate } from './utils.js';

// 显示通知
export function showNotification(title, message, type = 'success') {
    const notification = document.getElementById('notification');
    const notificationTitle = document.getElementById('notification-title');
    const notificationMessage = document.getElementById('notification-message');
    const notificationIcon = document.getElementById('notification-icon');
    
    // 设置内容
    notificationTitle.textContent = title;
    notificationMessage.textContent = message;
    
    // 设置类型
    notification.className = notification.className.replace(/border-\w+-500/g, '');
    notification.classList.add(`border-${type === 'success' ? 'green' : type === 'error' ? 'red' : 'yellow'}-500`);
    
    // 设置图标
    notificationIcon.textContent = type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'warning';
    notificationIcon.className = notificationIcon.className.replace(/text-\w+-500/g, '');
    notificationIcon.classList.add(`text-${type === 'success' ? 'green' : type === 'error' ? 'red' : 'yellow'}-500`);
    
    // 显示通知
    notification.classList.remove('hidden');
    notification.classList.add('show');
    
    // 5秒后隐藏
    setTimeout(() => {
        hideNotification();
    }, 5000);
}

// 隐藏通知
export function hideNotification() {
    const notification = document.getElementById('notification');
    notification.classList.add('hidden');
    notification.classList.remove('show');
}

// 显示任务进度对话框
export function showTaskModal(statusText) {
    const modal = document.getElementById('task-modal');
    const statusElement = document.getElementById('task-status');
    const progressBar = document.getElementById('task-progress');
    
    if (!modal || !statusElement || !progressBar) return;
    
    // 设置初始内容
    statusElement.textContent = statusText;
    progressBar.style.width = '5%';
    progressBar.style.transition = 'width 0.5s ease-in-out';
    
    // 显示对话框
    modal.classList.remove('hidden');
}

// 隐藏任务进度对话框
export function hideTaskModal() {
    const modal = document.getElementById('task-modal');
    if (!modal) return;
    
    modal.classList.add('hidden');
}

// 切换下拉菜单
export function toggleDropdown(dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    if (!dropdown) return;
    
    if (dropdown.classList.contains('hidden')) {
        // 先隐藏所有其他下拉菜单
        document.querySelectorAll('.dropdown-content').forEach(el => {
            el.classList.add('hidden');
        });
        
        // 显示当前下拉菜单
        dropdown.classList.remove('hidden');
    } else {
        dropdown.classList.add('hidden');
    }
}

// 隐藏下拉菜单
export function hideDropdown(dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    if (!dropdown) return;
    
    dropdown.classList.add('hidden');
}

// 过滤标签下拉列表
export function filterTagDropdown(query) {
    const tagItems = document.querySelectorAll('#tag-list > div');
    query = query.toLowerCase();
    
    tagItems.forEach(item => {
        const tagName = item.textContent.trim().toLowerCase();
        if (tagName.includes(query)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

// 更新分页控件
export function updatePagination(pagination) {
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    const paginationNumbers = document.getElementById('pagination-numbers');
    const resultsInfo = document.getElementById('showing-results');
    
    if (!prevBtn || !nextBtn || !paginationNumbers || !resultsInfo) return;
    
    const { page, limit, total } = pagination;
    const maxPage = Math.ceil(total / limit);
    
    // 启用/禁用上一页/下一页按钮
    prevBtn.disabled = page <= 1;
    nextBtn.disabled = page >= maxPage;
    
    // 生成页码
    let paginationHtml = '';
    
    // 确定要显示的页码范围
    let startPage = Math.max(1, page - 2);
    let endPage = Math.min(maxPage, startPage + 4);
    
    // 调整，如果接近末尾
    if (endPage - startPage < 4 && startPage > 1) {
        startPage = Math.max(1, endPage - 4);
    }
    
    // 第一页
    if (startPage > 1) {
        paginationHtml += `
            <button class="pagination-btn px-3 py-1 rounded-md border ${page === 1 ? 'bg-blue-500 text-white' : 'text-gray-600 hover:bg-gray-100'}" data-page="1">1</button>
        `;
        
        if (startPage > 2) {
            paginationHtml += `
                <span class="px-2 py-1">...</span>
            `;
        }
    }
    
    // 页码
    for (let i = startPage; i <= endPage; i++) {
        paginationHtml += `
            <button class="pagination-btn px-3 py-1 rounded-md border ${page === i ? 'bg-blue-500 text-white' : 'text-gray-600 hover:bg-gray-100'}" data-page="${i}">${i}</button>
        `;
    }
    
    // 最后一页
    if (endPage < maxPage) {
        if (endPage < maxPage - 1) {
            paginationHtml += `
                <span class="px-2 py-1">...</span>
            `;
        }
        
        paginationHtml += `
            <button class="pagination-btn px-3 py-1 rounded-md border ${page === maxPage ? 'bg-blue-500 text-white' : 'text-gray-600 hover:bg-gray-100'}" data-page="${maxPage}">${maxPage}</button>
        `;
    }
    
    paginationNumbers.innerHTML = paginationHtml;
    
    // 更新结果信息
    const start = (page - 1) * limit + 1;
    const end = Math.min(start + limit - 1, total);
    resultsInfo.textContent = `显示 ${start}-${end} / ${total} 结果`;
}

// 显示确认对话框
export function showConfirmDialog(title, message, confirmCallback, cancelCallback = null) {
    console.log('调用showConfirmDialog:', title, message);
    
    // 找到对话框元素
    const dialog = document.getElementById('confirm-dialog');
    const dialogTitle = document.getElementById('confirm-dialog-title');
    const dialogMessage = document.getElementById('confirm-dialog-message');
    const confirmBtn = document.getElementById('confirm-dialog-confirm');
    const cancelBtn = document.getElementById('confirm-dialog-cancel');
    
    // 检查元素是否存在
    if (!dialog || !dialogTitle || !dialogMessage || !confirmBtn || !cancelBtn) {
        console.error('确认对话框元素不存在或不完整:', {
            dialog: !!dialog,
            dialogTitle: !!dialogTitle,
            dialogMessage: !!dialogMessage,
            confirmBtn: !!confirmBtn,
            cancelBtn: !!cancelBtn
        });
        
        // 元素不存在时，使用alert作为备选方案
        if (window.confirm(message)) {
            if (typeof confirmCallback === 'function') {
                confirmCallback();
            }
        } else {
            if (typeof cancelCallback === 'function') {
                cancelCallback();
            }
        }
        return;
    }
    
    // 设置对话框内容
    dialogTitle.textContent = title;
    dialogMessage.textContent = message;
    
    // 移除现有事件监听器
    const newConfirmBtn = confirmBtn.cloneNode(true);
    const newCancelBtn = cancelBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
    
    // 添加新的事件监听器
    newConfirmBtn.addEventListener('click', function() {
        console.log('确认按钮被点击');
        dialog.classList.add('hidden');
        if (typeof confirmCallback === 'function') {
            confirmCallback();
        }
    });
    
    newCancelBtn.addEventListener('click', function() {
        console.log('取消按钮被点击');
        dialog.classList.add('hidden');
        if (typeof cancelCallback === 'function') {
            cancelCallback();
        }
    });
    
    // 显示对话框
    dialog.classList.remove('hidden');
    console.log('确认对话框已显示');
}

// 删除转录记录
export async function deleteTranscription(videoId) {
    try {
        const response = await fetch(`/api/transcription/${videoId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error(`删除失败: ${response.statusText}`);
        }
        
        return { success: true };
    } catch (error) {
        console.error('删除转录记录失败:', error);
        return { success: false, error: error.message };
    }
}

// 渲染转录列表
export async function renderTranscriptionsList(videos) {
    if (!videos || videos.length === 0) {
        return `
            <div class="bg-gray-50 rounded-lg p-6 text-center">
                <p class="text-gray-600">暂无转录记录</p>
                <p class="text-sm text-gray-500 mt-2">开始您的第一个转录任务吧！</p>
            </div>
        `;
    }
    
    let html = '';
    
    videos.forEach(video => {
        const status = video.status;
        const statusClass = status === 'transcribed' ? 'bg-green-100 text-green-800' :
                            status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                            status === 'failed' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800';
        
        const statusText = status === 'transcribed' ? '已转录' :
                           status === 'processing' ? '处理中' :
                           status === 'failed' ? '失败' : '未知';
        
        const tags = video.tags && video.tags.length > 0 ? 
            video.tags.map(tag => `
                <span class="text-xs px-2 py-0.5 rounded-full mr-1" 
                      style="background-color: ${tag.color}33; color: ${tag.color}">
                    ${tag.name}
                </span>
            `).join('') : '';
        
        // 添加模型信息显示
        const modelInfo = video.model_size ? 
            `<span class="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full mr-1">模型: ${video.model_size}</span>` : '';
        
        html += `
            <div class="card-hover video-card bg-white rounded-lg shadow-sm overflow-hidden flex transition-all duration-200">
                <div class="w-1/4 min-w-[120px] aspect-video flex-shrink-0">
                    <img src="${video.thumbnail_path || '/static/img/placeholder.jpg'}" alt="${video.title}" 
                         class="w-full h-full object-cover">
                </div>
                <div class="p-4 flex-1">
                    <div class="flex justify-between items-start">
                        <h3 class="text-lg font-medium text-gray-800 mb-1 title line-clamp-1">${video.title || `转录记录 (${video.bv_number})`}</h3>
                        <span class="text-xs px-2 py-0.5 rounded-full ${statusClass}">${statusText}</span>
                    </div>
                    <p class="text-sm text-gray-600 mb-2">${video.author || '未知作者'} · ${formatDate(video.download_date)}</p>
                    
                    <div class="flex items-center mb-2">
                        ${modelInfo}
                        ${tags || '<span class="text-xs text-gray-500">无标签</span>'}
                    </div>
                    
                    <div class="flex justify-between items-center">
                        <p class="text-xs text-gray-500">${video.bv_number}</p>
                        <div class="flex items-center">
                            <a href="#transcription/${video.id}" class="text-sm text-blue-500 hover:text-blue-600 flex items-center">
                                查看详情 <span class="material-icons text-sm ml-1">arrow_forward</span>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    return html;
}

// 渲染转录详情
export function renderTranscriptionDetail(data) {
    const { video, transcription } = data;
    
    // 更新视频信息
    const videoTitle = document.getElementById('video-title');
    const videoAuthor = document.getElementById('video-author');
    const videoDuration = document.getElementById('video-duration');
    const videoThumbnail = document.getElementById('video-thumbnail');
    const videoLink = document.getElementById('video-link');
    
    if (videoTitle) videoTitle.textContent = video.title || `转录记录 (${video.bv_number})`;
    if (videoAuthor) videoAuthor.textContent = video.author || '未知作者';
    if (videoDuration) videoDuration.textContent = video.formatted_duration || '未知时长';
    if (videoThumbnail) videoThumbnail.src = video.thumbnail_path || '/static/img/placeholder.jpg';
    if (videoLink) videoLink.href = video.url;
    
    // 更新转录信息
    const engineBadge = document.getElementById('transcription-engine');
    const modelBadge = document.getElementById('transcription-model');
    const contentContainer = document.getElementById('transcription-content');
    const editBtn = document.getElementById('edit-btn');
    const deleteBtn = document.getElementById('delete-btn');
    
    if (transcription) {
        // 显示转录内容
        if (engineBadge) {
            engineBadge.textContent = `引擎: ${transcription.engine}`;
        }
        
        // 显示模型信息（如果有）
        if (modelBadge) {
            if (transcription.model_size) {
                modelBadge.textContent = `模型: ${transcription.model_size}`;
                modelBadge.classList.remove('hidden');
            } else {
                modelBadge.classList.add('hidden');
            }
        }
        
        if (contentContainer) {
            contentContainer.innerHTML = `<pre class="transcription-text whitespace-pre-wrap text-gray-800">${transcription.text}</pre>`;
        }
        
        // 启用编辑和删除按钮
        if (editBtn) editBtn.disabled = false;
        if (deleteBtn) {
            deleteBtn.disabled = false;
            deleteBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            deleteBtn.classList.add('hover:bg-red-600');
        }
    } else {
        // 无转录内容
        if (engineBadge) {
            engineBadge.textContent = '未转录';
        }
        
        if (modelBadge) {
            modelBadge.classList.add('hidden');
        }
        
        if (contentContainer) {
            contentContainer.innerHTML = `
                <div class="bg-gray-50 rounded-lg p-6 text-center">
                    <p class="text-gray-600">暂无转录内容</p>
                    <p class="text-sm text-gray-500 mt-2">视频可能仍在处理中，或者转录失败</p>
                </div>
            `;
        }
        
        // 禁用编辑和删除按钮
        if (editBtn) editBtn.disabled = true;
        if (deleteBtn) {
            deleteBtn.disabled = true;
            deleteBtn.classList.add('opacity-50', 'cursor-not-allowed');
            deleteBtn.classList.remove('hover:bg-red-600');
        }
    }
}