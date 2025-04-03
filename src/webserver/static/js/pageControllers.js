/**
 * pageControllers.js
 * 页面控制器模块 - 处理不同页面的特定功能
 */

import * as api from './api.js';
import * as ui from './ui.js';
import { debounce } from './utils.js';
import { monitorTask } from './taskMonitor.js';
import { navigateTo, getCurrentPage, registerPageResetCallback } from './router.js';

// 分页状态
const pagination = {
    page: 1,
    limit: 10,
    total: 0
};

// 初始化首页
export function initHomePage() {
    // 加载最近的转录记录
    loadRecentTranscriptions();
    
    // 设置引擎选择
    const engineSelect = document.getElementById('engine-select');
    if (engineSelect) {
        toggleEngineOptions(engineSelect.value);
        
        // 监听引擎选择变化
        engineSelect.addEventListener('change', (e) => {
            toggleEngineOptions(e.target.value);
        });
    }
    
    // 设置表单提交事件
    const form = document.getElementById('transcribe-form');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            handleTranscribeForm();
        });
    }
}

// 初始化转录列表页
export function initTranscriptionsPage() {
    // 重置分页
    pagination.page = 1;
    
    // 加载标签过滤器
    loadTagsForFilter();
    
    // 加载转录列表
    loadTranscriptions();
    
    // 监听标签过滤器变化
    const tagFilter = document.getElementById('tag-filter');
    if (tagFilter) {
        tagFilter.addEventListener('change', () => {
            filterByTag(tagFilter.value);
        });
    }
    
    // 监听搜索输入
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(() => {
            searchTranscriptions(searchInput.value);
        }, 300));
    }
    
    // 监听分页按钮
    document.addEventListener('click', e => {
        if (e.target.id === 'prev-page' || e.target.closest('#prev-page')) {
            prevPage();
        } else if (e.target.id === 'next-page' || e.target.closest('#next-page')) {
            nextPage();
        } else if (e.target.classList.contains('pagination-btn')) {
            goToPage(parseInt(e.target.getAttribute('data-page')));
        }
    });
    
    // 设置删除按钮事件委托
    document.addEventListener('click', e => {
        console.log('点击事件:', e.target);
        const deleteBtn = e.target.closest('.delete-transcription-btn');
        console.log('删除按钮:', deleteBtn);
        // 如果点击的是删除按钮
        if (deleteBtn) {
            const videoId = deleteBtn.getAttribute('data-id');
            if (videoId) {
                confirmDeleteTranscription(videoId);
            }
        }
    });
}

// 初始化详情页
export function initDetailPage() {
    const { videoId } = getCurrentPage();
    if (!videoId) {
        navigateTo('home');
        return;
    }
    
    console.log('初始化详情页，视频ID:', videoId);
    
    // 加载转录详情
    loadTranscriptionDetail(videoId);
    
    // 加载视频标签
    loadTagsForVideo(videoId);
    
    // 监听导出按钮
    const exportBtn = document.getElementById('export-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', () => {
            ui.toggleDropdown('export-dropdown');
        });
    }
    
    // 监听导出链接
    document.querySelectorAll('.export-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const format = e.target.getAttribute('data-format');
            if (format) {
                api.exportTranscription(videoId, format);
                ui.hideDropdown('export-dropdown');
            }
        });
    });
    
    // 监听编辑按钮
    const editBtn = document.getElementById('edit-btn');
    if (editBtn) {
        editBtn.addEventListener('click', () => {
            startEditTranscription();
        });
    }
    
    // 监听取消编辑按钮
    const cancelEditBtn = document.getElementById('cancel-edit-btn');
    if (cancelEditBtn) {
        cancelEditBtn.addEventListener('click', () => {
            cancelEditTranscription();
        });
    }
    
    // 监听保存编辑按钮
    const saveEditBtn = document.getElementById('save-edit-btn');
    if (saveEditBtn) {
        saveEditBtn.addEventListener('click', () => {
            saveEditTranscription(videoId);
        });
    }
    
    // 监听删除按钮 - 特殊处理详情页删除按钮
    const detailPageDeleteBtn = document.getElementById('delete-btn');
    if (detailPageDeleteBtn) {
        console.log('找到详情页删除按钮，设置事件监听器');
        
        // 移除可能存在的旧事件监听器
        const newDeleteBtn = detailPageDeleteBtn.cloneNode(true);
        detailPageDeleteBtn.parentNode.replaceChild(newDeleteBtn, detailPageDeleteBtn);
        
        // 添加点击事件监听
        newDeleteBtn.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            console.log('详情页删除按钮被点击，视频ID:', videoId);
            confirmDeleteTranscription(videoId);
        });
    } else {
        console.error('未找到详情页删除按钮');
    }
    
    // 监听添加标签按钮
    const addTagBtn = document.getElementById('add-tag-btn');
    if (addTagBtn) {
        addTagBtn.addEventListener('click', () => {
            ui.toggleDropdown('tag-dropdown');
        });
    }
    
    // 监听标签搜索
    const tagSearch = document.getElementById('tag-search');
    if (tagSearch) {
        tagSearch.addEventListener('input', (e) => {
            ui.filterTagDropdown(e.target.value);
        });
    }
    
    // 设置点击其他地方关闭下拉菜单
    document.addEventListener('click', (e) => {
        if (!e.target.closest('#export-btn') && !e.target.closest('#export-dropdown')) {
            ui.hideDropdown('export-dropdown');
        }
        
        if (!e.target.closest('#add-tag-container')) {
            ui.hideDropdown('tag-dropdown');
        }
    });
}

// 设置删除按钮监听器 - 新增函数，更可靠地处理删除按钮
function setupDeleteButtonListener(videoId) {
    const deleteBtn = document.getElementById('delete-btn-' + videoId);
    
    if (!deleteBtn) {
        console.error('找不到删除按钮');
        return;
    }
    
    console.log('找到删除按钮，设置事件监听器');
    
    // 移除可能存在的旧事件监听器
    const newDeleteBtn = deleteBtn.cloneNode(true);
    deleteBtn.parentNode.replaceChild(newDeleteBtn, deleteBtn);
    
    // 添加多种事件监听方式以确保可以触发
    // 方法1: 使用标准事件监听器
    newDeleteBtn.addEventListener('click', function(event) {
        event.preventDefault();
        event.stopPropagation();
        console.log('删除按钮被点击 (addEventListener)，视频ID:', videoId);
        confirmDeleteTranscription(videoId);
    });
    
    // 方法2: 使用onclick属性
    newDeleteBtn.onclick = function(event) {
        event.preventDefault();
        event.stopPropagation();
        console.log('删除按钮被点击 (onclick)，视频ID:', videoId);
        confirmDeleteTranscription(videoId);
        return false;
    };
    
    // 直接测试确认框
    console.log('测试直接调用确认对话框');
    setTimeout(() => {
        // 延迟3秒后测试直接调用确认对话框功能（仅用于调试）
        // ui.showConfirmDialog('测试确认对话框', '这是一个测试消息，您可以关闭此对话框', () => {
        //     console.log('测试确认回调被执行');
        // });
    }, 3000);
}

// 确认删除转录记录
function confirmDeleteTranscription(videoId) {
    console.log('触发删除确认，视频ID:', videoId);
    
    ui.showConfirmDialog(
        '确认删除',
        '确定要删除这个转录记录吗？此操作不可撤销。',
        async () => {
            console.log('确认删除，开始执行删除操作...');
            
            try {
                const result = await api.deleteTranscription(videoId);
                
                if (result.success) {
                    ui.showNotification('删除成功', '转录记录已成功删除', 'success');
                    
                    // 在详情页返回到列表页
                    if (getCurrentPage().name === 'detail') {
                        console.log('从详情页返回到列表页');
                        // 使用history.back()方法返回上一页，而不是硬编码导航到列表页
                        setTimeout(() => {
                            console.log('执行返回上一页操作');
                            window.history.back();
                            // 如果返回上一页失败，则导航到转录列表页
                            setTimeout(() => {
                                if (getCurrentPage().name === 'detail') {
                                    console.log('返回上一页失败，导航到转录列表页');
                                    navigateTo('transcriptions');
                                }
                            }, 100);
                        }, 1000);
                    } else {
                        // 如果在列表页，重新加载列表
                        console.log('重新加载转录列表');
                        loadTranscriptions();
                    }
                } else {
                    console.error('删除失败:', result.error);
                    ui.showNotification('删除失败', result.error || '删除转录记录失败', 'error');
                }
            } catch (error) {
                console.error('删除过程中发生错误:', error);
                ui.showNotification('删除失败', '删除过程中发生错误，请稍后重试', 'error');
            }
        }
    );
}

// 加载最近的转录记录
async function loadRecentTranscriptions() {
    const container = document.getElementById('recent-transcriptions');
    if (!container) return;
    
    try {
        const data = await api.fetchRecentTranscriptions(5);
        
        if (data.success && data.videos.length > 0) {
            container.innerHTML = await ui.renderTranscriptionsList(data.videos);
        } else {
            container.innerHTML = `
                <div class="bg-gray-50 rounded-lg p-6 text-center">
                    <p class="text-gray-600">暂无转录记录</p>
                    <p class="text-sm text-gray-500 mt-2">开始您的第一个转录任务吧！</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading recent transcriptions:', error);
        container.innerHTML = `
            <div class="bg-red-50 rounded-lg p-6 text-center">
                <p class="text-red-600">加载失败</p>
                <p class="text-sm text-red-500 mt-2">请刷新页面重试</p>
            </div>
        `;
    }
}

// 加载所有转录记录（带分页）
async function loadTranscriptions() {
    const container = document.getElementById('transcriptions-list');
    if (!container) return;
    
    const { page, limit } = pagination;
    const offset = (page - 1) * limit;
    
    // 获取过滤值
    const tagFilter = document.getElementById('tag-filter')?.value || '';
    
    // 获取搜索值
    const searchQuery = document.getElementById('search-input')?.value || '';
    
    try {
        const data = await api.fetchTranscriptions(limit, offset, tagFilter, searchQuery);
        
        if (data.success) {
            // 更新分页
            pagination.total = data.total;
            ui.updatePagination(pagination);
            
            if (data.videos.length > 0) {
                container.innerHTML = await ui.renderTranscriptionsList(data.videos);
            } else {
                container.innerHTML = `
                    <div class="bg-gray-50 rounded-lg p-6 text-center">
                        <p class="text-gray-600">暂无转录记录</p>
                        <p class="text-sm text-gray-500 mt-2">开始您的第一个转录任务吧！</p>
                    </div>
                `;
            }
        } else {
            container.innerHTML = `
                <div class="bg-red-50 rounded-lg p-6 text-center">
                    <p class="text-red-600">加载失败</p>
                    <p class="text-sm text-red-500 mt-2">请刷新页面重试</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading transcriptions:', error);
        container.innerHTML = `
            <div class="bg-red-50 rounded-lg p-6 text-center">
                <p class="text-red-600">加载失败</p>
                <p class="text-sm text-red-500 mt-2">请刷新页面重试</p>
            </div>
        `;
    }
}

// 加载转录详情
async function loadTranscriptionDetail(videoId) {
    const contentContainer = document.getElementById('transcription-content');
    if (!contentContainer) return;
    
    try {
        const data = await api.fetchTranscriptionDetail(videoId);
        
        if (data.success) {
            ui.renderTranscriptionDetail(data);
        } else {
            contentContainer.innerHTML = `
                <div class="bg-red-50 rounded-lg p-6 text-center">
                    <p class="text-red-600">加载失败</p>
                    <p class="text-sm text-red-500 mt-2">${data.error || '请刷新页面重试'}</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading transcription detail:', error);
        contentContainer.innerHTML = `
            <div class="bg-red-50 rounded-lg p-6 text-center">
                <p class="text-red-600">加载失败</p>
                <p class="text-sm text-red-500 mt-2">请刷新页面重试</p>
            </div>
        `;
    }
}

// 加载标签过滤器
async function loadTagsForFilter() {
    const tagFilter = document.getElementById('tag-filter');
    if (!tagFilter) return;
    
    try {
        const data = await api.fetchAllTags();
        
        if (data.success && data.tags.length > 0) {
            let options = '<option value="">所有标签</option>';
            data.tags.forEach(tag => {
                options += `<option value="${tag.id}">${tag.name}</option>`;
            });
            tagFilter.innerHTML = options;
        }
    } catch (error) {
        console.error('Error loading tags for filter:', error);
    }
}

// 加载视频标签
async function loadTagsForVideo(videoId) {
    const tagsContainer = document.getElementById('video-tags');
    const tagDropdown = document.getElementById('tag-list');
    
    if (!tagsContainer || !tagDropdown) return;
    
    try {
        // 先加载所有标签
        const allTagsData = await api.fetchAllTags();
        if (!allTagsData.success) return;
        
        // 然后加载视频标签
        const videoTagsData = await api.fetchVideoTags(videoId);
        
        if (videoTagsData.success) {
            // 渲染视频标签
            tagsContainer.innerHTML = '';
            
            if (videoTagsData.tags.length === 0) {
                tagsContainer.innerHTML = '<span class="text-sm text-gray-500">暂无标签</span>';
            } else {
                videoTagsData.tags.forEach(tag => {
                    const tagElement = document.createElement('span');
                    tagElement.className = 'tag-badge px-2 py-1 text-sm rounded-full mr-2 mb-2';
                    tagElement.style.backgroundColor = tag.color + '33'; // 添加透明度
                    tagElement.style.color = tag.color;
                    
                    tagElement.innerHTML = `
                        ${tag.name}
                        <span class="tag-remove ml-1 cursor-pointer" data-tag-id="${tag.id}">×</span>
                    `;
                    
                    tagsContainer.appendChild(tagElement);
                });
                
                // 添加标签移除事件
                document.querySelectorAll('.tag-remove').forEach(btn => {
                    btn.addEventListener('click', e => {
                        const tagId = e.target.getAttribute('data-tag-id');
                        removeTagFromVideo(videoId, tagId);
                    });
                });
            }
            
            // 渲染标签下拉菜单
            tagDropdown.innerHTML = '';
            
            // 获取已添加的标签ID
            const videoTagIds = videoTagsData.tags.map(tag => tag.id);
            
            // 只添加尚未添加的标签
            allTagsData.tags
                .filter(tag => !videoTagIds.includes(tag.id))
                .forEach(tag => {
                    const tagItem = document.createElement('div');
                    tagItem.className = 'px-2 py-1 text-sm hover:bg-gray-100 cursor-pointer rounded';
                    tagItem.setAttribute('data-tag-id', tag.id);
                    
                    // 添加彩色圆点
                    tagItem.innerHTML = `
                        <span class="inline-block w-2 h-2 rounded-full mr-2" style="background-color: ${tag.color}"></span>
                        ${tag.name}
                    `;
                    
                    tagItem.addEventListener('click', () => {
                        addTagToVideo(videoId, tag.id);
                        ui.hideDropdown('tag-dropdown');
                    });
                    
                    tagDropdown.appendChild(tagItem);
                });
                
            if (tagDropdown.children.length === 0) {
                tagDropdown.innerHTML = '<div class="px-2 py-1 text-sm text-gray-500">没有更多标签可添加</div>';
            }
        }
    } catch (error) {
        console.error('Error loading tags for video:', error);
    }
}

// 处理转录表单提交
function handleTranscribeForm() {
    const form = document.getElementById('transcribe-form');
    if (!form) return;
    
    const bvNumber = form.elements['bv_number'].value.trim();
    const engine = form.elements['engine'].value;
    let modelSize = 'small';  // 默认值
    
    // 确保只有whisper引擎时才获取模型大小
    if (engine === 'whisper' && form.elements['model_size']) {
        modelSize = form.elements['model_size'].value;
    }
    
    // 验证BV号
    if (!bvNumber) {
        ui.showNotification('输入错误', '请输入有效的BV号', 'error');
        return;
    }
    
    // 提交转录请求
    submitTranscription({
        bv_number: bvNumber,
        engine: engine,
        model_size: modelSize
    });
}

// 提交转录请求
async function submitTranscription(formData) {
    try {
        const data = await api.submitTranscriptionRequest(formData);
        
        if (data.success) {
            if (data.status === 'completed') {
                // 视频已经转录过
                ui.showNotification('处理完成', '该视频已经过转录，正在跳转到详情页', 'success');
                setTimeout(() => {
                    navigateTo(`transcription/${data.video_id}`);
                }, 1500);
            } else {
                // 新的转录任务
                ui.showTaskModal('正在下载视频，请稍候...');
                monitorTask(data.task_id, data.video_id, navigateTo);
            }
        } else {
            ui.showNotification('提交失败', data.error || '提交转录请求失败', 'error');
        }
    } catch (error) {
        console.error('Error submitting transcription:', error);
        ui.showNotification('提交失败', '提交转录请求失败，请稍后重试', 'error');
    }
}

// 切换引擎特定选项
function toggleEngineOptions(engine) {
    const whisperOptions = document.getElementById('whisper-options');
    if (!whisperOptions) return;
    
    if (engine === 'whisper') {
        whisperOptions.classList.remove('hidden');
    } else {
        whisperOptions.classList.add('hidden');
    }
}

// 开始编辑转录
function startEditTranscription() {
    const content = document.getElementById('transcription-content');
    const editForm = document.getElementById('edit-form-container');
    const editTextarea = document.getElementById('edit-transcription');
    
    if (!content || !editForm || !editTextarea) return;
    
    // 复制内容到文本框
    editTextarea.value = content.textContent.trim();
    
    // 显示编辑表单，隐藏内容
    content.classList.add('hidden');
    editForm.classList.remove('hidden');
}

// 取消编辑转录
function cancelEditTranscription() {
    const content = document.getElementById('transcription-content');
    const editForm = document.getElementById('edit-form-container');
    
    if (!content || !editForm) return;
    
    // 隐藏编辑表单，显示内容
    editForm.classList.add('hidden');
    content.classList.remove('hidden');
}

// 保存编辑的转录
async function saveEditTranscription(videoId) {
    const editTextarea = document.getElementById('edit-transcription');
    if (!editTextarea) return;
    
    const text = editTextarea.value.trim();
    
    try {
        const data = await api.updateTranscriptionContent(videoId, text);
        
        if (data.success) {
            ui.showNotification('保存成功', '转录内容已更新', 'success');
            
            // 更新显示
            document.getElementById('transcription-content').textContent = text;
            
            // 退出编辑模式
            document.getElementById('edit-form-container').classList.add('hidden');
            document.getElementById('transcription-content').classList.remove('hidden');
        } else {
            ui.showNotification('保存失败', data.error || '更新转录内容失败', 'error');
        }
    } catch (error) {
        console.error('Error updating transcription content:', error);
        ui.showNotification('保存失败', '更新转录内容失败，请稍后重试', 'error');
    }
}

// 向视频添加标签
async function addTagToVideo(videoId, tagId) {
    try {
        const data = await api.addTagToVideo(videoId, tagId);
        
        if (data.success) {
            loadTagsForVideo(videoId);
            ui.showNotification('标签已添加', '标签已成功添加到视频', 'success');
        } else {
            ui.showNotification('添加失败', data.error || '添加标签失败', 'error');
        }
    } catch (error) {
        console.error('Error adding tag to video:', error);
        ui.showNotification('添加失败', '添加标签失败，请稍后重试', 'error');
    }
}

// 从视频移除标签
async function removeTagFromVideo(videoId, tagId) {
    try {
        const data = await api.removeTagFromVideo(videoId, tagId);
        
        if (data.success) {
            loadTagsForVideo(videoId);
            ui.showNotification('标签已移除', '标签已从视频中移除', 'success');
        } else {
            ui.showNotification('移除失败', data.error || '移除标签失败', 'error');
        }
    } catch (error) {
        console.error('Error removing tag from video:', error);
        ui.showNotification('移除失败', '移除标签失败，请稍后重试', 'error');
    }
}

// 搜索转录
function searchTranscriptions(query) {
    // 重置到第一页
    pagination.page = 1;
    
    // 重新加载带搜索的转录
    loadTranscriptions();
}

// 按标签过滤
function filterByTag(tagId) {
    // 重置到第一页
    pagination.page = 1;
    
    // 重新加载带过滤的转录
    loadTranscriptions();
}

// 分页控制 - 上一页
function prevPage() {
    if (pagination.page > 1) {
        pagination.page--;
        loadTranscriptions();
    }
}

// 分页控制 - 下一页
function nextPage() {
    const maxPage = Math.ceil(pagination.total / pagination.limit);
    if (pagination.page < maxPage) {
        pagination.page++;
        loadTranscriptions();
    }
}

// 分页控制 - 跳转到指定页
function goToPage(page) {
    pagination.page = page;
    loadTranscriptions();
}

// 注册页面初始化回调
export function setupPageCallbacks() {
    registerPageResetCallback('home', initHomePage);
    registerPageResetCallback('transcriptions', initTranscriptionsPage);
    registerPageResetCallback('detail', initDetailPage);
}