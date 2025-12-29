<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import apiClient from '@/api'
import { useCourseStore } from '@/stores/courseStore'
import { getFullMediaUrl } from '@/utils/common'

const courseStore = useCourseStore()
const assignments = ref([])
const submissions = ref([])
const activeTab = ref('list')

// 筛选状态
const filterCategorySlug = ref('')
const filterCourseId = ref('')

// 根据分类筛选课程列表
const filteredCourses = computed(() => {
  if (!filterCategorySlug.value) return courseStore.instructorCourses
  return courseStore.instructorCourses.filter(c => c.category?.slug === filterCategorySlug.value)
})

// 当分类变化时，重置课程筛选并刷新数据
watch(filterCategorySlug, () => {
  filterCourseId.value = ''
  if (activeTab.value === 'list') fetchAssignments()
  if (activeTab.value === 'review') fetchSubmissions()
})

// 详情弹窗状态
const showDetailModal = ref(false)
const currentSubmission = ref(null)
const customScore = ref(0) // 【新增】自定义分数绑定

// 表单数据 (发布作业)
const newAssign = ref({
    course: '',
    title: '',
    description: '请完成以下选择题',
    assignment_type: 'regular'
})
const quizList = ref([{ question: '', options: { A: '', B: '', C: '', D: '' }, answer: 'A' }])
const assignmentFile = ref(null)

// 获取数据
const fetchAssignments = async () => {
  try {
    const params = {}
    if (filterCourseId.value) params.course_id = filterCourseId.value
    else if (filterCategorySlug.value) params.category = filterCategorySlug.value
    const res = await apiClient.get('/api/assignments/', { params })
    assignments.value = res.data.results || res.data
  } catch (e) { console.error(e) }
}

const fetchSubmissions = async () => {
  try {
    const params = {}
    if (filterCourseId.value) params.course_id = filterCourseId.value
    else if (filterCategorySlug.value) params.category = filterCategorySlug.value
    const res = await apiClient.get('/api/submissions/', { params })
    submissions.value = res.data.results || res.data
  } catch (e) { console.error(e) }
}

// 监听筛选变化
watch(filterCourseId, () => {
    if (activeTab.value === 'list') fetchAssignments()
    if (activeTab.value === 'review') fetchSubmissions()
})

const handleFileChange = (event) => { assignmentFile.value = event.target.files ? event.target.files[0] : null }

const addQuestion = () => {
    quizList.value.push({ question: '', options: { A: '', B: '', C: '', D: '' }, answer: 'A' })
    setTimeout(() => {
        const container = document.querySelector('.quiz-builder');
        if(container) container.scrollTop = container.scrollHeight;
    }, 100)
}
const removeQuestion = (index) => { if (quizList.value.length > 1) quizList.value.splice(index, 1) }

const handleCreate = async () => {
    if (!newAssign.value.course) return alert('请选择课程')
    if (!newAssign.value.title) return alert('请填写标题')

    const formData = new FormData()
    formData.append('course', newAssign.value.course)
    formData.append('title', newAssign.value.title)
    formData.append('description', newAssign.value.description)
    formData.append('assignment_type', newAssign.value.assignment_type)
    if (newAssign.value.assignment_type === 'choice') formData.append('quiz_data', JSON.stringify(quizList.value))
    if (assignmentFile.value) formData.append('attachment', assignmentFile.value)

    try {
        await apiClient.post('/api/assignments/', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
        alert('发布成功');
        // 重置表单
        newAssign.value = { course: '', title: '', description: '请完成以下选择题', assignment_type: 'regular' }
        quizList.value = [{ question: '', options: { A: '', B: '', C: '', D: '' }, answer: 'A' }]
        assignmentFile.value = null
        activeTab.value = 'list';
        fetchAssignments()
    } catch (e) { alert('发布失败: ' + (e.response?.data?.detail || '未知错误')) }
}

const handleGrade = async (sub, status, grade) => {
  try {
    await apiClient.patch(`/api/submissions/${sub.id}/`, { status, grade })
    alert('操作成功')
    showDetailModal.value = false
    fetchSubmissions()
  } catch (e) {
      console.error(e)
      alert('操作失败: ' + (e.response?.data?.detail || '未知错误'))
  }
}

// 查看详情
const viewSubmission = (sub) => {
    currentSubmission.value = sub
    // 【新增】初始化分数为已有分数或60分
    customScore.value = sub.grade !== null ? sub.grade : 60
    showDetailModal.value = true
}

// 【新增】确认自定义打分
const confirmCustomGrade = () => {
    if (customScore.value < 0 || customScore.value > 100) {
        return alert('分数必须在 0-100 之间')
    }
    // 自动判定：>=60 通过，<60 需修改
    const status = customScore.value >= 60 ? 'passed' : 'rejected'
    handleGrade(currentSubmission.value, status, customScore.value)
}

const parseAnswer = (jsonStr) => {
    try {
        const obj = JSON.parse(jsonStr)
        if (typeof obj === 'object') return Object.entries(obj).map(([idx, ans]) => `${parseInt(idx)+1}:${ans}`).join(', ')
        return jsonStr
    } catch { return jsonStr }
}

const downloadFile = (url) => { window.open(getFullMediaUrl(url), '_blank') }

onMounted(async () => {
  await courseStore.fetchCategories()
  await courseStore.fetchInstructorCourses()
  await fetchAssignments()
  await fetchSubmissions()
})
</script>

<template>
  <div class="assign-panel">
    <div class="panel-header">
      <div class="toolbar">
        <button :class="{active: activeTab === 'list'}" @click="activeTab = 'list'">作业列表</button>
        <button :class="{active: activeTab === 'create'}" @click="activeTab = 'create'">+ 发布新作业</button>
        <button :class="{active: activeTab === 'review'}" @click="activeTab = 'review'">批改作业</button>
      </div>

      <div class="filter-box" v-if="activeTab !== 'create'">
          <select v-model="filterCategorySlug">
              <option value="">所有分类</option>
              <option v-for="cat in courseStore.categories" :key="cat.slug" :value="cat.slug">{{ cat.name }}</option>
          </select>
          <select v-model="filterCourseId">
              <option value="">所有课程</option>
              <option v-for="c in filteredCourses" :key="c.id" :value="c.id">{{ c.title }}</option>
          </select>
      </div>
    </div>

    <div v-if="activeTab === 'list'" class="list-view">
      <div v-for="a in assignments" :key="a.id" class="item-card">
        <div class="card-top">
            <h4>{{ a.title }} <span class="course-badge">{{ a.course_title }}</span></h4>
            <span class="type-tag">{{ a.assignment_type === 'choice' ? '选择题' : '文件' }}</span>
        </div>
        <p class="sub">提交数: {{ a.submission_count }} | 发布时间: {{ new Date(a.created_at).toLocaleDateString() }}</p>
      </div>
      <div v-if="assignments.length === 0" class="empty">暂无作业</div>
    </div>

    <div v-if="activeTab === 'create'" class="create-view">
        <div class="form-group"><label>选择课程</label><select v-model="newAssign.course"><option v-for="c in courseStore.instructorCourses" :key="c.id" :value="c.id">{{ c.title }}</option></select></div>
        <div class="form-group"><label>类型</label><select v-model="newAssign.assignment_type"><option value="regular">图文/文件</option><option value="choice">选择题</option></select></div>
        <div class="form-group"><label>标题</label><input v-model="newAssign.title"></div>
        <div class="form-group" v-if="newAssign.assignment_type === 'regular'"><label>描述</label><textarea v-model="newAssign.description"></textarea></div>

        <div v-if="newAssign.assignment_type === 'choice'" class="quiz-builder">
            <h4>题目列表</h4>
            <div v-for="(item, index) in quizList" :key="index" class="quiz-item">
                <div class="quiz-header"><span>第 {{ index + 1 }} 题</span><button class="btn-del" @click="removeQuestion(index)">删除</button></div>
                <div class="form-group"><input v-model="item.question" placeholder="题目内容..." class="q-input" /></div>
                <div class="options-grid">
                    <div class="opt-row" v-for="opt in ['A', 'B', 'C', 'D']" :key="opt"><span class="opt-label">{{ opt }}</span><input v-model="item.options[opt]" /></div>
                </div>
                <div class="form-group correct-ans"><label>答案：</label><select v-model="item.answer"><option value="A">A</option><option value="B">B</option><option value="C">C</option><option value="D">D</option></select></div>
            </div>
            <button class="btn-add-q" @click="addQuestion">+ 添加题目</button>
        </div>

        <div class="form-group" v-if="newAssign.assignment_type === 'regular'"><label>附件</label><input type="file" @change="handleFileChange"></div>
        <button class="btn-submit" @click="handleCreate">发布</button>
    </div>

    <div v-if="activeTab === 'review'" class="review-view">
      <table class="table">
        <thead><tr><th>课程</th><th>学生</th><th>作业</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="s in submissions" :key="s.id">
            <td>{{ s.course_title }}</td>
            <td>{{ s.student?.nickname || s.student?.username }}</td>
            <td>{{ s.assignment_title }}</td>
            <td>
                <span :class="s.status">{{ s.status === 'passed'?'通过':(s.status==='rejected'?'打回':'待批改') }}</span>
                <span v-if="s.grade !== null"> ({{ s.grade }}分)</span>
            </td>
            <td>
              <button @click="viewSubmission(s)" class="btn-view">查看/评分</button>
            </td>
          </tr>
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
                <p class="hint-text">* 分数 ≥ 60 将自动标记为“通过”，否则为“需修改”</p>

                <div class="quick-actions">
                    <span class="label">快捷操作：</span>
                    <button @click="handleGrade(currentSubmission, 'passed', 100)" class="btn-pass">💯 满分通过</button>
                    <button @click="handleGrade(currentSubmission, 'rejected', 0)" class="btn-reject">⭕ 0分打回</button>
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
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 15px; }
.toolbar button { margin-right: 10px; padding: 6px 15px; border-radius: 20px; border:none; cursor: pointer; background: #f3f4f6; }
.toolbar button.active { background: #4f46e5; color: white; }
.filter-box { display: flex; gap: 10px; }
.filter-box select { padding: 6px 10px; border-radius: 4px; border: 1px solid #ddd; min-width: 120px; }

.item-card { padding: 15px; border: 1px solid #eee; border-radius: 6px; margin-bottom: 10px; }
.card-top { display: flex; justify-content: space-between; align-items: center; }
.course-badge { background: #e0e7ff; color: #4f46e5; font-size: 0.8rem; padding: 2px 5px; border-radius: 4px; margin-left: 10px; }
.type-tag { background: #f3f4f6; color: #666; font-size: 0.75rem; padding: 2px 6px; border-radius: 4px; }
.sub { color: #999; font-size: 0.85rem; margin-top: 5px; }

.table { width: 100%; border-collapse: collapse; }
.table th, .table td { padding: 12px; border-bottom: 1px solid #f3f3f3; text-align: left; }
.btn-view { background: #3b82f6; color: white; border: none; padding: 4px 10px; border-radius: 4px; cursor: pointer; }

/* Grading Styles */
.grading-section { background: #f8fafc; padding: 15px; border-radius: 6px; margin-top: 20px; border: 1px solid #e2e8f0; }
.grading-section h4 { margin: 0 0 10px 0; font-size: 1rem; color: #334155; }
.grade-input-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.score-input { width: 80px; padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px; text-align: center; font-weight: bold; }
.btn-confirm-grade { background: #4f46e5; color: white; border: none; padding: 6px 15px; border-radius: 4px; cursor: pointer; }
.hint-text { font-size: 0.8rem; color: #94a3b8; margin: 0 0 15px 0; }
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

/* Create View Styles */
.create-view .form-group { margin-bottom: 15px; }
.create-view label { display: block; font-weight: bold; margin-bottom: 5px; }
.create-view input, .create-view select, .create-view textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
.btn-submit { background: #10b981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; margin-top: 10px; }
.quiz-builder { background: #f8fafc; padding: 15px; border-radius: 8px; border: 1px dashed #cbd5e1; margin-bottom: 20px; max-height: 500px; overflow-y: auto; }
.quiz-item { background: white; padding: 15px; border: 1px solid #e2e8f0; border-radius: 6px; margin-bottom: 15px; }
.quiz-header { display: flex; justify-content: space-between; margin-bottom: 10px; font-weight: bold; color: #475569; border-bottom: 1px solid #eee; padding-bottom: 5px; }
.btn-del { color: #ef4444; background: none; border: none; cursor: pointer; font-size: 0.85rem; font-weight: bold; }
.options-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 10px 0; }
.opt-row { display: flex; align-items: center; gap: 5px; }
.opt-label { font-weight: bold; color: #64748b; width: 20px; }
.btn-add-q { width: 100%; padding: 12px; border: 1px dashed #4f46e5; color: #4f46e5; background: #e0e7ff; cursor: pointer; border-radius: 6px; }
</style>
