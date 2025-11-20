// src/utils/common.js

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

/**
 * 通用：获取完整的媒体资源 URL
 * 兼容处理头像、封面图、视频等
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

// 【关键修复】导出 getFullCoverImagePath 作为别名
// 这样无论组件里写的是 getFullMediaUrl 还是 getFullCoverImagePath 都能用
export const getFullCoverImagePath = getFullMediaUrl

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
 * 图片加载失败回退
 */
export const handleImageError = (event) => {
  event.target.src = 'https://via.placeholder.com/300x150.png?text=No+Image'
}
