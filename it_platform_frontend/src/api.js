// src/api.js
import axios from 'axios'

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000',
  timeout: 10000, // 10秒超时
  headers: {
    'Content-Type': 'application/json',
  }
})

// --- 请求拦截器 ---
apiClient.interceptors.request.use(
  (config) => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Token ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// --- 响应拦截器 ---
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    const status = error.response ? error.response.status : null

    // 处理 401 (未授权) 或 403 (禁止访问)
    if (status === 401 || status === 403) {
      console.warn('API: 认证失败，正在退出登录...')

      try {
        // 动态导入 authStore 避免循环依赖
        const { useAuthStore } = await import('@/stores/authStore')
        const authStore = useAuthStore()
        
        // 清理状态
        authStore.logout()

        // 如果当前不在登录页，则跳转
        if (window.location.pathname !== '/login') {
            window.location.href = '/login'
        }
      } catch (e) {
        // 兜底：手动清除 Storage
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient