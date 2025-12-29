<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import apiClient from '@/api'
import { formatDate, getFullMediaUrl } from '@/utils/common'

const activeTab = ref('assignments')
const assignments = ref([])
const submissions = ref([])
const courses = ref([])
const categories = ref([])
const loading = ref(false)
const filterCategorySlug = ref('')
const filterCourseId = ref('')

// 根据分类筛选课程列表
const filteredCourses = computed(() => {
  if (!filterCategorySlug.value) return courses.value
  return courses.value.filter(c => c.category?.slug === filterCategorySlug.value)
})

// 当分类变化时，重置课程筛选并刷新数据
watch(filterCategorySlug, () => {
  filterCourseId.value = ''
  if (activeTab.value === 'assignments') fetchAssignments()
  else fetchSubmissions()
})

// 详情弹窗
const showDetailModal = ref(false)
const currentSubmission = ref(null)
const customScore = ref(0) // 自定义分数

// 作业创建/编辑弹窗
const showAssignmentModal = ref(false)
const isEditMode = ref(false)
const isSaving = ref(false)
const assignmentForm = ref({
  id: null,
  title: '',
  description: '',
  course: '',
  assignment_type: 'file',
  quiz_data: ''
})

// 获取分类列表
const fetchCategories = async () => {
    try {
        const res = await apiClient.get('/api/categories/')
        categories.value = res.data.results || res.data
    } catch(e) {}
}

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
    const params = {}
    if (filterCourseId.value) params.course_id = filterCourseId.value
    else if (filterCategorySlug.value) params.category = filterCategorySlug.value
    const res = await apiClient.get('/api/assignments/', { params })
    assignments.value = res.data.results || res.data
  } catch (e) { console.error(e) } finally { loading.value = false }
}

const fetchSubmissions = async () => {
  loading.value = true
  try {
    const params = {}
    if (filterCourseId.value) params.course_id = filterCourseId.value
    else if (filterCategorySlug.value) params.category = filterCategorySlug.value
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

// ===== 作业 CRUD 操作 =====
const openCreateModal = () => {
  isEditMode.value = false
  assignmentForm.value = {
    id: null,
    title: '',
    description: '',
    course: filterCourseId.value || '',
    assignment_type: 'file',
    quiz_data: ''
  }
  showAssignmentModal.value = true
}

const openEditModal = (assign) => {
  isEditMode.value = true
  assignmentForm.value = {
    id: assign.id,
    title: assign.title,
    description: assign.description || '',
    course: assign.course,
    assignment_type: assign.assignment_type,
    quiz_data: assign.quiz_data || ''
  }
  showAssignmentModal.value = true
}

const saveAssignment = async () => {
  if (!assignmentForm.value.title || !assignmentForm.value.course) {
    return alert('请填写作业标题并选择课程')
  }
  isSaving.value = true
  try {
    const data = {
      title: assignmentForm.value.title,
      description: assignmentForm.value.description,
      course: assignmentForm.value.course,
      assignment_type: assignmentForm.value.assignment_type,
      quiz_data: assignmentForm.value.quiz_data
    }
    if (isEditMode.value) {
      await apiClient.patch(`/api/assignments/${assignmentForm.value.id}/`, data)
      alert('作业更新成功')
    } else {
      await apiClient.post('/api/assignments/', data)
      alert('作业创建成功')
    }
    showAssignmentModal.value = false
    fetchAssignments()
  } catch (e) {
    console.error(e)
    alert('保存失败: ' + (e.response?.data?.detail || '未知错误'))
  } finally {
    isSaving.value = false
  }
}

const deleteAssignment = async (assign) => {
  if (!confirm(`确定要删除作业 "${assign.title}" 吗？相关的学生提交也会被删除！`)) return
  try {
    await apiClient.delete(`/api/assignments/${assign.id}/`)
    alert('删除成功')
    fetchAssignments()
  } catch (e) {
    alert('删除失败')
  }
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
  fetchCategories()
  fetchCourses()
  fetchAssignments()
})
</script>

<template>
  <div class="manager-view">
    <div class="toolbar">
        <div class="tabs">
            <button :class="{ active: activeTab === 'assignments' }" @click="switchTab('assignments')">作业列表</button>
            <button :class="{ active: activeTab === 'submissions' }" @click="switchTab('submissions')">提交记录</button>
        </div>
        <div class="toolbar-right">
            <button v-if="activeTab === 'assignments'" @click="openCreateModal" class="btn-create">+ 创建作业</button>
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
    </div>

    <div v-if="loading" class="loading">正在加载数据...</div>

    <!-- 作业列表 -->
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
            <th>操作</th>
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
            <td class="actions">
              <button @click="openEditModal(assign)" class="btn-sm btn-edit">编辑</button>
              <button @click="deleteAssignment(assign)" class="btn-sm btn-delete">删除</button>
            </td>
          </tr>
          <tr v-if="assignments.length === 0"><td colspan="7" class="empty">暂无作业记录</td></tr>
        </tbody>
      </table>
    </div>

    <!-- 提交记录 -->
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
            <td><span :class="['status-badge', sub.status]">{{ sub.status === 'pending' ? '待审核' : (sub.status === 'passed' ? '已通过' : '已驳回') }}</span></td>
            <td>{{ sub.grade !== null ? sub.grade + '分' : '-' }}</td>
            <td>
                <button @click="viewSubmission(sub)" class="btn-sm btn-view">查看/批改</button>
            </td>
          </tr>
          <tr v-if="submissions.length === 0"><td colspan="8" class="empty">暂无提交记录</td></tr>
        </tbody>
      </table>
    </div>

    <!-- 作业创建/编辑弹窗 -->
    <div v-if="showAssignmentModal" class="modal-overlay" @click.self="showAssignmentModal = false">
        <div class="modal-content">
            <h3>{{ isEditMode ? '编辑作业' : '创建作业' }}</h3>
            <form @submit.prevent="saveAssignment">
                <div class="form-group">
                    <label>作业标题 *</label>
                    <input v-model="assignmentForm.title" required placeholder="请输入作业标题" />
                </div>
                <div class="form-group">
                    <label>所属课程 *</label>
                    <select v-model="assignmentForm.course" required>
                        <option value="">请选择课程</option>
                        <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.title }}</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>作业类型</label>
                    <select v-model="assignmentForm.assignment_type">
                        <option value="file">文件提交</option>
                        <option value="choice">选择题</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>作业描述</label>
                    <textarea v-model="assignmentForm.description" rows="3" placeholder="作业要求说明..."></textarea>
                </div>
                <div v-if="assignmentForm.assignment_type === 'choice'" class="form-group">
                    <label>题目数据 (JSON格式)</label>
                    <textarea v-model="assignmentForm.quiz_data" rows="5" placeholder='[{"question":"题目1","options":["A","B","C","D"],"answer":"A"}]'></textarea>
                </div>
                <div class="modal-actions">
                    <button type="button" @click="showAssignmentModal = false" class="btn-cancel">取消</button>
                    <button type="submit" class="btn-save" :disabled="isSaving">
                        {{ isSaving ? '保存中...' : (isEditMode ? '更新作业' : '创建作业') }}
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- 提交详情弹窗 -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
        <div class="modal-content">
            <h3>提交详情</h3>
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
.toolbar-right { display: flex; align-items: center; gap: 15px; }
.tabs { display: flex; gap: 10px; }
.tabs button { padding: 8px 16px; background: transparent; border: none; font-size: 1rem; color: #6b7280; cursor: pointer; border-bottom: 2px solid transparent; }
.tabs button.active { color: #4f46e5; border-bottom-color: #4f46e5; font-weight: 600; }
.filter-box { display: flex; gap: 10px; }
.filter-box select { padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px; min-width: 120px; }

.btn-create { background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; transition: background 0.2s; }
.btn-create:hover { background: #059669; }

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

.actions { display: flex; gap: 8px; }
.btn-sm { padding: 4px 10px; border-radius: 4px; cursor: pointer; border: none; font-size: 0.85rem; }
.btn-view { background: #3b82f6; color: white; }
.btn-edit { background: #f59e0b; color: white; }
.btn-delete { background: #ef4444; color: white; }
.btn-edit:hover { background: #d97706; }
.btn-delete:hover { background: #dc2626; }

/* Form Styles */
.form-group { margin-bottom: 15px; }
.form-group label { display: block; margin-bottom: 5px; font-weight: 600; font-size: 0.9rem; color: #374151; }
.form-group input, .form-group select, .form-group textarea { width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 6px; font-family: inherit; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
.btn-cancel { padding: 8px 16px; border: 1px solid #d1d5db; background: white; border-radius: 6px; cursor: pointer; }
.btn-save { padding: 8px 20px; background: #4f46e5; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; }
.btn-save:hover { background: #4338ca; }
.btn-save:disabled { opacity: 0.7; cursor: not-allowed; }

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
.modal-content h3 { margin-top: 0; margin-bottom: 20px; color: #1f2937; }
.detail-row { margin-bottom: 15px; }
.detail-row label { font-weight: bold; margin-right: 10px; }
.text-content { background: #f9f9f9; padding: 10px; border-radius: 4px; max-height: 150px; overflow-y: auto; white-space: pre-wrap; }
.btn-download { background: #f59e0b; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; }
.divider { border: 0; border-top: 1px solid #eee; margin: 20px 0; }
.modal-footer { text-align: right; margin-top: 10px; }
.btn-close { background: #eee; border: none; padding: 8px 20px; border-radius: 4px; cursor: pointer; }
</style>
