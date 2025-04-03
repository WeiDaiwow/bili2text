/**
 * Bili2Text Web Application
 * Main JavaScript file for handling UI interactions, routing, and API calls
 */

// Main application object
const App = {
    // Current state
    currentPage: 'home',
    taskCheckInterval: null,
    currentVideoId: null,
    pagination: {
        page: 1,
        limit: 10,
        total: 0
    },
    
    // Initialize the application
    init: function() {
        this.setupEventListeners();
        this.setupRouting();
        
        // Initialize the first page
        const hash = window.location.hash || '#home';
        this.navigateTo(hash.substring(1));
    },
    
    // Set up event listeners
    setupEventListeners: function() {
        // Navigation links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                const page = e.target.getAttribute('href').substring(1);
                this.navigateTo(page);
            });
        });
        
        // Close notification
        document.getElementById('notification-close').addEventListener('click', () => {
            this.hideNotification();
        });
        
        // Window events
        window.addEventListener('hashchange', () => {
            const hash = window.location.hash || '#home';
            this.navigateTo(hash.substring(1));
        });
        
        // Transcribe form
        document.addEventListener('submit', e => {
            if (e.target.id === 'transcribe-form') {
                e.preventDefault();
                this.handleTranscribeForm();
            }
        });
        
        // Engine select change
        document.addEventListener('change', e => {
            if (e.target.id === 'engine-select') {
                this.toggleEngineOptions(e.target.value);
            }
        });
        
        // Export dropdown
        document.addEventListener('click', e => {
            if (e.target.id === 'export-btn') {
                this.toggleDropdown('export-dropdown');
            } else if (e.target.classList.contains('export-link')) {
                e.preventDefault();
                this.exportTranscription(e.target.getAttribute('data-format'));
            } else if (e.target.id === 'add-tag-btn') {
                this.toggleDropdown('tag-dropdown');
            } else if (!e.target.closest('#export-btn') && !e.target.closest('#export-dropdown')) {
                this.hideDropdown('export-dropdown');
            }
            
            if (!e.target.closest('#add-tag-container')) {
                this.hideDropdown('tag-dropdown');
            }
        });
        
        // Edit transcription
        document.addEventListener('click', e => {
            if (e.target.id === 'edit-btn') {
                this.startEditTranscription();
            } else if (e.target.id === 'cancel-edit-btn') {
                this.cancelEditTranscription();
            } else if (e.target.id === 'save-edit-btn') {
                this.saveEditTranscription();
            }
        });
        
        // Pagination
        document.addEventListener('click', e => {
            if (e.target.id === 'prev-page' || e.target.closest('#prev-page')) {
                this.prevPage();
            } else if (e.target.id === 'next-page' || e.target.closest('#next-page')) {
                this.nextPage();
            } else if (e.target.classList.contains('pagination-btn')) {
                this.goToPage(parseInt(e.target.getAttribute('data-page')));
            }
        });
        
        // Search
        document.addEventListener('input', e => {
            if (e.target.id === 'search-input') {
                this.debounce(this.searchTranscriptions.bind(this), 300)();
            } else if (e.target.id === 'tag-search') {
                this.filterTagDropdown(e.target.value);
            }
        });
        
        // Tag filter
        document.addEventListener('change', e => {
            if (e.target.id === 'tag-filter') {
                this.filterByTag(e.target.value);
            }
        });
    },
    
    // Set up URL routing
    setupRouting: function() {
        window.addEventListener('hashchange', () => {
            const hash = window.location.hash || '#home';
            this.navigateTo(hash.substring(1));
        });
    },
    
    // Navigate to a specific page
    navigateTo: function(page) {
        // Clear any active intervals
        if (this.taskCheckInterval) {
            clearInterval(this.taskCheckInterval);
            this.taskCheckInterval = null;
        }
        
        // Handle video ID in URL
        if (page.startsWith('transcription/')) {
            const videoId = page.split('/')[1];
            this.currentVideoId = videoId;
            page = 'detail';
        }
        
        this.currentPage = page || 'home';
        
        // Update active navigation link
        document.querySelectorAll('.nav-link').forEach(link => {
            const linkPage = link.getAttribute('href').substring(1);
            if (linkPage === this.currentPage) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
        
        // Load the appropriate template
        this.loadPage(this.currentPage);
        
        // Update the URL if it doesn't match the current page
        const expectedHash = this.currentPage === 'detail' 
            ? `#transcription/${this.currentVideoId}` 
            : `#${this.currentPage}`;
            
        if (window.location.hash !== expectedHash) {
            window.location.hash = expectedHash;
        }
    },
    
    // Load a page template
    loadPage: function(page) {
        const container = document.getElementById('app-container');
        const loaderHtml = `
            <div class="loader-container flex justify-center items-center h-64">
                <div class="loader ease-linear rounded-full border-4 border-t-4 border-gray-200 h-12 w-12"></div>
            </div>
        `;
        
        // Show loader while loading
        container.innerHTML = loaderHtml;
        
        // Get the template
        const template = document.getElementById(`${page}-template`);
        if (!template) {
            container.innerHTML = '<div class="bg-white rounded-lg shadow-md p-6"><h1 class="text-2xl font-bold text-gray-800 mb-4">页面未找到</h1><p>请返回<a href="#home" class="text-blue-500 hover:underline">首页</a></p></div>';
            return;
        }
        
        // Clone the template
        const content = template.content.cloneNode(true);
        
        // Render the page after a brief delay to show the loader
        setTimeout(() => {
            container.innerHTML = '';
            container.appendChild(content);
            
            // Initialize page-specific functionality
            switch (page) {
                case 'home':
                    this.initHomePage();
                    break;
                case 'transcriptions':
                    this.initTranscriptionsPage();
                    break;
                case 'detail':
                    this.initDetailPage();
                    break;
                case 'about':
                    // Nothing to initialize
                    break;
            }
        }, 300);
    },
    
    // Initialize the home page
    initHomePage: function() {
        // Load recent transcriptions
        this.loadRecentTranscriptions();
        
        // Setup engine selection
        this.toggleEngineOptions(document.getElementById('engine-select').value);
    },
    
    // Initialize the transcriptions list page
    initTranscriptionsPage: function() {
        // Reset pagination
        this.pagination.page = 1;
        
        // Load tags for filter
        this.loadTags();
        
        // Load transcriptions
        this.loadTranscriptions();
    },
    
    // Initialize the detail page
    initDetailPage: function() {
        if (!this.currentVideoId) {
            this.navigateTo('home');
            return;
        }
        
        // Load transcription details
        this.loadTranscriptionDetail(this.currentVideoId);
        
        // Load tags
        this.loadTagsForVideo();
    },
    
    // API Calls
    
    // Load recent transcriptions for home page
    loadRecentTranscriptions: function() {
        const container = document.getElementById('recent-transcriptions');
        if (!container) return;
        
        fetch('/api/transcriptions/recent?limit=5')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.videos.length > 0) {
                    container.innerHTML = this.renderTranscriptionsList(data.videos);
                } else {
                    container.innerHTML = `
                        <div class="bg-gray-50 rounded-lg p-6 text-center">
                            <p class="text-gray-600">暂无转录记录</p>
                            <p class="text-sm text-gray-500 mt-2">开始您的第一个转录任务吧！</p>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error loading recent transcriptions:', error);
                container.innerHTML = `
                    <div class="bg-red-50 rounded-lg p-6 text-center">
                        <p class="text-red-600">加载失败</p>
                        <p class="text-sm text-red-500 mt-2">请刷新页面重试</p>
                    </div>
                `;
            });
    },
    
    // Load all transcriptions for the list page
    loadTranscriptions: function() {
        const container = document.getElementById('transcriptions-list');
        if (!container) return;
        
        const { page, limit } = this.pagination;
        const offset = (page - 1) * limit;
        
        // Get filter value
        const tagFilter = document.getElementById('tag-filter')?.value || '';
        const tagQuery = tagFilter ? `&tag_id=${tagFilter}` : '';
        
        // Get search value
        const searchQuery = document.getElementById('search-input')?.value || '';
        const searchParam = searchQuery ? `&search=${encodeURIComponent(searchQuery)}` : '';
        
        fetch(`/api/transcriptions?limit=${limit}&offset=${offset}${tagQuery}${searchParam}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update pagination
                    this.pagination.total = data.total;
                    this.updatePagination();
                    
                    if (data.videos.length > 0) {
                        container.innerHTML = this.renderTranscriptionsList(data.videos);
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
            })
            .catch(error => {
                console.error('Error loading transcriptions:', error);
                container.innerHTML = `
                    <div class="bg-red-50 rounded-lg p-6 text-center">
                        <p class="text-red-600">加载失败</p>
                        <p class="text-sm text-red-500 mt-2">请刷新页面重试</p>
                    </div>
                `;
            });
    },
    
    // Load transcription detail
    loadTranscriptionDetail: function(videoId) {
        const contentContainer = document.getElementById('transcription-content');
        if (!contentContainer) return;
        
        fetch(`/api/transcription/${videoId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.renderTranscriptionDetail(data);
                } else {
                    contentContainer.innerHTML = `
                        <div class="bg-red-50 rounded-lg p-6 text-center">
                            <p class="text-red-600">加载失败</p>
                            <p class="text-sm text-red-500 mt-2">${data.error || '请刷新页面重试'}</p>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error loading transcription detail:', error);
                contentContainer.innerHTML = `
                    <div class="bg-red-50 rounded-lg p-6 text-center">
                        <p class="text-red-600">加载失败</p>
                        <p class="text-sm text-red-500 mt-2">请刷新页面重试</p>
                    </div>
                `;
            });
    },
    
    // Load tags for filter dropdown
    loadTags: function() {
        const tagFilter = document.getElementById('tag-filter');
        if (!tagFilter) return;
        
        fetch('/api/tags')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.tags.length > 0) {
                    let options = '<option value="">所有标签</option>';
                    data.tags.forEach(tag => {
                        options += `<option value="${tag.id}">${tag.name}</option>`;
                    });
                    tagFilter.innerHTML = options;
                }
            })
            .catch(error => {
                console.error('Error loading tags:', error);
            });
    },
    
    // Load tags for the current video
    loadTagsForVideo: function() {
        if (!this.currentVideoId) return;
        
        const tagsContainer = document.getElementById('video-tags');
        const tagDropdown = document.getElementById('tag-list');
        
        if (!tagsContainer || !tagDropdown) return;
        
        // First load all tags
        fetch('/api/tags')
            .then(response => response.json())
            .then(allTagsData => {
                if (!allTagsData.success) return;
                
                // Then load video tags
                fetch(`/api/transcription/${this.currentVideoId}/tags`)
                    .then(response => response.json())
                    .then(videoTagsData => {
                        if (videoTagsData.success) {
                            // Render video tags
                            tagsContainer.innerHTML = '';
                            
                            if (videoTagsData.tags.length === 0) {
                                tagsContainer.innerHTML = '<span class="text-sm text-gray-500">暂无标签</span>';
                            } else {
                                videoTagsData.tags.forEach(tag => {
                                    const tagElement = document.createElement('span');
                                    tagElement.className = 'tag-badge px-2 py-1 text-sm rounded-full mr-2 mb-2';
                                    tagElement.style.backgroundColor = tag.color + '33'; // Add transparency
                                    tagElement.style.color = tag.color;
                                    
                                    tagElement.innerHTML = `
                                        ${tag.name}
                                        <span class="tag-remove ml-1 cursor-pointer" data-tag-id="${tag.id}">×</span>
                                    `;
                                    
                                    tagsContainer.appendChild(tagElement);
                                });
                                
                                // Add tag removal event
                                document.querySelectorAll('.tag-remove').forEach(btn => {
                                    btn.addEventListener('click', e => {
                                        const tagId = e.target.getAttribute('data-tag-id');
                                        this.removeTagFromVideo(tagId);
                                    });
                                });
                            }
                            
                            // Render tag dropdown
                            tagDropdown.innerHTML = '';
                            
                            // Get IDs of tags already added to the video
                            const videoTagIds = videoTagsData.tags.map(tag => tag.id);
                            
                            // Add only tags that aren't already added
                            allTagsData.tags
                                .filter(tag => !videoTagIds.includes(tag.id))
                                .forEach(tag => {
                                    const tagItem = document.createElement('div');
                                    tagItem.className = 'px-2 py-1 text-sm hover:bg-gray-100 cursor-pointer rounded';
                                    tagItem.setAttribute('data-tag-id', tag.id);
                                    
                                    // Add colored dot
                                    tagItem.innerHTML = `
                                        <span class="inline-block w-2 h-2 rounded-full mr-2" style="background-color: ${tag.color}"></span>
                                        ${tag.name}
                                    `;
                                    
                                    tagItem.addEventListener('click', () => {
                                        this.addTagToVideo(tag.id);
                                        this.hideDropdown('tag-dropdown');
                                    });
                                    
                                    tagDropdown.appendChild(tagItem);
                                });
                                
                            if (tagDropdown.children.length === 0) {
                                tagDropdown.innerHTML = '<div class="px-2 py-1 text-sm text-gray-500">没有更多标签可添加</div>';
                            }
                        }
                    })
                    .catch(error => {
                        console.error('Error loading video tags:', error);
                    });
            })
            .catch(error => {
                console.error('Error loading all tags:', error);
            });
    },
    
    // Add a tag to the current video
    addTagToVideo: function(tagId) {
        if (!this.currentVideoId) return;
        
        fetch(`/api/transcription/${this.currentVideoId}/tag/${tagId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.loadTagsForVideo();
                    this.showNotification('标签已添加', '标签已成功添加到视频', 'success');
                } else {
                    this.showNotification('添加失败', data.error || '添加标签失败', 'error');
                }
            })
            .catch(error => {
                console.error('Error adding tag:', error);
                this.showNotification('添加失败', '添加标签失败，请稍后重试', 'error');
            });
    },
    
    // Remove a tag from the current video
    removeTagFromVideo: function(tagId) {
        if (!this.currentVideoId) return;
        
        fetch(`/api/transcription/${this.currentVideoId}/tag/${tagId}`, {
            method: 'DELETE'
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.loadTagsForVideo();
                    this.showNotification('标签已移除', '标签已从视频中移除', 'success');
                } else {
                    this.showNotification('移除失败', data.error || '移除标签失败', 'error');
                }
            })
            .catch(error => {
                console.error('Error removing tag:', error);
                this.showNotification('移除失败', '移除标签失败，请稍后重试', 'error');
            });
    },
    
    // Submit a transcription request
    submitTranscription: function(formData) {
        fetch('/api/transcribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.status === 'completed') {
                        // Video was already transcribed
                        this.showNotification('处理完成', '该视频已经过转录，正在跳转到详情页', 'success');
                        setTimeout(() => {
                            this.navigateTo(`transcription/${data.video_id}`);
                        }, 1500);
                    } else {
                        // New transcription task
                        this.showTaskModal('正在下载视频，请稍候...');
                        this.monitorTask(data.task_id, data.video_id);
                    }
                } else {
                    this.showNotification('提交失败', data.error || '提交转录请求失败', 'error');
                }
            })
            .catch(error => {
                console.error('Error submitting transcription:', error);
                this.showNotification('提交失败', '提交转录请求失败，请稍后重试', 'error');
            });
    },
    
    // Monitor a transcription task
    monitorTask: function(taskId, videoId) {
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
        
        const checkStatus = () => {
            fetch(`/api/task/${taskId}`)
                .then(response => response.json())
                .then(data => {
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
                                this.hideTaskModal();
                                this.showNotification('处理完成', '视频转录已完成，正在跳转到详情页', 'success');
                                setTimeout(() => {
                                    this.navigateTo(`transcription/${videoId}`);
                                }, 1000);
                            }, 1500);
                        } else if (status === 'failed') {
                            // 任务失败
                            document.getElementById('task-status').textContent = '转录失败，请稍后重试...';
                            
                            // 显示错误提示，延迟关闭对话框
                            setTimeout(() => {
                                this.hideTaskModal();
                                this.showNotification('处理失败', '视频转录失败，请稍后重试', 'error');
                            }, 1500);
                        }
                    } else {
                        // API错误
                        setTimeout(() => {
                            this.hideTaskModal();
                            this.showNotification('状态检查失败', data.error || '无法获取任务状态', 'error');
                        }, 1000);
                    }
                })
                .catch(error => {
                    console.error('Error checking task status:', error);
                    // 错误后继续尝试检查（最多尝试5次）
                    if (checkCount < 5) {
                        setTimeout(checkStatus, 3000);
                        checkCount++;
                    } else {
                        this.hideTaskModal();
                        this.showNotification('连接失败', '无法连接到服务器，请检查网络连接', 'error');
                    }
                });
        };
        
        // 立即开始第一次检查
        checkStatus();
    },

    // Show task modal: updated to include smooth progress bar animation
    showTaskModal: function(statusText) {
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
    },
    
    // Export transcription
    exportTranscription: function(format) {
        if (!this.currentVideoId) return;
        
        // Hide dropdown
        this.hideDropdown('export-dropdown');
        
        // Open export URL in new tab
        window.open(`/api/transcription/${this.currentVideoId}/export?format=${format}`, '_blank');
    },
    
    // Update transcription content
    updateTranscriptionContent: function(videoId, text) {
        fetch(`/api/transcription/${videoId}/content`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showNotification('保存成功', '转录内容已更新', 'success');
                    
                    // Update the display
                    document.getElementById('transcription-content').textContent = text;
                    
                    // Exit edit mode
                    document.getElementById('edit-form-container').classList.add('hidden');
                    document.getElementById('transcription-content').classList.remove('hidden');
                } else {
                    this.showNotification('保存失败', data.error || '更新转录内容失败', 'error');
                }
            })
            .catch(error => {
                console.error('Error updating transcription content:', error);
                this.showNotification('保存失败', '更新转录内容失败，请稍后重试', 'error');
            });
    },
    
    // Search transcriptions
    searchTranscriptions: function() {
        // Reset to first page
        this.pagination.page = 1;
        
        // Reload transcriptions with search
        this.loadTranscriptions();
    },
    
    // Filter by tag
    filterByTag: function(tagId) {
        // Reset to first page
        this.pagination.page = 1;
        
        // Reload transcriptions with filter
        this.loadTranscriptions();
    },
    
    // UI Helpers
    
    // Handle transcribe form submission
    handleTranscribeForm: function() {
        const form = document.getElementById('transcribe-form');
        if (!form) return;
        
        const bvNumber = form.elements['bv_number'].value.trim();
        const engine = form.elements['engine'].value;
        const modelSize = form.elements['model_size']?.value || 'small';
        
        // Validate BV number
        if (!bvNumber) {
            this.showNotification('输入错误', '请输入有效的BV号', 'error');
            return;
        }
        
        // Submit transcription request
        this.submitTranscription({
            bv_number: bvNumber,
            engine: engine,
            model_size: modelSize
        });
    },
    
    // Toggle engine-specific options
    toggleEngineOptions: function(engine) {
        const whisperOptions = document.getElementById('whisper-options');
        if (!whisperOptions) return;
        
        if (engine === 'whisper') {
            whisperOptions.classList.remove('hidden');
        } else {
            whisperOptions.classList.add('hidden');
        }
    },
    
    // Show notification
    showNotification: function(title, message, type = 'success') {
        const notification = document.getElementById('notification');
        const notificationTitle = document.getElementById('notification-title');
        const notificationMessage = document.getElementById('notification-message');
        const notificationIcon = document.getElementById('notification-icon');
        
        // Set content
        notificationTitle.textContent = title;
        notificationMessage.textContent = message;
        
        // Set type
        notification.className = notification.className.replace(/border-\w+-500/g, '');
        notification.classList.add(`border-${type === 'success' ? 'green' : type === 'error' ? 'red' : 'yellow'}-500`);
        
        // Set icon
        notificationIcon.textContent = type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'warning';
        notificationIcon.className = notificationIcon.className.replace(/text-\w+-500/g, '');
        notificationIcon.classList.add(`text-${type === 'success' ? 'green' : type === 'error' ? 'red' : 'yellow'}-500`);
        
        // Show notification
        notification.classList.remove('hidden');
        notification.classList.add('show');
        
        // Hide after 5 seconds
        setTimeout(() => {
            this.hideNotification();
        }, 5000);
    },
    
    // Hide notification
    hideNotification: function() {
        const notification = document.getElementById('notification');
        notification.classList.add('hidden');
        notification.classList.remove('show');
    },
    
    // Hide task modal
    hideTaskModal: function() {
        const modal = document.getElementById('task-modal');
        if (!modal) return;
        
        modal.classList.add('hidden');
    },
    
    // Toggle dropdown
    toggleDropdown: function(dropdownId) {
        const dropdown = document.getElementById(dropdownId);
        if (!dropdown) return;
        
        if (dropdown.classList.contains('hidden')) {
            // Hide all other dropdowns first
            document.querySelectorAll('.dropdown-content').forEach(el => {
                el.classList.add('hidden');
            });
            
            // Show this dropdown
            dropdown.classList.remove('hidden');
        } else {
            dropdown.classList.add('hidden');
        }
    },
    
    // Hide dropdown
    hideDropdown: function(dropdownId) {
        const dropdown = document.getElementById(dropdownId);
        if (!dropdown) return;
        
        dropdown.classList.add('hidden');
    },
    
    // Filter tag dropdown
    filterTagDropdown: function(query) {
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
    },
    
    // Start editing transcription
    startEditTranscription: function() {
        const content = document.getElementById('transcription-content');
        const editForm = document.getElementById('edit-form-container');
        const editTextarea = document.getElementById('edit-transcription');
        
        if (!content || !editForm || !editTextarea) return;
        
        // Copy content to textarea
        editTextarea.value = content.textContent.trim();
        
        // Show edit form, hide content
        content.classList.add('hidden');
        editForm.classList.remove('hidden');
    },
    
    // Cancel editing transcription
    cancelEditTranscription: function() {
        const content = document.getElementById('transcription-content');
        const editForm = document.getElementById('edit-form-container');
        
        if (!content || !editForm) return;
        
        // Hide edit form, show content
        editForm.classList.add('hidden');
        content.classList.remove('hidden');
    },
    
    // Save edited transcription
    saveEditTranscription: function() {
        if (!this.currentVideoId) return;
        
        const editTextarea = document.getElementById('edit-transcription');
        if (!editTextarea) return;
        
        const text = editTextarea.value.trim();
        
        // Update content
        this.updateTranscriptionContent(this.currentVideoId, text);
    },
    
    // Pagination controls
    prevPage: function() {
        if (this.pagination.page > 1) {
            this.pagination.page--;
            this.loadTranscriptions();
        }
    },
    
    nextPage: function() {
        const maxPage = Math.ceil(this.pagination.total / this.pagination.limit);
        if (this.pagination.page < maxPage) {
            this.pagination.page++;
            this.loadTranscriptions();
        }
    },
    
    goToPage: function(page) {
        this.pagination.page = page;
        this.loadTranscriptions();
    },
    
    updatePagination: function() {
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');
        const paginationNumbers = document.getElementById('pagination-numbers');
        const resultsInfo = document.getElementById('showing-results');
        
        if (!prevBtn || !nextBtn || !paginationNumbers || !resultsInfo) return;
        
        const { page, limit, total } = this.pagination;
        const maxPage = Math.ceil(total / limit);
        
        // Enable/disable prev/next buttons
        prevBtn.disabled = page <= 1;
        nextBtn.disabled = page >= maxPage;
        
        // Generate page numbers
        let paginationHtml = '';
        
        // Determine range of pages to show
        let startPage = Math.max(1, page - 2);
        let endPage = Math.min(maxPage, startPage + 4);
        
        // Adjust if we're near the end
        if (endPage - startPage < 4 && startPage > 1) {
            startPage = Math.max(1, endPage - 4);
        }
        
        // First page
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
        
        // Page numbers
        for (let i = startPage; i <= endPage; i++) {
            paginationHtml += `
                <button class="pagination-btn px-3 py-1 rounded-md border ${page === i ? 'bg-blue-500 text-white' : 'text-gray-600 hover:bg-gray-100'}" data-page="${i}">${i}</button>
            `;
        }
        
        // Last page
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
        
        // Update results info
        const start = (page - 1) * limit + 1;
        const end = Math.min(start + limit - 1, total);
        resultsInfo.textContent = `显示 ${start}-${end} / ${total} 结果`;
    },
    
    // Rendering Functions
    
    // Render transcriptions list
    renderTranscriptionsList: function(videos) {
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
                            ${tags || '<span class="text-xs text-gray-500">无标签</span>'}
                        </div>
                        
                        <div class="flex justify-between items-center">
                            <p class="text-xs text-gray-500">${video.bv_number}</p>
                            <a href="#transcription/${video.id}" class="text-sm text-blue-500 hover:text-blue-600 flex items-center">
                                查看详情 <span class="material-icons text-sm ml-1">arrow_forward</span>
                            </a>
                        </div>
                    </div>
                </div>
            `;
        });
        
        return html;
    },
    
    // Render transcription detail
    renderTranscriptionDetail: function(data) {
        const { video, transcription } = data;
        
        // Update video information
        document.getElementById('video-title').textContent = video.title || `转录记录 (${video.bv_number})`;
        document.getElementById('video-author').textContent = video.author || '未知作者';
        document.getElementById('video-duration').textContent = video.formatted_duration || '未知时长';
        document.getElementById('video-thumbnail').src = video.thumbnail_path || '/static/img/placeholder.jpg';
        document.getElementById('video-link').href = video.url;
        
        // Update transcription information
        const engineBadge = document.getElementById('transcription-engine');
        const contentContainer = document.getElementById('transcription-content');
        
        if (transcription) {
            // Show transcription content
            engineBadge.textContent = `引擎: ${transcription.engine}`;
            contentContainer.innerHTML = `<pre class="transcription-text whitespace-pre-wrap text-gray-800">${transcription.text}</pre>`;
            
            // Enable edit button
            document.getElementById('edit-btn').disabled = false;
        } else {
            // No transcription yet
            engineBadge.textContent = '未转录';
            contentContainer.innerHTML = `
                <div class="bg-gray-50 rounded-lg p-6 text-center">
                    <p class="text-gray-600">暂无转录内容</p>
                    <p class="text-sm text-gray-500 mt-2">视频可能仍在处理中，或者转录失败</p>
                </div>
            `;
            
            // Disable edit button
            document.getElementById('edit-btn').disabled = true;
        }
    },
    
    // Utility Functions
    
    // Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function() {
            const context = this;
            const args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                func.apply(context, args);
            }, wait);
        };
    }
};

// Date formatter
function formatDate(dateString) {
    if (!dateString) return '未知日期';
    
    const date = new Date(dateString);
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
        return dateString;
    }
    
    // Format as YYYY-MM-DD HH:MM
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day} ${hours}:${minutes}`;
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    App.init();
});