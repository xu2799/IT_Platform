<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '@/api'
import { formatDate } from '@/utils/common'

const applications = ref([])
const loading = ref(true)

const fetchApplications = async () => {
    loading.value = true
    try {
        const response = await apiClient.get('/api/applications/')
        if (response.data.results) applications.value = response.data.results
        else applications.value = response.data
    } catch (error) {
        alert('加载失败')
    } finally {
        loading.value = false
    }
}

const handleApproval = async (application, newStatus) => {
    if (!confirm(`确定要 "${newStatus === 'approved' ? '批准' : '拒绝'}" 此申请吗？`)) return
    try {
        const response = await apiClient.patch(`/api/applications/${application.id}/`, { status: newStatus })
        const index = applications.value.findIndex(app => app.id === application.id)
        if (index !== -1) applications.value[index] = response.data
    } catch (error) {
        alert('操作失败')
    }
}

onMounted(fetchApplications)
</script>

<template>
  <div class="manager-view">
    <div class="table-container">
      <table>
        <thead>
            <tr>
                <th>申请人</th>
                <th>申请时间</th>
                <th>状态</th>
                <th width="40%">申请理由</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="app in applications" :key="app.id">
                <td class="fw-bold">{{ app.user.username }}</td>
                <td>{{ formatDate(app.created_at) }}</td>
                <td>
                    <span :class="['status-badge', app.status]">{{ app.status === 'pending' ? '待审核' : (app.status === 'approved' ? '已批准' : '已拒绝') }}</span>
                </td>
                <td class="reason">{{ app.justification }}</td>
                <td>
                    <div v-if="app.status === 'pending'" class="btn-group">
                        <button @click="handleApproval(app, 'approved')" class="btn-sm approve">批准</button>
                        <button @click="handleApproval(app, 'rejected')" class="btn-sm reject">拒绝</button>
                    </div>
                    <span v-else class="text-muted">--</span>
                </td>
            </tr>
            <tr v-if="!loading && applications.length === 0">
                <td colspan="5" class="empty">暂无待处理申请</td>
            </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
/* 复用表格样式 */
.table-container { background: white; border-radius: 8px; border: 1px solid #e5e7eb; overflow: hidden; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 15px; text-align: left; border-bottom: 1px solid #f3f4f6; font-size: 0.9rem; }
th { background: #f9fafb; font-weight: 600; color: #374151; }
.fw-bold { font-weight: 600; }
.reason { color: #4b5563; line-height: 1.5; }
.empty { text-align: center; padding: 30px; color: #9ca3af; }

.status-badge { padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
.status-badge.pending { background: #fef3c7; color: #d97706; }
.status-badge.approved { background: #d1fae5; color: #059669; }
.status-badge.rejected { background: #fee2e2; color: #dc2626; }

.btn-group { display: flex; gap: 8px; }
.btn-sm { border: none; padding: 6px 12px; border-radius: 4px; color: white; cursor: pointer; font-size: 0.8rem; transition: opacity 0.2s; }
.btn-sm:hover { opacity: 0.9; }
.approve { background: #10b981; }
.reject { background: #ef4444; }
.text-muted { color: #9ca3af; }
</style>
