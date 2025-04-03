/**
 * router.js
 * 路由管理模块
 */

// 存储当前页面状态
const state = {
    currentPage: 'home',
    currentVideoId: null,
    pageResetCallbacks: {} // 存储页面重置回调函数
};

/**
 * 初始化路由
 */
export function initRouter() {
    window.addEventListener('hashchange', () => {
        const hash = window.location.hash || '#home';
        navigateTo(hash.substring(1));
    });
    
    // 初始化第一个页面
    const hash = window.location.hash || '#home';
    navigateTo(hash.substring(1));
}

/**
 * 注册页面重置回调函数
 * @param {string} page 页面名称
 * @param {Function} callback 重置回调函数
 */
export function registerPageResetCallback(page, callback) {
    state.pageResetCallbacks[page] = callback;
}

/**
 * 导航到特定页面
 * @param {string} page 页面名称或路径
 */
export function navigateTo(page) {
    // 处理URL中的视频ID
    if (page.startsWith('transcription/')) {
        const videoId = page.split('/')[1];
        state.currentVideoId = videoId;
        page = 'detail';
    }
    
    state.currentPage = page || 'home';
    
    // 更新活动导航链接
    document.querySelectorAll('.nav-link').forEach(link => {
        const linkPage = link.getAttribute('href').substring(1);
        if (linkPage === state.currentPage) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
    
    // 加载相应的模板
    loadPage(state.currentPage);
    
    // 更新URL如果与当前页面不匹配
    const expectedHash = state.currentPage === 'detail' 
        ? `#transcription/${state.currentVideoId}` 
        : `#${state.currentPage}`;
        
    if (window.location.hash !== expectedHash) {
        window.location.hash = expectedHash;
    }
}

/**
 * 加载页面模板
 * @param {string} page 页面名称
 */
function loadPage(page) {
    const container = document.getElementById('app-container');
    const loaderHtml = `
        <div class="loader-container flex justify-center items-center h-64">
            <div class="loader ease-linear rounded-full border-4 border-t-4 border-gray-200 h-12 w-12"></div>
        </div>
    `;
    
    // 显示加载中指示器
    container.innerHTML = loaderHtml;
    
    // 获取模板
    const template = document.getElementById(`${page}-template`);
    if (!template) {
        container.innerHTML = '<div class="bg-white rounded-lg shadow-md p-6"><h1 class="text-2xl font-bold text-gray-800 mb-4">页面未找到</h1><p>请返回<a href="#home" class="text-blue-500 hover:underline">首页</a></p></div>';
        return;
    }
    
    // 克隆模板
    const content = template.content.cloneNode(true);
    
    // 在短暂延迟后渲染页面，以显示加载中指示器
    setTimeout(() => {
        container.innerHTML = '';
        container.appendChild(content);
        
        // 调用页面重置回调函数（如果存在）
        if (state.pageResetCallbacks[page]) {
            state.pageResetCallbacks[page]();
        }
    }, 300);
}

/**
 * 获取当前页面信息
 * @returns {Object} 当前页面状态
 */
export function getCurrentPage() {
    return {
        page: state.currentPage,
        videoId: state.currentVideoId
    };
}