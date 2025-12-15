<script setup>
import { ref, onMounted, computed } from 'vue'
import apiClient from '@/api'
import { formatDate, getFullMediaUrl } from '@/utils/common'
import { useAuthStore } from '@/stores/authStore'

const authStore = useAuthStore()
const users = ref([])
const loading = ref(true)
const searchQuery = ref('')

// 【新增】多选状态
const selectedIds = ref([])
const isBulkDeleting = ref(false)

// 编辑相关状态
const showEditModal = ref(false)
const isSaving = ref(false)
const editForm = ref({
  id: null,
  username: '',
  nickname: '',
  email: '',
  role: 'student',
  bio: '',
  is_active: true
})

// 计算属性：是否全选
const isAllSelected = computed(() => {
  return users.value.length > 0 && selectedIds.value.length === users.value.length
})

const fetchUsers = async () => {
  loading.value = true
  try {
    const params = searchQuery.value ? { search: searchQuery.value } : {}
    const res = await apiClient.get('/api/admin/users/', { params })
    users.value = res.data.results || res.data
    selectedIds.value = [] // 刷新后清空选择
  } catch (e) {
    console.error(e)
    alert('加载用户失败: ' + (e.response?.data?.detail || '权限不足'))
  } finally {
    loading.value = false
  }
}

// 【新增】全选/取消全选
const toggleSelectAll = (event) => {
  if (event.target.checked) {
    selectedIds.value = users.value.map(u => u.id)
  } else {
    selectedIds.value = []
  }
}

// 【新增】批量删除
const handleBulkDelete = async () => {
  if (selectedIds.value.length === 0) return
  if (!confirm(`确定要删除选中的 ${selectedIds.value.length} 个用户吗？此操作不可恢复！`)) return

  isBulkDeleting.value = true
  try {
    const res = await apiClient.post('/api/admin/users/bulk_delete/', { ids: selectedIds.value })
    alert(`成功删除 ${res.data.deleted} 个用户`)
    fetchUsers()
  } catch (e) {
    alert('批量删除失败: ' + (e.response?.data?.detail || '未知错误'))
  } finally {
    isBulkDeleting.value = false
  }
}

// 打开编辑弹窗
const handleEdit = (user) => {
  editForm.value = {
    id: user.id,
    username: user.username,
    nickname: user.nickname || '',
    email: user.email || '',
    role: user.role,
    bio: user.bio || '',
    is_active: user.is_active !== undefined ? user.is_active : true
  }
  showEditModal.value = true
}

// 提交更新
const saveUser = async () => {
  isSaving.value = true
  try {
    await apiClient.patch(`/api/admin/users/${editForm.value.id}/`, editForm.value)
    alert('修改成功！')
    showEditModal.value = false
    fetchUsers()
  } catch (e) {
    console.error(e)
    const errorData = e.response?.data
    let msg = '修改失败'
    if (errorData) msg += ': ' + JSON.stringify(errorData)
    alert(msg)
  } finally {
    isSaving.value = false
  }
}

const handleDelete = async (id, name) => {
  if (!confirm(`确定要删除用户 "${name}" 吗？该用户的所有数据（课程、评论）都将被清除！`)) return
  try {
    await apiClient.delete(`/api/admin/users/${id}/`)
    fetchUsers()
  } catch (e) {
    alert('删除失败')
  }
}

onMounted(fetchUsers)
</script>

<template>
  <div class="manager-view">
    <div class="toolbar">
      <div class="left-actions">
        <button
          v-if="selectedIds.length > 0"
          @click="handleBulkDelete"
          class="btn-danger bulk-btn"
          :disabled="isBulkDeleting"
        >
          🗑️ 批量删除 ({{ selectedIds.length }})
        </button>
      </div>

      <div class="search-wrapper">
        <input v-model="searchQuery" @keyup.enter="fetchUsers" placeholder="搜索用户名/邮箱..." class="search-input" />
        <button @click="fetchUsers" class="btn-primary">搜索</button>
      </div>
    </div>

    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th class="checkbox-col">
              <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" />
            </th>
            <th>ID</th>
            <th>用户</th>
            <th>角色</th>
            <th>邮箱</th>
            <th>注册时间</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id" :class="{ selected: selectedIds.includes(user.id) }">
            <td class="checkbox-col">
              <input
                v-if="user.id !== authStore.user?.id"
                type="checkbox"
                :value="user.id"
                v-model="selectedIds"
              />
            </td>
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
               <span v-if="user.is_active !== false" class="status-active">正常</span>
               <span v-else class="status-inactive">禁用</span>
            </td>
            <td class="actions">
              <button @click="handleEdit(user)" class="btn-text edit">编辑</button>
              <button v-if="user.role !== 'admin'" @click="handleDelete(user.id, user.username)" class="btn-text danger">删除</button>
            </td>
          </tr>
          <tr v-if="users.length === 0">
            <td colspan="8" class="empty">暂无用户数据</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal-content">
        <h3>编辑用户</h3>
        <form @submit.prevent="saveUser">
          <div class="form-group">
            <label>用户名 (必填)</label>
            <input v-model="editForm.username" required />
          </div>
          <div class="form-group">
            <label>昵称</label>
            <input v-model="editForm.nickname" />
          </div>
          <div class="form-group">
            <label>邮箱</label>
            <input v-model="editForm.email" type="email" />
          </div>
          <div class="form-group">
            <label>角色</label>
            <select v-model="editForm.role">
              <option value="student">学生</option>
              <option value="instructor">讲师</option>
              <option value="admin">管理员</option>
            </select>
          </div>
          <div class="form-group">
            <label>个人简介</label>
            <textarea v-model="editForm.bio" rows="3"></textarea>
          </div>
          <div class="form-group checkbox-group">
            <label>
              <input type="checkbox" v-model="editForm.is_active" />
              账号启用状态
            </label>
          </div>

          <div class="modal-actions">
            <button type="button" @click="showEditModal = false" class="btn-cancel">取消</button>
            <button type="submit" class="btn-save" :disabled="isSaving">
              {{ isSaving ? '保存中...' : '保存修改' }}
            </button>
          </div>
        </form>
      </div>
    </div>

  </div>
</template>

<style scoped>
.manager-view { padding: 0; }
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.search-wrapper { display: flex; gap: 10px; }
.search-input { padding: 10px 15px; border: 1px solid #d1d5db; border-radius: 6px; width: 300px; }
.btn-primary { background: #4f46e5; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: 600; }
.btn-primary:hover { background: #4338ca; }

/* 批量删除按钮 */
.bulk-btn { background: #dc2626; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: 600; transition: background 0.2s; }
.bulk-btn:hover { background: #b91c1c; }
.bulk-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.table-container { background: white; border-radius: 8px; border: 1px solid #e5e7eb; overflow: hidden; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #f3f4f6; font-size: 0.9rem; vertical-align: middle; }
th { background: #f9fafb; font-weight: 600; color: #374151; }

.checkbox-col { width: 40px; text-align: center; }
tr.selected { background-color: #f0fdfa; }

.user-cell { display: flex; align-items: center; gap: 10px; }
.avatar-sm { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; }
.text-xs { font-size: 0.75rem; }
.text-muted { color: #6b7280; }
.fw-bold { font-weight: 600; }

.role-badge { padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600; }
.role-badge.admin { background: #fee2e2; color: #ef4444; }
.role-badge.instructor { background: #e0e7ff; color: #4f46e5; }
.role-badge.student { background: #f3f4f6; color: #6b7280; }

.status-active { color: #10b981; font-weight: bold; font-size: 0.85rem; }
.status-inactive { color: #ef4444; font-weight: bold; font-size: 0.85rem; }

.actions { display: flex; gap: 10px; }
.btn-text { background: none; border: none; cursor: pointer; font-size: 0.9rem; }
.btn-text.edit { color: #3b82f6; }
.btn-text.edit:hover { text-decoration: underline; }
.btn-text.danger { color: #ef4444; }
.btn-text.danger:hover { text-decoration: underline; }
.empty { text-align: center; padding: 30px; color: #9ca3af; }

/* 模态框样式 */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.5); z-index: 100; display: flex; justify-content: center; align-items: center; }
.modal-content { background: white; padding: 30px; border-radius: 12px; width: 450px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
.modal-content h3 { margin-top: 0; margin-bottom: 20px; color: #1f2937; }
.form-group { margin-bottom: 15px; }
.form-group label { display: block; margin-bottom: 5px; font-weight: 600; font-size: 0.9rem; color: #374151; }
.form-group input, .form-group select, .form-group textarea { width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 6px; font-family: inherit; }
.checkbox-group label { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.checkbox-group input { width: auto; }

.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 25px; }
.btn-cancel { padding: 8px 16px; border: 1px solid #d1d5db; background: white; border-radius: 6px; cursor: pointer; }
.btn-save { padding: 8px 20px; background: #4f46e5; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; }
.btn-save:hover { background: #4338ca; }
.btn-save:disabled { opacity: 0.7; cursor: not-allowed; }
</style>
