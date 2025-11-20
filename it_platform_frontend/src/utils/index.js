// src/utils/index.js

// 获取 API 基础 URL，优先使用环境变量
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

/**
 * 获取完整的媒体资源 URL (如课程封面、视频)
 * @param {string} relativePath - 后端返回的相对路径
 * @returns {string} 完整的 URL
 */
export const getFullMediaUrl = (relativePath) => {
  if (!relativePath) {
    // 默认占位图
    return 'https://via.placeholder.com/300x150.png?text=No+Cover'
  }
  // 如果已经是完整 URL (如 http 开头)，直接返回
  if (relativePath.startsWith('http://') || relativePath.startsWith('https://')) {
    return relativePath
  }
  
  // 处理路径拼接，防止出现双斜杠或缺少斜杠
  const cleanPath = relativePath.startsWith('/') ? relativePath : `/${relativePath}`
  const cleanBase = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL
  
  return `${cleanBase}${cleanPath}`
}

/**
 * 图片加载失败时的处理函数 (回退到占位图)
 */
export const handleImageError = (event) => {
  event.target.src = 'https://via.placeholder.com/300x150.png?text=No+Cover'
}

/**
 * 格式化日期为 YYYY-MM-DD
 * @param {string} dateString - ISO 日期字符串
 */
export const formatDate = (dateString) => {
  if (!dateString) return ''
  try {
    const date = new Date(dateString)
    return date.toISOString().split('T')[0]
  } catch (e) {
    return dateString
  }
}

/**
 * 格式化日期时间为本地字符串 (YYYY/MM/DD HH:mm:ss)
 * @param {string} dateString 
 */
export const formatDateTime = (dateString) => {
  if (!dateString) return ''
  try {
    return new Date(dateString).toLocaleString('zh-CN')
  } catch (e) {
    return dateString
  }
}