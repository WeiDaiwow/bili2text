/**
 * main.js
 * 应用入口点，负责初始化和协调各个模块
 */

import { initRouter } from './router.js';
import { setupPageCallbacks } from './pageControllers.js';

// 应用初始化
function initApp() {
    // 设置页面回调
    setupPageCallbacks();
    
    // 初始化路由系统
    initRouter();
    
    console.log('Bili2Text Web App initialized');
}

// 当DOM加载完成时初始化应用
document.addEventListener('DOMContentLoaded', initApp);