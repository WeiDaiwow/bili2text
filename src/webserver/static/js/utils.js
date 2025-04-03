/**
 * utils.js
 * 通用工具函数模块
 */

// 格式化日期
export function formatDate(dateString) {
    if (!dateString) return '未知日期';
    
    const date = new Date(dateString);
    
    // 检查日期是否有效
    if (isNaN(date.getTime())) {
        return dateString;
    }
    
    // 格式化为 YYYY-MM-DD HH:MM
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day} ${hours}:${minutes}`;
}

// 防抖函数
export function debounce(func, wait) {
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