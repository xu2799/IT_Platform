<script setup>
import { ref, onMounted, computed } from 'vue'
import { useCourseStore } from '@/stores/courseStore'
import apiClient from '@/api'
import { useRouter } from 'vue-router'
import { formatDate, getFullCoverImagePath } from '@/utils/common'

const router = useRouter()
const courseStore = useCourseStore()
const searchQuery = ref('')
const isDeleting = ref(false)

// 初始化加载课程数据
onMounted(() => {
  courseStore.fetchCourses()
})

// 前端搜索过滤
const filteredCourses = computed(() => {
  if (!searchQuery.value) return courseStore.courses
  const q = searchQuery.value.toLowerCase()
  return courseStore.courses.filter(c =>
    c.title.toLowerCase().includes(q) ||
    (c.instructor?.username || '').toLowerCase().includes(q)
  )
})

// 删除课程
const handleDelete = async (id, title) => {
  if (!confirm(`确定要永久删除课程 "${title}" 吗？此操作不可撤销！`)) return
  isDeleting.value = true
  try {
    await apiClient.delete(`/api/courses/${id}/`)
    courseStore.markAsStale()
    await courseStore.fetchCourses()
    alert('删除成功')
  } catch (error) {
    alert('删除失败: ' + (error.response?.data?.detail || '未知错误'))
  } finally {
    isDeleting.value = false
  }
}

const handleImageError = (e) => {
  e.target.src = 'https://via.placeholder.com/50x30?text=No+Img'
}
</script>

<template>
  <div class="manager-view">
    <div class="toolbar">
      <div class="search-box">
        <input v-model="searchQuery" placeholder="搜索课程标题或讲师..." />
      </div>
      <button @click="router.push({ name: 'create-course' })" class="btn-add">
        + 发布新课程
      </button>
    </div>

    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th width="60">ID</th>
            <th width="80">封面</th>
            <th>课程标题</th>
            <th>分类</th>
            <th>讲师</th>
            <th>数据 (阅/赞)</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="course in filteredCourses" :key="course.id">
            <td>#{{ course.id }}</td>
            <td>
              <img
                :src="getFullCoverImagePath(course.cover_image)"
                class="thumb"
                @error="handleImageError"
              />
            </td>
            <td class="fw-bold">{{ course.title }}</td>
            <td><span class="tag">{{ course.category?.name || '未分类' }}</span></td>
            <td>
              <div class="instructor-info">
                <span>{{ course.instructor?.nickname || course.instructor?.username || '未知' }}</span>
              </div>
            </td>
            <td>{{ course.view_count }} / {{ course.like_count }}</td>
            <td>{{ formatDate(course.created_at) }}</td>
            <td class="actions">
              <button @click="router.push({ name: 'course-edit', params: { id: course.id } })" class="btn-icon edit" title="编辑">✏️</button>
              <button @click="handleDelete(course.id, course.title)" class="btn-icon del" title="删除" :disabled="isDeleting">🗑️</button>
            </td>
          </tr>
          <tr v-if="filteredCourses.length === 0">
            <td colspan="8" class="empty">暂无课程数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
/* 通用样式，保证风格统一 */
.toolbar { display: flex; justify-content: space-between; margin-bottom: 20px; }
.search-box input { padding: 10px 15px; border: 1px solid #d1d5db; border-radius: 6px; width: 300px; }
.btn-add { background: #10b981; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: 600; cursor: pointer; }
.btn-add:hover { background: #059669; }

.table-container { background: white; border-radius: 8px; border: 1px solid #e5e7eb; overflow: hidden; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #f3f4f6; font-size: 0.9rem; vertical-align: middle; }
th { background: #f9fafb; font-weight: 600; color: #374151; }

.thumb { width: 60px; height: 40px; object-fit: cover; border-radius: 4px; border: 1px solid #eee; }
.tag { background: #e0e7ff; color: #4f46e5; padding: 2px 8px; border-radius: 10px; font-size: 0.8rem; display: inline-block; }
.fw-bold { font-weight: 600; color: #111827; }
.actions { display: flex; gap: 8px; }
.btn-icon { border: none; background: none; cursor: pointer; font-size: 1.1rem; transition: transform 0.2s; }
.btn-icon:hover { transform: scale(1.1); }
.empty { text-align: center; padding: 30px; color: #9ca3af; }
</style>
