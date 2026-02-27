import { ref } from 'vue'
import { defineStore } from 'pinia'
import apiClient from '@/api'

export const useCourseStore = defineStore('courses', () => {
  const courses = ref([]) // 公开课程列表
  const instructorCourses = ref([]) // 【新增】讲师自己的课程列表
  const categories = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  const isStale = ref(true)

  // 1. 获取公开课程列表
  async function fetchCourses(params = {}) {
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

  // 2. 【新增】获取讲师自己的课程 (用于下拉框选择)
  async function fetchInstructorCourses() {
    isLoading.value = true
    try {
      const response = await apiClient.get('/api/instructor/courses/')
      instructorCourses.value = response.data.results || response.data
    } catch (err) {
      console.error('获取讲师课程失败:', err)
    } finally {
      isLoading.value = false
    }
  }

  // 3. 获取课程详情
  async function fetchCourseDetail(courseId, forceRefresh = false) {
    const existingCourse = courses.value.find(c => c.id == courseId)

    // 如果不是强制刷新，且数据未过期，且已有完整数据，则直接返回缓存
    if (!forceRefresh && !isStale.value && existingCourse?.modules && existingCourse.is_liked !== undefined) {
      return existingCourse
    }

    try {
      const response = await apiClient.get(`/api/courses/${courseId}/`)
      const detailedCourse = response.data

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

  // 4. 获取分类
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

  return {
    courses,
    instructorCourses, // 导出这个状态
    categories,
    isLoading,
    error,
    fetchCourses,
    fetchInstructorCourses, // 导出这个方法
    fetchCourseDetail,
    fetchCategories,
    markAsStale
  }
})

export default useCourseStore
