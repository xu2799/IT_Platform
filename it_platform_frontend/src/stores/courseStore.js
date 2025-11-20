import { ref } from 'vue'
import { defineStore } from 'pinia'
import apiClient from '@/api'

export const useCourseStore = defineStore('courses', () => {
  const courses = ref([])
  const categories = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  const isStale = ref(true)

  async function fetchCourses(params = {}) {
    // 简单的缓存策略：如果数据不陈旧且没有查询参数，直接返回
    if (!isStale.value && courses.value.length > 0 && !params.search && !params.category) {
      return
    }

    isLoading.value = true
    error.value = null
    try {
      const response = await apiClient.get('/api/courses/', { params })
      courses.value = response.data.results || response.data
      isStale.value = false
    } catch (err) {
      console.error('获取课程失败:', err)
      error.value = err.response?.data?.detail || '获取课程失败'
      courses.value = []
    } finally {
      isLoading.value = false
    }
  }

  async function fetchCourseDetail(courseId) {
    const existingCourse = courses.value.find(c => c.id == courseId)

    // 如果缓存中有完整的详情数据（包含模块信息），直接使用
    if (!isStale.value && existingCourse?.modules && existingCourse.is_liked !== undefined) {
      return existingCourse
    }

    try {
      const response = await apiClient.get(`/api/courses/${courseId}/`)
      const detailedCourse = response.data

      // 更新本地列表中的单一课程数据
      const index = courses.value.findIndex(c => c.id == detailedCourse.id)
      if (index !== -1) {
        const newCourses = [...courses.value]
        newCourses[index] = detailedCourse
        courses.value = newCourses
      } else {
        courses.value.push(detailedCourse)
      }
      return detailedCourse
    } catch (err) {
      console.error(`获取课程 ${courseId} 详情失败:`, err)
      throw err
    }
  }

  async function fetchCategories() {
    if (categories.value.length > 0) return
    try {
      const response = await apiClient.get('/api/categories/')
      categories.value = response.data.results || response.data
    } catch (err) {
      console.error('获取分类失败:', err)
    }
  }

  function markAsStale() {
    isStale.value = true
  }

  function updateCourseLikeStatus(courseId, liked, like_count) {
    const index = courses.value.findIndex(c => c.id == courseId)
    if (index !== -1) {
      const updatedCourse = { ...courses.value[index], is_liked: liked, like_count }
      courses.value.splice(index, 1, updatedCourse)
    }
  }

  function updateCourseFavoriteStatus(courseId, favorited) {
    const index = courses.value.findIndex(c => c.id == courseId)
    if (index !== -1) {
      const updatedCourse = { ...courses.value[index], is_favorited: favorited }
      courses.value.splice(index, 1, updatedCourse)
    }
  }

  return {
    courses,
    categories,
    isLoading,
    error,
    fetchCourses,
    fetchCourseDetail,
    fetchCategories,
    markAsStale,
    updateCourseLikeStatus,
    updateCourseFavoriteStatus
  }
})

export default useCourseStore