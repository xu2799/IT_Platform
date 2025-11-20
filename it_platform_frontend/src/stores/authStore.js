import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import apiClient from '@/api'
import axios from 'axios' 

const API_URL = import.meta.env.VITE_API_URL

export const useAuthStore = defineStore('auth', () => {

  const token = ref(localStorage.getItem('token') || null)
  const user = ref(JSON.parse(localStorage.getItem('user')) || null)

  const isAuthenticated = computed(() => !!token.value)
  
  const isCourseFavorited = computed(() => {
    return (courseId) => {
      if (!user.value || !user.value.favorited_courses) {
        return false
      }
      return user.value.favorited_courses.includes(Number(courseId))
    }
  })

  async function fetchUser() {
    if (!token.value) {
      console.log('AuthStore: (fetchUser) 没有令牌, 无法获取用户。')
      throw new Error("No token found");
    }
    try {
      console.log('AuthStore: 正在从 /api/users/me/ 获取真实用户数据...')
      const response = await apiClient.get('/api/users/me/')
      const realUserData = response.data 
      user.value = realUserData
      localStorage.setItem('user', JSON.stringify(realUserData))
      console.log('AuthStore: 真实用户数据已获取:', realUserData)
    } catch (error) {
      console.error('AuthStore: (fetchUser) 获取用户失败!', error)
      logout() 
      throw error; 
    }
  }

  async function login(username, password) {
    try {
      console.log('AuthStore: 正在尝试登录...')
      
      const response = await axios.post(`${API_URL}/api/token-auth/`, {
        username: username,
        password: password
      })
      
      const receivedToken = response.data.token
      if (!receivedToken) {
        throw new Error('未收到认证令牌')
      }

      localStorage.setItem('token', receivedToken)
      token.value = receivedToken
      
      await fetchUser() 
      
      console.log('AuthStore: 登录成功!')
      return { success: true, error: null }
      
    } catch (error) {
      console.error('AuthStore: 登录失败!', error)
      let errorMessage = '登录失败，请稍后重试'
      if (error.response) {
        if (error.response.status === 400 || error.response.status === 401) {
          errorMessage = '用户名或密码错误'
        } else if (error.response.status >= 500) {
          errorMessage = '服务器错误，请稍后再试'
        }
      } else if (error.request) {
        errorMessage = '网络错误，请检查网络连接'
      }
      return { success: false, error: errorMessage }
    }
  }

  function logout() {
    console.log('AuthStore: 正在退出登录...')
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  // --- 【【【已修复】】】: 确保 user 对象的更新是响应式的 ---
  async function toggleFavorite(courseId) {
    if (!isAuthenticated.value) {
      alert('请先登录！')
      return { success: false, error: 'Not authenticated' }
    }

    try {
      const response = await apiClient.post(`/api/courses/${courseId}/favorite/`)
      const { favorited, favorites_list } = response.data
      
      if (user.value) {
        // 【【【关键修复】】】: 
        // 错误做法: user.value.favorited_courses = favorites_list (这不会触发更新)
        // 正确做法: 创建一个新对象来替换 user.value
        
        const updatedUser = { 
          ...user.value, 
          favorited_courses: favorites_list 
        };
        
        console.log('!!! AuthStore 正在更新 user ref (收藏) !!!');
        user.value = updatedUser; // 替换整个 user ref
        localStorage.setItem('user', JSON.stringify(updatedUser));
      }

      return { success: true, favorited: favorited }

    } catch (error) {
      console.error('切换收藏失败:', error)
      return { success: false, error: 'API error' }
    }
  }
  // --- 【【【修复结束】】】 ---

  return { 
    token, user, isAuthenticated, 
    login, logout, fetchUser,
    isCourseFavorited,
    toggleFavorite
  }
})