// src/utils/common.js

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

/**
 * 通用：获取完整的媒体资源 URL
 * 兼容处理头像、封面图、视频等
 * @param {string} relativePath - 后端返回的相对路径
 * @returns {string} 完整的 URL
 */
export const getFullMediaUrl = (relativePath) => {
  if (!relativePath) return ''
  if (relativePath.startsWith('http://') || relativePath.startsWith('https://')) {
    return relativePath
  }

  // 移除开头多余的斜杠
  const cleanPath = relativePath.startsWith('/') ? relativePath : `/${relativePath}`
  // 移除 API_URL 末尾多余的斜杠
  const cleanBase = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL

  return `${cleanBase}${cleanPath}`
}

// 导出别名，方便语义化使用
export const getFullCoverImagePath = getFullMediaUrl

/**
 * 图片加载失败回退
 */
export const handleImageError = (event) => {
  event.target.src = 'https://via.placeholder.com/300x150.png?text=No+Image'
}

/**
 * 格式化日期 (YYYY-MM-DD)
 */
export const formatDate = (dateString) => {
  if (!dateString) return ''
  try {
    return new Date(dateString).toISOString().split('T')[0]
  } catch (e) {
    return dateString
  }
}

/**
 * 格式化日期时间 (YYYY/MM/DD HH:mm:ss)
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
