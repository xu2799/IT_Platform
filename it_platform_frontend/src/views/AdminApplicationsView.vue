<script setup>
import { ref, onMounted } from 'vue'
// 【【【修改】】】: 导入 apiClient
import apiClient from '@/api'
import BackButton from '@/components/BackButton.vue'

// (API_URL 已移至 apiClient)
const applications = ref([])
const loading = ref(true)
const errorMessage = ref('')

const fetchApplications = async () => {
    loading.value = true
    errorMessage.value = ''
    try {
        // 【【【修改】】】: 使用 apiClient
        const response = await apiClient.get('/api/applications/')
        
        // --- 【【【BUG 修复】】】 ---
        // 原始代码: applications.value = response.data
        // 修复后: 我们需要的是 'results' 数组
        if (response.data.results) {
            applications.value = response.data.results
        } else {
            // 作为备用，以防分页被禁用
            applications.value = response.data
        }
        // --- 【【【修复结束】】】 ---
        
    } catch (error) {
        console.error('获取申请失败:', error.response?.data || error.message)
        errorMessage.value = '无法加载申请列表。'
    } finally {
        loading.value = false
    }
}

const handleApproval = async (application, newStatus) => {
    if (!confirm(`确定要 "${newStatus === 'approved' ? '批准' : '拒绝'}" ${application.user.username} 的申请吗？`)) {
        return
    }
    
    try {
        // 【【【修改】】】: 使用 apiClient
        const response = await apiClient.patch(`/api/applications/${application.id}/`, {
            status: newStatus
        })
        
        const index = applications.value.findIndex(app => app.id === application.id)
        if (index !== -1) {
            applications.value[index] = response.data
        }
        
    } catch (error) {
        console.error('审批失败:', error.response?.data || error.message)
        alert('操作失败！')
    }
}

onMounted(fetchApplications)

const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('zh-CN')
}
</script>

<template>
  <div class="admin-page">
    <BackButton 
      :fallback-route="{ name: 'courses' }" 
      text="返回课程列表"
      small
    />
    <h1>管理讲师申请</h1>

    <div v-if="loading">正在加载...</div>
    <div v-if="errorMessage" class="message error">{{ errorMessage }}</div>

    <table class="applications-table" v-if="applications.length > 0">
        <thead>
            <tr>
                <th>申请人</th>
                <th>申请时间</th>
                <th>状态</th>
                <th>申请理由</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="app in applications" :key="app.id">
                <td>{{ app.user.username }}</td>
                <td>{{ formatDate(app.created_at) }}</td>
                <td>
                    <span :class="`status-${app.status}`">{{ app.status }}</span>
                </td>
                <td class="justification">{{ app.justification }}</td>
                <td class="actions">
                    <div v-if="app.status === 'pending'">
                        <button @click="handleApproval(app, 'approved')" class="btn approve">
                            批准
                        </button>
                        <button @click="handleApproval(app, 'rejected')" class="btn reject">
                            拒绝
                        </button>
                    </div>
                    <div v-else>
                        (已处理)
                    </div>
                </td>
            </tr>
        </tbody>
    </table>
    
    <div v-if="!loading && applications.length === 0 && !errorMessage" class="no-results">
        <p>目前没有待处理的申请。</p>
    </div>
  </div>
</template>

<style scoped>
/* 样式部分 (完全不变) */
.admin-page { 
  max-width: 1000px; 
  margin: 20px auto; 
  padding: 20px; 
}
.admin-page h1 { 
  text-align: center; 
  margin-top: 0;
}
.applications-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
}
.applications-table th, .applications-table td {
    border: 1px solid #ddd;
    padding: 12px;
    text-align: left;
    vertical-align: top;
}
.applications-table th {
    background-color: #f4f4f4;
}
.justification {
    max-width: 300px;
    word-break: break-word;
    font-size: 0.9rem;
}
.actions {
    display: flex;
    flex-direction: column;
    gap: 10px;
    width: 100px;
}
.btn {
    padding: 8px 12px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    color: white;
}
.btn.approve { background-color: #28a745; }
.btn.reject { background-color: #dc3545; }
.status-pending { color: #f0ad4e; font-weight: bold; }
.status-approved { color: #28a745; font-weight: bold; }
.status-rejected { color: #dc3545; font-weight: bold; }
.message { padding: 15px; border-radius: 4px; margin-bottom: 15px; font-size: 1.1rem; text-align: center; }
.error { background-color: #f8d7da; color: #721c24; border-color: #f5c6cb; }

/* 【【【新增】】】 */
.no-results {
    text-align: center;
    padding: 40px;
    color: #777;
    font-size: 1.2rem;
}
</style>