<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '@/api'
import { formatDate, getFullMediaUrl } from '@/utils/common'

const users = ref([])
const loading = ref(true)
const searchQuery = ref('')

const fetchUsers = async () => {
  loading.value = true
  try {
    const params = searchQuery.value ? { search: searchQuery.value } : {}
    const res = await apiClient.get('/api/admin/users/', { params })
    users.value = res.data.results || res.data
  } catch (e) {
    console.error(e)
    alert('加载用户失败: ' + (e.response?.data?.detail || '权限不足'))
  } finally {
    loading.value = false
  }
}

const handleDelete = async (id, name) => {
  if (!confirm(`确定要删除用户 "${name}" 吗？该用户的所有数据（课程、评论）都将被清除！`)) return
  try {
    await apiClient.delete(`/api/admin/users/${id}/`)
    await fetchUsers()
  } catch (e) {
    alert('删除失败')
  }
}

onMounted(fetchUsers)
</script>

<template>
  <div class="manager-view">
    <div class="toolbar">
      <div class="search-wrapper">
        <input v-model="searchQuery" @keyup.enter="fetchUsers" placeholder="搜索用户名/邮箱..." class="search-input" />
        <button @click="fetchUsers" class="btn-primary">搜索</button>
      </div>
    </div>

    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>用户</th>
            <th>角色</th>
            <th>邮箱</th>
            <th>注册时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>#{{ user.id }}</td>
            <td class="user-cell">
              <img
                :src="user.avatar ? getFullMediaUrl(user.avatar) : `https://ui-avatars.com/api/?name=${user.username}&background=random`"
                class="avatar-sm"
              />
              <div>
                <div class="fw-bold">{{ user.nickname || user.username }}</div>
                <div class="text-xs text-muted">@{{ user.username }}</div>
              </div>
            </td>
            <td>
              <span :class="['role-badge', user.role === 'admin' ? 'admin' : (user.role === 'instructor' ? 'instructor' : 'student')]">
                {{ user.role === 'admin' ? '管理员' : (user.role === 'instructor' ? '讲师' : '学生') }}
              </span>
            </td>
            <td>{{ user.email || '-' }}</td>
            <td>{{ formatDate(user.date_joined) }}</td>
            <td>
              <button v-if="user.role !== 'admin'" @click="handleDelete(user.id, user.username)" class="btn-text danger">删除</button>
            </td>
          </tr>
          <tr v-if="users.length === 0">
            <td colspan="6" class="empty">暂无用户数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.manager-view { padding: 0; }
.toolbar { display: flex; margin-bottom: 20px; }
.search-wrapper { display: flex; gap: 10px; }
.search-input { padding: 10px 15px; border: 1px solid #d1d5db; border-radius: 6px; width: 300px; }
.btn-primary { background: #4f46e5; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: 600; }
.btn-primary:hover { background: #4338ca; }

.table-container { background: white; border-radius: 8px; border: 1px solid #e5e7eb; overflow: hidden; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #f3f4f6; font-size: 0.9rem; vertical-align: middle; }
th { background: #f9fafb; font-weight: 600; color: #374151; }

.user-cell { display: flex; align-items: center; gap: 10px; }
.avatar-sm { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; }
.text-xs { font-size: 0.75rem; }
.text-muted { color: #6b7280; }
.fw-bold { font-weight: 600; }

.role-badge { padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600; }
.role-badge.admin { background: #fee2e2; color: #ef4444; }
.role-badge.instructor { background: #e0e7ff; color: #4f46e5; }
.role-badge.student { background: #f3f4f6; color: #6b7280; }

.btn-text { background: none; border: none; cursor: pointer; font-size: 0.9rem; }
.btn-text.danger { color: #ef4444; }
.btn-text.danger:hover { text-decoration: underline; }
.empty { text-align: center; padding: 30px; color: #9ca3af; }
</style>
