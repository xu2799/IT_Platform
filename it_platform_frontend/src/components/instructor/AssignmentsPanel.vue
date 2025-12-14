<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '@/api'
import { useCourseStore } from '@/stores/courseStore'

const courseStore = useCourseStore()
const assignments = ref([])
const submissions = ref([])
const activeTab = ref('list')

// 表单数据
const newAssign = ref({
    course: '',
    title: '',
    description: '请完成以下选择题',
    assignment_type: 'regular'
})

// 多题列表 (默认先给一道空题)
const quizList = ref([
    { question: '', options: { A: '', B: '', C: '', D: '' }, answer: 'A' }
])

const assignmentFile = ref(null)

const fetchAssignments = async () => {
  try {
    const res = await apiClient.get('/api/assignments/')
    assignments.value = res.data.results || res.data
  } catch (e) { console.error(e) }
}

const fetchSubmissions = async () => {
  try {
    const res = await apiClient.get('/api/submissions/')
    submissions.value = res.data.results || res.data
  } catch (e) { console.error(e) }
}

const handleFileChange = (event) => {
  assignmentFile.value = event.target.files ? event.target.files[0] : null
}

// 【修复】添加题目功能
const addQuestion = () => {
    quizList.value.push({
        question: '',
        options: { A: '', B: '', C: '', D: '' },
        answer: 'A'
    })
    // 自动滚动到底部
    setTimeout(() => {
        const container = document.querySelector('.quiz-builder');
        if(container) container.scrollTop = container.scrollHeight;
    }, 100)
}

const removeQuestion = (index) => {
    if (quizList.value.length > 1) {
        quizList.value.splice(index, 1)
    } else {
        alert('至少需要保留一道题目')
    }
}

const handleCreate = async () => {
  if (!newAssign.value.course) return alert('请选择课程')
  if (!newAssign.value.title) return alert('请填写标题')

  const formData = new FormData()
  formData.append('course', newAssign.value.course)
  formData.append('title', newAssign.value.title)
  formData.append('description', newAssign.value.description)
  formData.append('assignment_type', newAssign.value.assignment_type)

  // 【修复】处理选择题数据打包
  if (newAssign.value.assignment_type === 'choice') {
      // 简单验证
      for (let i = 0; i < quizList.value.length; i++) {
          const q = quizList.value[i]
          if (!q.question.trim()) {
              return alert(`第 ${i+1} 题的题目不能为空`)
          }
          if (!q.options.A.trim() || !q.options.B.trim()) {
              return alert(`第 ${i+1} 题至少需要填写选项 A 和 B`)
          }
      }
      // 将数组转换为 JSON 字符串发送
      formData.append('quiz_data', JSON.stringify(quizList.value))
  }

  if (assignmentFile.value) {
      formData.append('attachment', assignmentFile.value)
  }

  try {
    await apiClient.post('/api/assignments/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    })
    alert('发布成功')

    // 重置表单
    newAssign.value = { course: '', title: '', description: '请完成以下选择题', assignment_type: 'regular' }
    quizList.value = [{ question: '', options: { A: '', B: '', C: '', D: '' }, answer: 'A' }]
    assignmentFile.value = null
    activeTab.value = 'list'
    fetchAssignments()
  } catch (e) {
    alert('发布失败: ' + (e.response?.data?.detail || '未知错误'))
  }
}

const handleGrade = async (sub, status, grade) => {
  try {
    await apiClient.patch(`/api/submissions/${sub.id}/`, { status, grade })
    alert('批改完成')
    fetchSubmissions()
  } catch (e) { alert('操作失败') }
}

onMounted(async () => {
  await courseStore.fetchInstructorCourses()
  await fetchAssignments()
  await fetchSubmissions()
})
</script>

<template>
  <div class="assign-panel">
    <div class="toolbar">
      <button :class="{active: activeTab === 'list'}" @click="activeTab = 'list'">作业列表</button>
      <button :class="{active: activeTab === 'create'}" @click="activeTab = 'create'">+ 发布新作业</button>
      <button :class="{active: activeTab === 'review'}" @click="activeTab = 'review'">批改作业</button>
    </div>

    <div v-if="activeTab === 'list'" class="list-view">
      <div v-for="a in assignments" :key="a.id" class="item-card">
        <div class="card-top">
            <h4>{{ a.title }}</h4>
            <span class="type-tag">{{ a.assignment_type === 'choice' ? '选择题' : '图文/文件' }}</span>
        </div>
        <p class="sub">ID: {{ a.id }} | 提交数: {{ a.submission_count }}</p>
      </div>
      <div v-if="assignments.length === 0" class="empty">暂无作业</div>
    </div>

    <div v-if="activeTab === 'create'" class="create-view">
      <div class="form-group">
        <label>选择课程</label>
        <select v-model="newAssign.course">
          <option disabled value="">请选择课程</option>
          <option v-for="c in courseStore.instructorCourses" :key="c.id" :value="c.id">{{ c.title }}</option>
        </select>
      </div>

      <div class="form-group">
        <label>作业类型</label>
        <select v-model="newAssign.assignment_type">
          <option value="regular">图文/文件作业</option>
          <option value="choice">选择题 (支持多题)</option>
        </select>
      </div>

      <div class="form-group">
        <label>标题</label>
        <input v-model="newAssign.title" type="text" />
      </div>

      <div class="form-group" v-if="newAssign.assignment_type === 'regular'">
        <label>作业描述</label>
        <textarea v-model="newAssign.description" rows="3"></textarea>
      </div>

      <div v-if="newAssign.assignment_type === 'choice'" class="quiz-builder">
          <h4>题目列表</h4>
          <div v-for="(item, index) in quizList" :key="index" class="quiz-item">
              <div class="quiz-header">
                  <span>第 {{ index + 1 }} 题</span>
                  <button class="btn-del" @click="removeQuestion(index)">删除此题</button>
              </div>

              <div class="form-group">
                  <input v-model="item.question" placeholder="输入题目内容..." class="q-input" />
              </div>

              <div class="options-grid">
                  <div class="opt-row" v-for="opt in ['A', 'B', 'C', 'D']" :key="opt">
                      <span class="opt-label">{{ opt }}</span>
                      <input v-model="item.options[opt]" :placeholder="`选项 ${opt}`" />
                  </div>
              </div>

              <div class="form-group correct-ans">
                  <label>正确答案：</label>
                  <select v-model="item.answer">
                      <option value="A">A</option>
                      <option value="B">B</option>
                      <option value="C">C</option>
                      <option value="D">D</option>
                  </select>
              </div>
          </div>

          <button class="btn-add-q" @click="addQuestion">+ 添加下一道题</button>
      </div>

      <div class="form-group" v-if="newAssign.assignment_type === 'regular'">
        <label>附件 (可选)</label>
        <input type="file" @change="handleFileChange" />
      </div>

      <button class="btn-submit" @click="handleCreate">立即发布</button>
    </div>

    <div v-if="activeTab === 'review'" class="review-view">
      <table class="table">
        <thead><tr><th>类型</th><th>学生</th><th>作业</th><th>得分/状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="s in submissions" :key="s.id">
            <td>{{ s.assignment_type === 'choice' ? '选择题' : '文件' }}</td>
            <td>{{ s.student?.nickname || s.student?.username }}</td>
            <td>{{ s.assignment_title }}</td>
            <td>
                <span :class="s.status">{{ s.status }}</span>
                <span v-if="s.grade !== null"> ({{ s.grade }}分)</span>
            </td>
            <td>
              <div v-if="s.status !== 'passed'" class="btn-group">
                <button @click="handleGrade(s, 'passed', 100)" class="btn-pass">通过</button>
                <button @click="handleGrade(s, 'rejected', 0)" class="btn-reject">打回</button>
              </div>
              <span v-else class="done-text">已批改</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.assign-panel { background: white; padding: 20px; border-radius: 8px; border: 1px solid #eee; }
.toolbar { display: flex; gap: 10px; border-bottom: 1px solid #eee; padding-bottom: 15px; margin-bottom: 20px; }
.toolbar button { padding: 8px 16px; background: #f3f4f6; border: none; border-radius: 20px; cursor: pointer; transition: all 0.2s; }
.toolbar button:hover { background: #e5e7eb; }
.toolbar button.active { background: #4f46e5; color: white; }

.item-card { padding: 15px; border: 1px solid #eee; border-radius: 6px; margin-bottom: 10px; }
.card-top { display: flex; justify-content: space-between; align-items: center; }
.type-tag { background: #e0e7ff; color: #4f46e5; font-size: 0.75rem; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
.item-card h4 { margin: 0; color: #333; }
.sub { color: #666; font-size: 0.9rem; margin: 0; }

.form-group { margin-bottom: 15px; }
.form-group label { display: block; margin-bottom: 5px; font-weight: bold; font-size: 0.9rem; }
.form-group input[type="text"], .form-group textarea, .form-group select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-family: inherit; }

/* 题目编辑器样式 */
.quiz-builder { background: #f8fafc; padding: 15px; border-radius: 8px; border: 1px dashed #cbd5e1; margin-bottom: 20px; max-height: 500px; overflow-y: auto; }
.quiz-item { background: white; padding: 15px; border: 1px solid #e2e8f0; border-radius: 6px; margin-bottom: 15px; }
.quiz-header { display: flex; justify-content: space-between; margin-bottom: 10px; font-weight: bold; color: #475569; border-bottom: 1px solid #eee; padding-bottom: 5px; }
.btn-del { color: #ef4444; background: none; border: none; cursor: pointer; font-size: 0.85rem; font-weight: bold; }
.q-input { font-weight: bold; }
.options-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 10px 0; }
.opt-row { display: flex; align-items: center; gap: 5px; }
.opt-label { font-weight: bold; color: #64748b; width: 20px; }
.btn-add-q { width: 100%; padding: 12px; border: 1px dashed #4f46e5; color: #4f46e5; background: #e0e7ff; cursor: pointer; border-radius: 6px; font-weight: bold; font-size: 1rem; margin-top: 10px; }
.btn-add-q:hover { background: #c7d2fe; }

.btn-submit { background: #10b981; color: white; padding: 10px 24px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
.btn-submit:hover { background: #059669; }

.table { width: 100%; border-collapse: collapse; margin-top: 10px; }
.table th, .table td { padding: 12px; border-bottom: 1px solid #eee; text-align: left; font-size: 0.9rem; }
.table th { background: #f9fafb; font-weight: 600; }

.btn-group { display: flex; gap: 5px; }
.btn-pass { color: #10b981; background: #ecfdf5; border: 1px solid #10b981; padding: 2px 8px; border-radius: 4px; cursor: pointer; }
.btn-reject { color: #ef4444; background: #fef2f2; border: 1px solid #ef4444; padding: 2px 8px; border-radius: 4px; cursor: pointer; }
.done-text { color: #999; font-size: 0.85rem; }

.pending { color: #f59e0b; }
.passed { color: #10b981; }
.rejected { color: #ef4444; }
.empty { text-align: center; color: #999; padding: 20px; }
</style>
