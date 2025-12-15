import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import apiClient from '@/api' // ✅ 使用封装好的 apiClient

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
    if (!token.value) return
    try {
      const response = await apiClient.get('/api/users/me/')
      const realUserData = response.data
      user.value = realUserData
      localStorage.setItem('user', JSON.stringify(realUserData))
    } catch (error) {
      console.error('获取用户信息失败', error)
      logout()
    }
  }

  async function login(username, password) {
    try {
      // ✅ 修改点：使用 apiClient.post，不需要手动拼写完整 URL
      // apiClient 会自动添加 baseURL (http://127.0.0.1:8000)
      const response = await apiClient.post('/api/token-auth/', {
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

      return { success: true, error: null }

    } catch (error) {
      console.error('登录请求失败:', error)
      let errorMessage = '登录失败，请检查网络或服务器状态'

      if (error.response) {
        // 服务器有返回，但状态码是 4xx/5xx
        if (error.response.status === 400 || error.response.status === 401) {
          errorMessage = '用户名或密码错误'
        } else {
          errorMessage = `服务器错误 (${error.response.status})`
        }
      } else if (error.request) {
        // 请求发出了，但没有收到响应 (通常是后端没开，或者跨域被拦截)
        errorMessage = '无法连接到服务器，请确保后台已启动'
      }

      return { success: false, error: errorMessage }
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  async function toggleFavorite(courseId) {
    if (!isAuthenticated.value) {
      alert('请先登录！')
      return { success: false, error: 'Not authenticated' }
    }

    try {
      const response = await apiClient.post(`/api/courses/${courseId}/favorite/`)
      const { favorited, favorites_list } = response.data

      if (user.value) {
        const updatedUser = {
          ...user.value,
          favorited_courses: favorites_list
        };
        user.value = updatedUser;
        localStorage.setItem('user', JSON.stringify(updatedUser));
      }

      return { success: true, favorited: favorited }

    } catch (error) {
      return { success: false, error: 'API error' }
    }
  }

  return {
    token, user, isAuthenticated,
    login, logout, fetchUser,
    isCourseFavorited,
    toggleFavorite
  }
})
