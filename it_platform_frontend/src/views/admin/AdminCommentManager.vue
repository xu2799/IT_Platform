<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import apiClient from '@/api'
import { formatDate } from '@/utils/common'

const comments = ref([])
const loading = ref(true)
const categories = ref([])
const courses = ref([])
const filterCategorySlug = ref('')
const filterCourseId = ref('')

// 根据分类筛选课程列表
const filteredCourses = computed(() => {
  if (!filterCategorySlug.value) return courses.value
  return courses.value.filter(c => c.category?.slug === filterCategorySlug.value)
})

// 获取分类列表
const fetchCategories = async () => {
  try {
    const res = await apiClient.get('/api/categories/')
    categories.value = res.data.results || res.data
  } catch (e) {
    console.error(e)
  }
}

// 获取所有课程用于筛选
const fetchCourses = async () => {
  try {
    const res = await apiClient.get('/api/courses/')
    courses.value = res.data.results || res.data
  } catch (e) {
    console.error(e)
  }
}

const fetchComments = async () => {
  loading.value = true
  try {
    const params = {}
    if (filterCourseId.value) {
      params.course_id = filterCourseId.value
    } else if (filterCategorySlug.value) {
      params.category = filterCategorySlug.value
    }
    // 后端 CommentViewSet 已修改为允许管理员获取所有
    const res = await apiClient.get('/api/comments/', { params })
    comments.value = res.data.results || res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

// 当分类变化时，重置课程筛选并刷新数据
watch(filterCategorySlug, () => {
  filterCourseId.value = ''
  fetchComments()
})

// 当课程变化时刷新评论列表
watch(filterCourseId, () => {
  fetchComments()
})

const handleDelete = async (id) => {
  if (!confirm('确定要删除这条评论吗？')) return
  try {
    await apiClient.delete(`/api/comments/${id}/`)
    comments.value = comments.value.filter(c => c.id !== id)
  } catch (e) {
    alert('删除失败')
  }
}

onMounted(() => {
  fetchCategories()
  fetchCourses()
  fetchComments()
})
</script>

<template>
  <div class="manager-view">
    <div class="toolbar">
      <div class="filter-box">
        <select v-model="filterCategorySlug">
          <option value="">所有分类</option>
          <option v-for="cat in categories" :key="cat.slug" :value="cat.slug">{{ cat.name }}</option>
        </select>
        <select v-model="filterCourseId">
          <option value="">所有课程</option>
          <option v-for="c in filteredCourses" :key="c.id" :value="c.id">{{ c.title }}</option>
        </select>
      </div>
    </div>
    
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th width="15%">用户</th>
            <th width="45%">内容</th>
            <th width="25%">来源</th>
            <th width="15%">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="comment in comments" :key="comment.id">
            <td class="fw-bold">{{ comment.user?.username || '未知' }}</td>
            <td>
              <div class="content-text">{{ comment.content }}</div>
              <div class="time-text">{{ formatDate(comment.created_at) }}</div>
            </td>
            <td class="source-text">
               课程ID: {{ comment.lesson }}
            </td>
            <td>
              <button @click="handleDelete(comment.id)" class="btn-sm danger">删除</button>
            </td>
          </tr>
          <tr v-if="comments.length === 0">
            <td colspan="4" class="text-center">暂无评论数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.manager-view { padding: 0; }
.toolbar { display: flex; justify-content: flex-end; margin-bottom: 15px; }
.filter-box { display: flex; gap: 10px; }
.filter-box select { padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; min-width: 150px; font-size: 0.9rem; }
.table-container { background: white; border-radius: 8px; border: 1px solid #e5e7eb; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #f3f4f6; vertical-align: top; }
th { background: #f9fafb; color: #374151; font-weight: 600; }
.content-text { color: #374151; margin-bottom: 4px; }
.time-text { font-size: 0.8rem; color: #9ca3af; }
.source-text { font-size: 0.9rem; color: #6b7280; }
.btn-sm { padding: 4px 10px; border-radius: 4px; border: none; cursor: pointer; font-size: 0.85rem; }
.btn-sm.danger { background: #fee2e2; color: #dc2626; }
.btn-sm.danger:hover { background: #fecaca; }
.fw-bold { font-weight: 600; }
.text-center { text-align: center; color: #999; padding: 30px; }
</style>
