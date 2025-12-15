<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useCourseStore } from '@/stores/courseStore'
import { useAuthStore } from '@/stores/authStore'
import apiClient from '@/api'
import { useRouter, useRoute, RouterLink } from 'vue-router'
import BackButton from '@/components/BackButton.vue'
import CommentItem from '@/components/CommentItem.vue'
import VideoNotes from '@/components/VideoNotes.vue'
import CodeSandbox from '@/components/CodeSandbox.vue'
import AITutor from '@/components/AITutor.vue'

const courseStore = useCourseStore()
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const props = defineProps({ id: { type: String, required: true } })

// 状态
const activeTab = ref('info')
const activeAssignmentId = ref(null)
const submissionContent = ref('')
const quizAnswers = ref({})
const submissionFile = ref(null)
const isSubmitting = ref(false)
const isDownloading = ref(false)

const videoPlayer = ref(null)
const currentTime = ref(0)
const comments = ref([])
const newComment = ref('')
const isPostingComment = ref(false)

// 讲师管理状态
const newModuleTitle = ref('')
const openModuleFormId = ref(null)
const currentLessonTitle = ref('')
const currentVideoFiles = ref([])
const uploadStatus = ref('')
const editingLessonId = ref(null)
const editLessonTitle = ref('')
const editLessonVideoFile = ref(null)
const editLessonOrder = ref(0)
const isUpdatingLesson = ref(false)
const showDeleteLessonConfirm = ref(false)
const isDeletingLesson = ref(false)
const lessonToDelete = ref(null)
const lessonErrorMessage = ref('')
const lessonSuccessMessage = ref('')

// 【新增】多选状态
const selectedLessonIds = ref([])
const isBulkDeleting = ref(false)

// 获取课程数据
const course = computed(() => courseStore.courses.find(c => c.id == props.id))
const lessonId = computed(() => route.params.lessonId)
const lesson = computed(() => {
  if (!course.value?.modules || !lessonId.value) return null
  for (const m of course.value.modules) {
    for (const l of (m.lessons || [])) {
      if (l.id == lessonId.value) return l
    }
  }
  return null
})

// 判断权限
const isInstructorOfCourse = computed(() => {
  if (!authStore.isAuthenticated) return false
  if (authStore.user.role === 'admin') return true
  if (authStore.user.role === 'instructor' && course.value) {
    return authStore.user.id === course.value.instructor?.id
  }
  return false
})

let videoCheckInterval = null

onMounted(async () => {
  await courseStore.fetchCourseDetail(props.id)
  if (lessonId.value) fetchComments(lessonId.value)
  startVideoProcessingCheck()
  try { apiClient.post(`/api/courses/${props.id}/record_view/`) } catch (e) {}
})

onUnmounted(() => { if (videoCheckInterval) clearInterval(videoCheckInterval) })

const hasProcessingVideos = () => {
  if (!course.value || !course.value.modules) return false
  for (const module of course.value.modules) {
    if (module.lessons) {
      for (const l of module.lessons) {
        if (l.lesson_type === 'text' && l.video_mp4_file && l.content.includes('处理中')) return true
      }
    }
  }
  return false
}

const startVideoProcessingCheck = () => {
  if (videoCheckInterval) clearInterval(videoCheckInterval)
  videoCheckInterval = setInterval(async () => {
    if (hasProcessingVideos()) {
       await courseStore.fetchCourseDetail(props.id)
    } else {
       clearInterval(videoCheckInterval); videoCheckInterval = null
    }
  }, 10000)
}

watch(course, (newCourse) => {
  if (newCourse) startVideoProcessingCheck()
  if (route.query.manage === 'true') return
  if (!lessonId.value && newCourse && newCourse.modules && newCourse.modules.length > 0) {
    const firstModule = newCourse.modules[0]
    if (firstModule.lessons && firstModule.lessons.length > 0) {
      const firstLesson = firstModule.lessons[0]
      router.replace({ name: 'lesson-watch', params: { courseId: newCourse.id, lessonId: firstLesson.id } })
    }
  }
}, { immediate: true })

const videoUrl = computed(() => {
  const l = lesson.value
  if (!l) return null
  if (l.video_mp4_file) return getFullCoverImagePath(l.video_mp4_file)
  if (l.video_m3u8_url) return getFullCoverImagePath(l.video_m3u8_url)
  return null
})

const handleTimeUpdate = (e) => { currentTime.value = e.target.currentTime }
const handleSeek = (time) => { if (videoPlayer.value) { videoPlayer.value.currentTime = time; videoPlayer.value.play() } }

watch(videoUrl, (newUrl) => { if (newUrl && videoPlayer.value) videoPlayer.value.load() })
watch(lessonId, (newId) => { if (newId) fetchComments(newId) })

// --- 评论功能 ---
const fetchComments = async (id) => {
  if (!id) return;
  try {
    const res = await apiClient.get('/api/comments/', { params: { lesson_id: id } })
    comments.value = Array.isArray(res.data.results || res.data) ? (res.data.results || res.data) : []
  } catch (e) { comments.value = [] }
}

const handlePostComment = async () => {
  if (!newComment.value.trim()) return
  isPostingComment.value = true
  try {
    const res = await apiClient.post('/api/comments/', {
      lesson: Number(lessonId.value), content: newComment.value, parent: null
    })
    comments.value.unshift(res.data)
    newComment.value = ''
  } finally { isPostingComment.value = false }
}

// --- 作业与下载 ---
const handleDownload = async (url) => {
  if (!url || isDownloading.value) return
  isDownloading.value = true
  try {
    const response = await apiClient.get(url, { responseType: 'blob' })
    const blob = new Blob([response.data])
    const link = document.createElement('a')
    link.href = window.URL.createObjectURL(blob)
    const filename = url.split('/').pop() || 'attachment'
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(link.href)
  } catch (error) { window.open(url, '_blank') } finally { isDownloading.value = false }
}

const toggleAssignmentForm = (assignId) => {
  if (activeAssignmentId.value === assignId) {
    activeAssignmentId.value = null; submissionContent.value = ''; submissionFile.value = null; quizAnswers.value = {}
  } else {
    activeAssignmentId.value = assignId; submissionContent.value = ''; submissionFile.value = null; quizAnswers.value = {}
  }
}

const handleSubmissionFileChange = (event) => { submissionFile.value = event.target.files ? event.target.files[0] : null }

const handleSubmitAssignment = async (assign) => {
  let contentToSend = ''
  if (assign.assignment_type === 'choice') {
      if (!assign.quiz_questions || assign.quiz_questions.length === 0) return alert('题目数据错误')
      if (Object.keys(quizAnswers.value).length < assign.quiz_questions.length) return alert('请完成所有选择题后再提交')
      contentToSend = JSON.stringify(quizAnswers.value)
  } else {
      if (!submissionContent.value.trim() && !submissionFile.value) return alert('请填写内容')
      contentToSend = submissionContent.value
  }

  if (!authStore.isAuthenticated) return router.push({ name: 'login' })
  isSubmitting.value = true
  const formData = new FormData()
  formData.append('assignment', assign.id)
  formData.append('content', contentToSend)
  if (submissionFile.value) formData.append('attachment', submissionFile.value)

  try {
    await apiClient.post('/api/submissions/', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    alert(assign.assignment_type === 'choice' ? '提交成功！系统已自动批改。' : '提交成功！')
    activeAssignmentId.value = null
    courseStore.markAsStale()
    await courseStore.fetchCourseDetail(props.id)
  } catch (error) { alert('提交失败: ' + (error.response?.data?.detail || '未知错误')) }
  finally { isSubmitting.value = false }
}

const parseAnswer = (jsonStr) => {
    try {
        const obj = JSON.parse(jsonStr)
        if (typeof obj === 'object') return Object.entries(obj).map(([idx, ans]) => `第${parseInt(idx)+1}题:${ans}`).join(';  ')
        return jsonStr
    } catch { return jsonStr }
}

const getFullCoverImagePath = (path) => {
    if(!path) return ''
    const baseUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
    return path.startsWith('http') ? path : `${baseUrl}${path}`
}

const sortedLessons = (lessons) => { if (!lessons) return []; return [...lessons].sort((a, b) => (a.order || 999) - (b.order || 999)); }

// --- 讲师管理逻辑 ---
const handleFileChange = (event) => {
    if (event.target.files) {
        currentVideoFiles.value = Array.from(event.target.files)
    } else {
        currentVideoFiles.value = []
    }
}

const showLessonForm = (moduleId) => {
    if (editingLessonId.value !== null) return;
    if (openModuleFormId.value === moduleId) { openModuleFormId.value = null; }
    else { openModuleFormId.value = moduleId; currentLessonTitle.value = ''; currentVideoFiles.value = []; uploadStatus.value = ''; }
}

const handleAddModule = async () => {
    if (!newModuleTitle.value.trim()) return;
    try {
        const moduleData = { course: props.id, title: newModuleTitle.value };
        const response = await apiClient.post('/api/modules/', moduleData);
        if (course.value.modules) { course.value.modules.push(response.data); }
        courseStore.markAsStale(); newModuleTitle.value = '';
    } catch (error) { alert('创建失败'); }
}

const handleAddLesson = async (moduleId) => {
    if (!moduleId || currentVideoFiles.value.length === 0) {
        alert('请选择至少一个视频文件'); return;
    }

    const isSingleFile = currentVideoFiles.value.length === 1
    const useUserTitle = isSingleFile && currentLessonTitle.value.trim() !== ''

    const total = currentVideoFiles.value.length
    let successCount = 0
    let failCount = 0

    for (let i = 0; i < total; i++) {
        const file = currentVideoFiles.value[i]
        const title = useUserTitle ? currentLessonTitle.value : file.name.replace(/\.[^/.]+$/, "")

        uploadStatus.value = `正在上传 (${i + 1}/${total}): ${title}...`

        const formData = new FormData();
        formData.append('title', title);
        formData.append('module', moduleId);
        formData.append('video_mp4_file', file);

        try {
            const response = await apiClient.post('/api/lessons/', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
            const targetModule = course.value.modules.find(m => m.id == moduleId);
            if (targetModule) { targetModule.lessons = targetModule.lessons || []; targetModule.lessons.push(response.data); }
            successCount++
        } catch (error) {
            console.error(`File ${file.name} failed`, error)
            failCount++
        }
    }

    courseStore.markAsStale();
    await courseStore.fetchCourseDetail(props.id);
    startVideoProcessingCheck();

    if (failCount === 0) {
        uploadStatus.value = '全部上传成功！'
        setTimeout(() => { showLessonForm(moduleId); }, 1500);
    } else {
        uploadStatus.value = `完成: 成功 ${successCount} 个, 失败 ${failCount} 个`;
    }
}

const startEditLesson = (lesson) => {
    if (openModuleFormId.value !== null) openModuleFormId.value = null;
    editingLessonId.value = lesson.id; editLessonTitle.value = lesson.title; editLessonOrder.value = lesson.order || 0; editLessonVideoFile.value = null; lessonErrorMessage.value = ''; lessonSuccessMessage.value = '';
}
const cancelEditLesson = () => {
    editingLessonId.value = null; editLessonTitle.value = ''; editLessonOrder.value = 0; editLessonVideoFile.value = null; lessonErrorMessage.value = ''; lessonSuccessMessage.value = '';
}
const handleEditLessonFileChange = (event) => { editLessonVideoFile.value = event.target.files ? event.target.files[0] : null }
const handleUpdateLesson = async (lessonId, moduleId) => {
    if (!editLessonTitle.value.trim()) return;
    isUpdatingLesson.value = true;
    const formData = new FormData();
    formData.append('title', editLessonTitle.value.trim());
    formData.append('order', editLessonOrder.value);
    if (editLessonVideoFile.value) formData.append('video_mp4_file', editLessonVideoFile.value);
    try {
        const response = await apiClient.patch(`/api/lessons/${lessonId}/`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
        const targetModule = course.value.modules.find(m => m.id == moduleId);
        if (targetModule && targetModule.lessons) {
            const lessonIndex = targetModule.lessons.findIndex(l => l.id == lessonId);
            if (lessonIndex !== -1) targetModule.lessons[lessonIndex] = response.data;
        }
        courseStore.markAsStale(); lessonSuccessMessage.value = '更新成功'; setTimeout(cancelEditLesson, 1500);
    } catch (error) { lessonErrorMessage.value = '更新失败'; }
    finally { isUpdatingLesson.value = false; }
}

const startDeleteLesson = (lesson) => { lessonToDelete.value = lesson; showDeleteLessonConfirm.value = true; }
const cancelDeleteLesson = () => { showDeleteLessonConfirm.value = false; lessonToDelete.value = null; }
const handleDeleteLesson = async () => {
    if (!lessonToDelete.value) return;
    isDeletingLesson.value = true;
    try {
        await apiClient.delete(`/api/lessons/${lessonToDelete.value.id}/`);
        const targetModule = course.value.modules.find(m => m.lessons && m.lessons.some(l => l.id === lessonToDelete.value.id));
        if (targetModule) targetModule.lessons = targetModule.lessons.filter(l => l.id !== lessonToDelete.value.id);

        // 同时从 selectedLessonIds 中移除
        selectedLessonIds.value = selectedLessonIds.value.filter(id => id !== lessonToDelete.value.id);

        courseStore.markAsStale(); lessonSuccessMessage.value = '删除成功'; cancelDeleteLesson(); setTimeout(() => { lessonSuccessMessage.value = '' }, 2000);
    } catch (error) { lessonErrorMessage.value = '删除失败'; cancelDeleteLesson(); }
    finally { isDeletingLesson.value = false; }
}

// 【新增】批量删除函数
const handleBulkDelete = async () => {
    if (selectedLessonIds.value.length === 0) return
    if (!confirm(`确定要删除选中的 ${selectedLessonIds.value.length} 个课时吗？`)) return

    isBulkDeleting.value = true
    try {
        await apiClient.post('/api/lessons/bulk_delete/', { ids: selectedLessonIds.value })
        courseStore.markAsStale()
        await courseStore.fetchCourseDetail(props.id)
        selectedLessonIds.value = [] // 清空选择
        alert('批量删除成功')
    } catch (e) {
        alert('批量删除失败: ' + (e.response?.data?.detail || '未知错误'))
    } finally {
        isBulkDeleting.value = false
    }
}
</script>

<template>
  <div class="course-detail">
    <div class="course-header-actions">
      <BackButton :fallback-route="{ name: 'courses' }" text="返回列表" small inline />
    </div>

    <div v-if="!course"><p>加载中...</p></div>
    <div v-else>
      <h1>{{ course.title }}</h1>
      <p>{{ course.description }}</p>
      <hr>

      <div v-if="course.assignments && course.assignments.length > 0" class="assignments-section">
        <h2>📝 课程作业</h2>
        <div class="assignment-list">
          <div v-for="assign in course.assignments" :key="assign.id" class="assignment-card">
            <div class="assign-header">
              <div class="title-row">
                  <h3>{{ assign.title }}</h3>
                  <span class="type-tag">{{ assign.assignment_type === 'choice' ? '选择题' : '图文/文件' }}</span>
              </div>
              <span v-if="assign.my_submission" :class="`status-badge ${assign.my_submission.status}`">
                {{ assign.my_submission.status === 'passed' ? '✅ 已通过' : (assign.my_submission.status === 'rejected' ? '❌ 需修改' : '⏳ 已提交') }}
              </span>
              <span v-else class="assign-date">未提交</span>
            </div>
            <p class="assign-desc">{{ assign.description }}</p>
            <div v-if="assign.attachment" class="attachment-link">
                <a href="#" @click.prevent="handleDownload(assign.attachment)" class="download-btn">📥 下载附件</a>
            </div>
            <div v-if="assign.my_submission" class="submission-result">
              <div class="result-box">
                <p v-if="assign.assignment_type === 'choice'"><strong>我的答案：</strong> {{ parseAnswer(assign.my_submission.content) }}</p>
                <p v-else><strong>我的提交：</strong> {{ assign.my_submission.content }}</p>
                <p v-if="assign.my_submission.grade !== null"><strong>评分：</strong> {{ assign.my_submission.grade }} 分</p>
                <p v-if="assign.my_submission.feedback"><strong>反馈：</strong> {{ assign.my_submission.feedback }}</p>
              </div>
              <button v-if="assign.my_submission.status === 'rejected'" @click="toggleAssignmentForm(assign.id)" class="btn-retry">重做</button>
            </div>
            <div v-else>
              <button @click="toggleAssignmentForm(assign.id)" class="btn-submit-toggle">{{ activeAssignmentId === assign.id ? '取消' : '开始作答' }}</button>
            </div>
            <div v-if="activeAssignmentId === assign.id" class="submission-form">
              <div v-if="assign.assignment_type === 'choice'" class="choice-container">
                  <div v-if="assign.quiz_questions && assign.quiz_questions.length > 0">
                    <div v-for="(question, index) in assign.quiz_questions" :key="index" class="question-block">
                        <p class="q-title">{{ index + 1 }}. {{ question.question }}</p>
                        <div class="radio-group">
                            <label v-for="(val, key) in question.options" :key="key" class="radio-item">
                                <input type="radio" :name="`q-${assign.id}-${index}`" :value="key" v-model="quizAnswers[index]" />
                                <span class="opt-text">{{ key }}. {{ val }}</span>
                            </label>
                        </div>
                    </div>
                  </div>
              </div>
              <div v-else>
                  <textarea v-model="submissionContent" placeholder="在此输入作业内容..." rows="4"></textarea>
                  <div class="form-group file-upload">
                    <label>上传附件 (可选):</label>
                    <input type="file" @change="handleSubmissionFileChange" />
                  </div>
              </div>
              <button @click="handleSubmitAssignment(assign)" class="btn-confirm-submit" :disabled="isSubmitting">{{ isSubmitting ? '提交中...' : '确认提交' }}</button>
            </div>
          </div>
        </div>
      </div>

      <div class="content-header-row">
          <h2>课程内容:</h2>
          <button v-if="isInstructorOfCourse && selectedLessonIds.length > 0"
                  @click="handleBulkDelete"
                  class="btn-bulk-delete"
                  :disabled="isBulkDeleting">
            🗑️ 删除选中 ({{ selectedLessonIds.length }})
          </button>
      </div>

      <div v-if="isInstructorOfCourse" class="admin-add-module">
        <input v-model="newModuleTitle" placeholder="输入新章节标题" class="module-input" />
        <button @click="handleAddModule" class="btn-add-module">+ 添加章节</button>
      </div>

      <div class="content-management">
        <div v-for="module in course.modules" :key="module.id" class="module-container">
          <div class="module-header">
            <h3>{{ module.title }}</h3>
            <button v-if="isInstructorOfCourse" @click="showLessonForm(module.id)" class="btn-sm btn-add-lesson">
                {{ openModuleFormId === module.id ? '取消' : '+ 添加课时' }}
            </button>
          </div>

          <div v-if="openModuleFormId === module.id" class="lesson-form-panel fade-in">
            <h4>在 "{{ module.title }}" 下添加新课时</h4>
            <div class="form-group">
                <label>视频文件 (支持多选):</label>
                <input type="file" accept="video/mp4" @change="handleFileChange" class="form-file" multiple />
            </div>

            <div v-if="currentVideoFiles.length <= 1" class="form-group">
                <input v-model="currentLessonTitle" placeholder="课时标题 (留空则使用文件名)" class="form-input" />
            </div>

            <div v-if="currentVideoFiles.length > 1" class="batch-info">
                <p>已选择 {{ currentVideoFiles.length }} 个文件，将批量上传。</p>
            </div>

            <div class="form-actions">
                <button @click="handleAddLesson(module.id)" class="btn-save">
                    {{ currentVideoFiles.length > 1 ? '批量上传' : '上传并保存' }}
                </button>
                <span class="status">{{ uploadStatus }}</span>
            </div>
          </div>

          <ul>
            <li v-for="(lessonItem, idx) in sortedLessons(module.lessons)" :key="lessonItem.id" class="lesson-item">
               <div class="lesson-display">
                  <div class="lesson-left">
                      <input v-if="isInstructorOfCourse" type="checkbox" :value="lessonItem.id" v-model="selectedLessonIds" class="lesson-checkbox" />
                      <RouterLink :to="{ name: 'lesson-watch', params: { courseId: course.id, lessonId: lessonItem.id } }" class="lesson-link">
                        <span>{{ idx + 1 }}. {{ lessonItem.title }}</span>
                      </RouterLink>
                  </div>
                  <div v-if="isInstructorOfCourse" class="lesson-actions">
                      <button @click="startEditLesson(lessonItem)" class="btn-icon">✏️</button>
                      <button @click="startDeleteLesson(lessonItem)" class="btn-icon delete">🗑️</button>
                  </div>
               </div>

               <div v-if="editingLessonId === lessonItem.id" class="lesson-edit-form fade-in">
                   <div class="form-row">
                       <input v-model="editLessonTitle" placeholder="标题" class="form-input" />
                       <input v-model="editLessonOrder" type="number" placeholder="顺序" class="form-input small" />
                   </div>
                   <input type="file" accept="video/mp4" @change="handleEditLessonFileChange" class="form-file" />
                   <div class="form-actions">
                       <button @click="handleUpdateLesson(lessonItem.id, module.id)" :disabled="isUpdatingLesson" class="btn-save">
                           {{ isUpdatingLesson ? '更新中...' : '保存修改' }}
                       </button>
                       <button @click="cancelEditLesson" class="btn-cancel">取消</button>
                   </div>
                   <p v-if="lessonErrorMessage" class="error-msg">{{ lessonErrorMessage }}</p>
                   <p v-if="lessonSuccessMessage" class="success-msg">{{ lessonSuccessMessage }}</p>
               </div>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <div v-if="showDeleteLessonConfirm" class="modal-overlay">
        <div class="modal">
            <h3>确认删除</h3>
            <p>确定要删除课时 "{{ lessonToDelete?.title }}" 吗？</p>
            <div class="modal-actions">
                <button @click="handleDeleteLesson" :disabled="isDeletingLesson" class="btn-danger">
                    {{ isDeletingLesson ? '删除中...' : '确认删除' }}
                </button>
                <button @click="cancelDeleteLesson" class="btn-cancel">取消</button>
            </div>
        </div>
    </div>
  </div>
</template>

<style scoped>
.course-detail { max-width: 900px; margin: 0 auto; padding: 20px; }
.assignments-section { margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px; }
.assignment-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin-bottom: 15px; }
.assign-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.title-row { display: flex; align-items: center; gap: 10px; }
.assign-header h3 { margin: 0; font-size: 1.1rem; }
.type-tag { background: #e0e7ff; color: #4f46e5; font-size: 0.75rem; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
.status-badge { font-size: 0.85rem; padding: 4px 8px; border-radius: 4px; font-weight: 500; }
.status-badge.pending { background: #f3f4f6; color: #6b7280; }
.status-badge.passed { background: #d1fae5; color: #059669; }
.status-badge.rejected { background: #fee2e2; color: #dc2626; }
.btn-submit-toggle { background: #4f46e5; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; }
.submission-form { margin-top: 15px; padding: 15px; background: #f9fafb; border-radius: 6px; }
.submission-form textarea { width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 6px; margin-bottom: 10px; }
.btn-confirm-submit { background: #10b981; color: white; border: none; padding: 8px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; margin-top: 10px; }
.choice-container { display: flex; flex-direction: column; gap: 20px; }
.question-block { background: white; padding: 15px; border-radius: 6px; border: 1px solid #e5e7eb; }
.q-title { font-weight: bold; margin-bottom: 10px; color: #1f2937; }
.radio-group { display: flex; flex-direction: column; gap: 8px; }
.radio-item { display: flex; align-items: center; gap: 10px; cursor: pointer; padding: 5px; border-radius: 4px; transition: background 0.2s; }
.radio-item:hover { background: #f3f4f6; }
.opt-text { color: #4b5563; }
.empty-quiz-msg { color: #ef4444; font-weight: bold; padding: 10px; }
.result-box { background: #f0fdf4; border: 1px solid #bbf7d0; padding: 15px; border-radius: 6px; font-size: 0.95rem; color: #166534; }
.btn-retry { background: #f59e0b; color: white; border: none; padding: 6px 12px; border-radius: 4px; margin-top: 10px; cursor: pointer; }
.download-btn { color: #4f46e5; font-size: 0.9rem; cursor: pointer; text-decoration: none; }

/* 讲师管理样式 */
.content-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.admin-add-module { margin: 20px 0; display: flex; gap: 10px; }
.module-input { padding: 10px; border: 1px solid #ddd; border-radius: 6px; flex: 1; }
.btn-add-module { padding: 10px 20px; background: #10b981; color: white; border: none; border-radius: 6px; cursor: pointer; }
.module-container { border: 1px solid #eee; margin-bottom: 15px; border-radius: 8px; overflow: hidden; }
.module-header { background: #f9fafb; padding: 10px 15px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
.btn-add-lesson { background: #4f46e5; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 0.8rem; }
.lesson-form-panel { padding: 15px; background: #f0f4ff; border-bottom: 1px solid #e0e7ff; }
.form-input { width: 100%; padding: 8px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px; }
.form-file { margin-bottom: 10px; }
.form-actions { display: flex; gap: 10px; align-items: center; }
.btn-save { background: #10b981; color: white; padding: 6px 15px; border: none; border-radius: 4px; cursor: pointer; }
.lesson-item { padding: 10px 15px; border-bottom: 1px solid #f1f1f1; }
.lesson-display { display: flex; justify-content: space-between; align-items: center; }
.lesson-left { display: flex; align-items: center; gap: 10px; flex: 1; }
.lesson-checkbox { transform: scale(1.2); cursor: pointer; }
.lesson-link { text-decoration: none; color: #333; }
.lesson-actions { display: flex; gap: 5px; }
.btn-icon { background: none; border: none; cursor: pointer; font-size: 1rem; }
.lesson-edit-form { margin-top: 10px; padding: 10px; background: #fffbe6; border: 1px solid #ffe58f; border-radius: 4px; }
.btn-cancel { background: #999; color: white; padding: 6px 15px; border: none; border-radius: 4px; cursor: pointer; }
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 2000; }
.modal { background: white; padding: 25px; border-radius: 8px; width: 300px; text-align: center; }
.modal-actions { margin-top: 20px; display: flex; justify-content: center; gap: 15px; }
.btn-danger { background: #ef4444; color: white; padding: 8px 20px; border: none; border-radius: 4px; cursor: pointer; }
.btn-bulk-delete { background: #dc2626; color: white; padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; }
.btn-bulk-delete:hover { background: #b91c1c; }
.fade-in { animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.batch-info { background: #e0f2fe; color: #0369a1; padding: 8px; border-radius: 4px; margin-bottom: 10px; font-size: 0.9rem; }
</style>
