<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '@/api'
import { useCourseStore } from '@/stores/courseStore'

const courseStore = useCourseStore()
const assignments = ref([])
const submissions = ref([])
const activeTab = ref('list') // list, create, review
const selectedAssignment = ref(null)

// 表单数据
const newAssign = ref({ course: '', title: '', description: '' })

const fetchAssignments = async () => {
  const res = await apiClient.get('/api/assignments/')
  assignments.value = res.data.results || res.data
}

const fetchSubmissions = async () => {
  const res = await apiClient.get('/api/submissions/')
  submissions.value = res.data.results || res.data
}

const handleCreate = async () => {
  if (!newAssign.value.course) return alert('请选择课程')
  try {
    await apiClient.post('/api/assignments/', newAssign.value)
    alert('发布成功')
    activeTab.value = 'list'
    fetchAssignments()
  } catch (e) { alert('发布失败') }
}

const handleGrade = async (sub, status, grade) => {
  try {
    await apiClient.patch(`/api/submissions/${sub.id}/`, { status, grade })
    alert('批改完成')
    fetchSubmissions()
  } catch (e) { alert('操作失败') }
}

onMounted(async () => {
  courseStore.fetchInstructorCourses()
  fetchAssignments()
  fetchSubmissions()
})
</script>

<template>
  <div class="assign-panel">
    <div class="toolbar">
      <button :class="{active: activeTab === 'list'}" @click="activeTab = 'list'">作业列表</button>
      <button :class="{active: activeTab === 'create'}" @click="activeTab = 'create'">+ 发布新作业</button>
      <button :class="{active: activeTab === 'review'}" @click="activeTab = 'review'">批改作业 ({{ submissions.length }})</button>
    </div>

    <div v-if="activeTab === 'list'" class="list-view">
      <div v-for="a in assignments" :key="a.id" class="item-card">
        <h4>{{ a.title }}</h4>
        <p class="sub">所属课程 ID: {{ a.course }} | 已提交: {{ a.submission_count }}</p>
      </div>
    </div>

    <div v-if="activeTab === 'create'" class="create-view">
      <div class="form-group">
        <label>选择课程</label>
        <select v-model="newAssign.course">
          <option v-for="c in courseStore.courses" :key="c.id" :value="c.id">{{ c.title }}</option>
        </select>
      </div>
      <div class="form-group">
        <label>标题</label>
        <input v-model="newAssign.title" type="text" />
      </div>
      <div class="form-group">
        <label>描述</label>
        <textarea v-model="newAssign.description" rows="4"></textarea>
      </div>
      <button class="btn-submit" @click="handleCreate">立即发布</button>
    </div>

    <div v-if="activeTab === 'review'" class="review-view">
      <table class="table">
        <thead><tr><th>学生</th><th>作业</th><th>内容</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="s in submissions" :key="s.id">
            <td>{{ s.student.username }}</td>
            <td>{{ s.assignment_title }}</td>
            <td><a href="#" @click.prevent="alert(s.content)">查看内容</a></td>
            <td>
              <span :class="s.status">{{ s.status }}</span>
            </td>
            <td>
              <button @click="handleGrade(s, 'passed', 100)" class="btn-pass">通过</button>
              <button @click="handleGrade(s, 'rejected', 0)" class="btn-reject">打回</button>
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
.toolbar button { padding: 8px 16px; background: #f3f4f6; border: none; border-radius: 20px; cursor: pointer; }
.toolbar button.active { background: #4f46e5; color: white; }

.item-card { padding: 15px; border: 1px solid #eee; border-radius: 6px; margin-bottom: 10px; }
.item-card h4 { margin: 0 0 5px 0; }
.sub { color: #666; font-size: 0.9rem; margin: 0; }

.form-group { margin-bottom: 15px; }
.form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
.form-group input, .form-group textarea, .form-group select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
.btn-submit { background: #10b981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }

.table { width: 100%; border-collapse: collapse; }
.table th, .table td { padding: 10px; border-bottom: 1px solid #eee; text-align: left; }
.btn-pass { color: #10b981; background: none; border: 1px solid #10b981; padding: 2px 8px; border-radius: 4px; cursor: pointer; margin-right: 5px; }
.btn-reject { color: #ef4444; background: none; border: 1px solid #ef4444; padding: 2px 8px; border-radius: 4px; cursor: pointer; }
.pending { color: orange; } .passed { color: green; } .rejected { color: red; }
</style>
