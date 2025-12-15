<script setup>
import { ref, onMounted, watch } from 'vue'
import apiClient from '@/api'
import { formatDate, getFullMediaUrl } from '@/utils/common'

const activeTab = ref('submissions')
const assignments = ref([])
const submissions = ref([])
const courses = ref([])
const loading = ref(false)
const filterCourseId = ref('')

// 详情弹窗
const showDetailModal = ref(false)
const currentSubmission = ref(null)
const customScore = ref(0) // 自定义分数

// 获取所有课程用于筛选
const fetchCourses = async () => {
    try {
        const res = await apiClient.get('/api/courses/')
        courses.value = res.data.results || res.data
    } catch(e) {}
}

const fetchAssignments = async () => {
  loading.value = true
  try {
    const params = filterCourseId.value ? { course_id: filterCourseId.value } : {}
    const res = await apiClient.get('/api/assignments/', { params })
    assignments.value = res.data.results || res.data
  } catch (e) { console.error(e) } finally { loading.value = false }
}

const fetchSubmissions = async () => {
  loading.value = true
  try {
    const params = filterCourseId.value ? { course_id: filterCourseId.value } : {}
    const res = await apiClient.get('/api/submissions/', { params })
    submissions.value = res.data.results || res.data
  } catch (e) { console.error(e) } finally { loading.value = false }
}

const switchTab = (tab) => {
  activeTab.value = tab
  if (tab === 'assignments') fetchAssignments()
  else fetchSubmissions()
}

watch(filterCourseId, () => {
    if (activeTab.value === 'assignments') fetchAssignments()
    else fetchSubmissions()
})

const viewSubmission = (sub) => {
    currentSubmission.value = sub
    customScore.value = sub.grade !== null ? sub.grade : 60
    showDetailModal.value = true
}

const handleGrade = async (sub, status, grade) => {
  try {
    await apiClient.patch(`/api/submissions/${sub.id}/`, { status, grade })
    alert('操作成功')
    showDetailModal.value = false
    fetchSubmissions()
  } catch (e) { alert('操作失败') }
}

const confirmCustomGrade = () => {
    if (customScore.value < 0 || customScore.value > 100) return alert('分数无效')
    const status = customScore.value >= 60 ? 'passed' : 'rejected'
    handleGrade(currentSubmission.value, status, customScore.value)
}

const downloadFile = (url) => { window.open(getFullMediaUrl(url), '_blank') }
const parseAnswer = (jsonStr) => {
    try {
        const obj = JSON.parse(jsonStr)
        if (typeof obj === 'object') return Object.entries(obj).map(([idx, ans]) => `${parseInt(idx)+1}:${ans}`).join(', ')
        return jsonStr
    } catch { return jsonStr }
}

onMounted(() => {
  fetchCourses()
  fetchSubmissions()
})
</script>

<template>
  <div class="manager-view">
    <div class="toolbar">
        <div class="tabs">
            <button :class="{ active: activeTab === 'submissions' }" @click="switchTab('submissions')">最新提交监控</button>
            <button :class="{ active: activeTab === 'assignments' }" @click="switchTab('assignments')">作业发布列表</button>
        </div>
        <div class="filter-box">
            <select v-model="filterCourseId">
                <option value="">所有课程</option>
                <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.title }}</option>
            </select>
        </div>
    </div>

    <div v-if="loading" class="loading">正在加载数据...</div>

    <div v-if="!loading && activeTab === 'submissions'" class="table-container">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>学生</th>
            <th>作业标题</th>
            <th>所属课程</th>
            <th>类型</th>
            <th>状态</th>
            <th>评分</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="sub in submissions" :key="sub.id">
            <td>#{{ sub.id }}</td>
            <td class="fw-bold">{{ sub.student?.nickname || sub.student?.username }}</td>
            <td>{{ sub.assignment_title }}</td>
            <td>{{ sub.course_title }}</td>
            <td><span class="tag">{{ sub.assignment_type === 'choice' ? '选择题' : '文件' }}</span></td>
            <td><span :class="['status-badge', sub.status]">{{ sub.status }}</span></td>
            <td>{{ sub.grade !== null ? sub.grade + '分' : '-' }}</td>
            <td>
                <button @click="viewSubmission(sub)" class="btn-sm btn-view">查看/批改</button>
            </td>
          </tr>
          <tr v-if="submissions.length === 0"><td colspan="8" class="empty">暂无记录</td></tr>
        </tbody>
      </table>
    </div>

    <div v-if="!loading && activeTab === 'assignments'" class="table-container">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>作业标题</th>
            <th>所属课程</th>
            <th>类型</th>
            <th>提交数</th>
            <th>发布时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="assign in assignments" :key="assign.id">
            <td>#{{ assign.id }}</td>
            <td class="fw-bold">{{ assign.title }}</td>
            <td>{{ assign.course_title }}</td>
            <td><span class="tag">{{ assign.assignment_type === 'choice' ? '选择题' : '文件' }}</span></td>
            <td>{{ assign.submission_count }}</td>
            <td>{{ formatDate(assign.created_at) }}</td>
          </tr>
          <tr v-if="assignments.length === 0"><td colspan="6" class="empty">暂无记录</td></tr>
        </tbody>
      </table>
    </div>

    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
        <div class="modal-content">
            <h3>作业详情</h3>
            <div class="detail-row"><label>学生：</label> {{ currentSubmission.student?.username }}</div>
            <div class="detail-row"><label>内容：</label>
                <div v-if="currentSubmission.assignment_type === 'choice'" class="answer-box">
                    {{ parseAnswer(currentSubmission.content) }}
                </div>
                <div v-else class="text-content">{{ currentSubmission.content }}</div>
            </div>
            <div class="detail-row" v-if="currentSubmission.attachment">
                <label>附件：</label>
                <button @click="downloadFile(currentSubmission.attachment)" class="btn-download">⬇️ 下载附件</button>
            </div>

            <hr class="divider">

            <div class="grading-section">
                <h4>评分操作</h4>
                <div class="grade-input-row">
                    <label>给予分数 (0-100):</label>
                    <input type="number" v-model="customScore" class="score-input" min="0" max="100">
                    <button @click="confirmCustomGrade" class="btn-confirm-grade">确认打分</button>
                </div>

                <div class="quick-actions">
                    <span class="label">快捷操作：</span>
                    <button @click="handleGrade(currentSubmission, 'passed', 100)" class="btn-pass">💯 满分</button>
                    <button @click="handleGrade(currentSubmission, 'rejected', 0)" class="btn-reject">⭕ 0分</button>
                </div>
            </div>

            <div class="modal-footer">
                <button @click="showDetailModal = false" class="btn-close">关闭</button>
            </div>
        </div>
    </div>
  </div>
</template>

<style scoped>
.manager-view { padding: 0; }
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #e5e7eb; padding-bottom: 10px; }
.tabs { display: flex; gap: 10px; }
.tabs button { padding: 8px 16px; background: transparent; border: none; font-size: 1rem; color: #6b7280; cursor: pointer; border-bottom: 2px solid transparent; }
.tabs button.active { color: #4f46e5; border-bottom-color: #4f46e5; font-weight: 600; }
.filter-box select { padding: 6px; border: 1px solid #ddd; border-radius: 4px; }

.table-container { background: white; border-radius: 8px; border: 1px solid #e5e7eb; overflow: hidden; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #f3f4f6; }
th { background: #f9fafb; font-weight: 600; color: #374151; }
.fw-bold { font-weight: 600; color: #111827; }
.tag { background: #e0e7ff; color: #4f46e5; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; }
.status-badge { padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600; }
.status-badge.pending { background: #fef3c7; color: #d97706; }
.status-badge.passed { background: #d1fae5; color: #059669; }
.status-badge.rejected { background: #fee2e2; color: #dc2626; }
.empty { text-align: center; padding: 30px; color: #9ca3af; }
.loading { text-align: center; color: #6b7280; margin: 20px; }

.btn-sm { padding: 4px 10px; border-radius: 4px; cursor: pointer; border: none; }
.btn-view { background: #3b82f6; color: white; }

/* Grading Styles */
.grading-section { background: #f8fafc; padding: 15px; border-radius: 6px; margin-top: 20px; border: 1px solid #e2e8f0; }
.grading-section h4 { margin: 0 0 10px 0; font-size: 1rem; color: #334155; }
.grade-input-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.score-input { width: 80px; padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px; text-align: center; font-weight: bold; }
.btn-confirm-grade { background: #4f46e5; color: white; border: none; padding: 6px 15px; border-radius: 4px; cursor: pointer; }
.quick-actions { display: flex; align-items: center; gap: 10px; border-top: 1px dashed #cbd5e1; padding-top: 10px; }
.quick-actions .label { font-size: 0.85rem; color: #64748b; }
.btn-pass { background: #10b981; color: white; border: none; padding: 5px 12px; border-radius: 4px; cursor: pointer; font-size: 0.85rem; }
.btn-reject { background: #ef4444; color: white; border: none; padding: 5px 12px; border-radius: 4px; cursor: pointer; font-size: 0.85rem; }

/* Modal */
.modal-overlay { position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-content { background: white; padding: 25px; border-radius: 8px; width: 500px; max-width: 90%; max-height: 90vh; overflow-y: auto; }
.detail-row { margin-bottom: 15px; }
.detail-row label { font-weight: bold; margin-right: 10px; }
.text-content { background: #f9f9f9; padding: 10px; border-radius: 4px; max-height: 150px; overflow-y: auto; white-space: pre-wrap; }
.btn-download { background: #f59e0b; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; }
.divider { border: 0; border-top: 1px solid #eee; margin: 20px 0; }
.modal-footer { text-align: right; margin-top: 10px; }
.btn-close { background: #eee; border: none; padding: 8px 20px; border-radius: 4px; cursor: pointer; }
</style>
