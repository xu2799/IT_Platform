<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useCourseStore } from '@/stores/courseStore'
import { useAuthStore } from '@/stores/authStore'
import { getFullCoverImagePath } from '@/utils/common'
import BackButton from '@/components/BackButton.vue'
import CommentItem from '@/components/CommentItem.vue'
import apiClient from '@/api'

import VideoNotes from '@/components/VideoNotes.vue'
import CodeSandbox from '@/components/CodeSandbox.vue'
import AITutor from '@/components/AITutor.vue'

const router = useRouter()
const route = useRoute()
const courseStore = useCourseStore()
const authStore = useAuthStore()

const props = defineProps({
  courseId: { type: String, required: true },
  lessonId: { type: String, required: true }
})

const activeTab = ref('info')
const videoPlayer = ref(null)
const currentTime = ref(0)
const comments = ref([])
const newComment = ref('')
const isPostingComment = ref(false)

// 作业状态
const activeAssignmentId = ref(null)
const submissionContent = ref('')
const submissionFile = ref(null)
const quizAnswers = ref({}) // 新增
const isSubmitting = ref(false)
const isDownloading = ref(false)

onMounted(async () => {
  try { await courseStore.fetchCourseDetail(props.courseId) } catch (e) {}
  fetchComments(props.lessonId)
})

const course = computed(() => courseStore.courses.find(c => c.id == props.courseId) || null)
const lesson = computed(() => {
  if (!course.value?.modules) return null
  for (const m of course.value.modules) {
    for (const l of (m.lessons || [])) {
      if (l.id == props.lessonId) return l
    }
  }
  return null
})
const safeModules = computed(() => (course.value?.modules || []).filter(m => m && typeof m === 'object'))
const getSafeLessons = (m) => (m?.lessons || []).filter(l => l && typeof l === 'object')

const videoUrl = computed(() => {
  const l = lesson.value
  if (!l) return null
  if (l.video_mp4_file) return getFullCoverImagePath(l.video_mp4_file)
  if (l.video_m3u8_url) return getFullCoverImagePath(l.video_m3u8_url)
  return null
})

const handleTimeUpdate = (e) => { currentTime.value = e.target.currentTime }
const handleSeek = (time) => {
  if (videoPlayer.value) {
    videoPlayer.value.currentTime = time
    videoPlayer.value.play()
  }
}

watch(videoUrl, (newUrl) => { if (newUrl && videoPlayer.value) videoPlayer.value.load() })
watch(() => props.lessonId, (newId) => { if (newId) fetchComments(newId) })

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
      lesson: Number(props.lessonId), content: newComment.value, parent: null
    })
    comments.value.unshift(res.data)
    newComment.value = ''
  } finally { isPostingComment.value = false }
}

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
    activeAssignmentId.value = null
    submissionContent.value = ''
    submissionFile.value = null
    quizAnswers.value = {}
  } else {
    activeAssignmentId.value = assignId
    submissionContent.value = ''
    submissionFile.value = null
    quizAnswers.value = {}
  }
}

const handleSubmissionFileChange = (event) => { submissionFile.value = event.target.files ? event.target.files[0] : null }

const handleSubmitAssignment = async (assign) => {
  let contentToSend = ''

  if (assign.assignment_type === 'choice') {
      if (!assign.quiz_questions || assign.quiz_questions.length === 0) return alert('题目数据错误')
      if (Object.keys(quizAnswers.value).length < assign.quiz_questions.length) {
          return alert('请完成所有选择题后再提交')
      }
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
    submissionContent.value = ''
    submissionFile.value = null
    quizAnswers.value = {}
    courseStore.markAsStale()
    await courseStore.fetchCourseDetail(props.courseId)
  } catch (error) {
    alert('提交失败: ' + (error.response?.data?.detail || '未知错误'))
  } finally {
    isSubmitting.value = false
  }
}

const parseAnswer = (jsonStr) => {
    try {
        const obj = JSON.parse(jsonStr)
        if (typeof obj === 'object') {
            return Object.entries(obj).map(([idx, ans]) => `第${parseInt(idx)+1}题:${ans}`).join(';  ')
        }
        return jsonStr
    } catch { return jsonStr }
}
</script>

<template>
  <div class="watch-container">
    <div class="content-wrapper">
      <div class="main-column">
        <div class="nav-header">
          <BackButton :fallback-route="{ name: 'course-detail', params: { id: props.courseId } }" text="返回详情" small inline />
          <span class="separator">/</span>
          <span class="current-title">{{ lesson?.title || '加载中...' }}</span>
        </div>

        <div class="video-stage">
          <div v-if="videoUrl" class="video-wrapper">
            <video ref="videoPlayer" :src="videoUrl" controls autoplay playsinline class="html5-player" @timeupdate="handleTimeUpdate"></video>
          </div>
          <div v-else class="placeholder-screen">
            <div class="spinner"></div>
            <p>暂无视频资源或正在加载...</p>
          </div>
        </div>

        <div class="tabs-container">
          <div class="tabs-header">
            <button :class="{ active: activeTab === 'info' }" @click="activeTab = 'info'">课程详情</button>
            <button :class="{ active: activeTab === 'assignments' }" @click="activeTab = 'assignments'">
              📝 作业 ({{ course?.assignments?.length || 0 }})
            </button>
            <button :class="{ active: activeTab === 'comments' }" @click="activeTab = 'comments'">讨论区 ({{ comments.length }})</button>
            <button :class="{ active: activeTab === 'notes' }" @click="activeTab = 'notes'">我的笔记</button>
            <button :class="{ active: activeTab === 'code' }" @click="activeTab = 'code'">代码沙箱 💻</button>
          </div>

          <div class="tabs-content">
            <div v-if="activeTab === 'info'" class="tab-pane info-pane">
              <h2>{{ lesson?.title }}</h2>
              <div class="desc" v-html="lesson?.content || '<p class=\'text-muted\'>暂无文本介绍</p>'"></div>
            </div>

            <div v-if="activeTab === 'assignments'" class="tab-pane">
              <div v-if="!course?.assignments || course.assignments.length === 0" class="empty-msg">
                🎉 本课程暂无作业
              </div>
              <div v-else class="assignment-list">
                <div v-for="assign in course.assignments" :key="assign.id" class="assignment-card">
                  <div class="assign-header">
                    <div class="title-row">
                        <h3>{{ assign.title }}</h3>
                        <span class="type-tag">{{ assign.assignment_type === 'choice' ? '选择题' : '图文/文件' }}</span>
                    </div>
                    <span v-if="assign.my_submission" :class="`status-badge ${assign.my_submission.status}`">
                      {{ assign.my_submission.status === 'passed' ? '✅ 已通过' : (assign.my_submission.status === 'rejected' ? '❌ 需修改' : '⏳ 已提交') }}
                    </span>
                    <span v-else class="assign-date">{{ new Date(assign.created_at).toLocaleDateString() }}</span>
                  </div>

                  <p class="assign-desc">{{ assign.description }}</p>

                  <div v-if="assign.attachment" class="attachment-link">
                        <a href="#" @click.prevent="handleDownload(assign.attachment)" class="download-btn">
                            📥 下载附件
                        </a>
                  </div>

                  <div v-if="assign.my_submission" class="submission-result">
                    <div class="result-box">
                      <p v-if="assign.assignment_type === 'choice'">
                          <strong>我的答案：</strong> {{ parseAnswer(assign.my_submission.content) }}
                      </p>
                      <p v-else>
                          <strong>我的提交：</strong> {{ assign.my_submission.content }}
                      </p>
                      <p v-if="assign.my_submission.grade !== null"><strong>评分：</strong> {{ assign.my_submission.grade }} 分</p>
                      <p v-if="assign.my_submission.feedback"><strong>反馈：</strong> {{ assign.my_submission.feedback }}</p>
                    </div>
                    <button v-if="assign.my_submission.status === 'rejected'" @click="toggleAssignmentForm(assign.id)" class="btn-retry">重做</button>
                  </div>

                  <div v-else>
                    <button @click="toggleAssignmentForm(assign.id)" class="btn-submit-toggle">
                      {{ activeAssignmentId === assign.id ? '取消' : '开始作答' }}
                    </button>
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
                        <div v-else class="empty-quiz-msg">⚠️ 未找到题目数据，请联系老师。</div>
                    </div>

                    <div v-else>
                        <textarea v-model="submissionContent" placeholder="作业内容..." rows="4"></textarea>
                        <div class="form-group file-upload">
                            <label>上传附件:</label>
                            <input type="file" @change="handleSubmissionFileChange" />
                        </div>
                    </div>

                    <button
                      @click="handleSubmitAssignment(assign)"
                      class="btn-confirm-submit"
                      :disabled="isSubmitting"
                    >
                      {{ isSubmitting ? '提交中...' : '确认提交' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="activeTab === 'comments'" class="tab-pane">
              <div class="comment-input-box">
                <textarea v-model="newComment" placeholder="发表你的看法..." rows="2"></textarea>
                <button @click="handlePostComment" :disabled="isPostingComment">发布</button>
              </div>
              <ul class="comment-list">
                <CommentItem v-for="c in comments" :key="c.id" :comment="c" @comment-posted="fetchComments(props.lessonId)" />
                <li v-if="comments.length === 0" class="empty-msg">暂无评论，快来抢沙发！</li>
              </ul>
            </div>

            <div v-if="activeTab === 'notes'" class="tab-pane full-height">
              <VideoNotes :lesson-id="props.lessonId" :current-time="currentTime" @seek="handleSeek" />
            </div>

            <div v-if="activeTab === 'code'" class="tab-pane full-height">
              <CodeSandbox />
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="playlist-sidebar">
      <div class="playlist-header">
        <h4>课程目录</h4>
        <span class="course-name-sub">{{ course?.title }}</span>
      </div>
      <div class="playlist-body">
        <div v-for="module in safeModules" :key="module.id" class="module-block">
          <div class="module-title">{{ module.title }}</div>
          <ul>
            <li v-for="(l, idx) in getSafeLessons(module)" :key="l.id" class="playlist-item" :class="{ 'playing': l.id == props.lessonId }" @click="router.push({ name: 'lesson-watch', params: { courseId: props.courseId, lessonId: l.id } })">
              <span class="status-icon">{{ l.id == props.lessonId ? '▶' : (idx + 1) }}</span>
              <span class="item-title">{{ l.title }}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <AITutor />
  </div>
</template>

<style scoped>
/* 复用样式 */
.watch-container { display: flex; height: calc(100vh - 70px); background: #f9fafb; overflow: hidden; }
.content-wrapper { flex: 1; display: flex; flex-direction: column; overflow-y: auto; padding: 20px 40px; }
.main-column { width: 100%; max-width: 1100px; margin: 0 auto; display: flex; flex-direction: column; }
.nav-header { display: flex; align-items: center; gap: 10px; margin-bottom: 15px; }
.separator { color: #ccc; }
.current-title { font-weight: 600; color: #333; font-size: 1.1rem; }
.video-stage { width: 100%; background: black; border-radius: 12px 12px 0 0; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
.video-wrapper { width: 100%; aspect-ratio: 16/9; background: #000; }
.html5-player { width: 100%; height: 100%; display: block; }
.placeholder-screen { padding: 100px; text-align: center; color: #fff; background: #1a1a1a; aspect-ratio: 16/9; display: flex; align-items: center; justify-content: center; flex-direction: column; }
.tabs-container { width: 100%; background: white; border-radius: 0 0 12px 12px; border: 1px solid #e5e7eb; border-top: none; display: flex; flex-direction: column; min-height: 600px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); margin-bottom: 40px; }
.tabs-header { display: flex; border-bottom: 1px solid #e5e7eb; background: #fdfdfd; }
.tabs-header button { padding: 16px 24px; border: none; background: none; cursor: pointer; font-size: 1rem; font-weight: 500; color: #64748b; border-bottom: 2px solid transparent; transition: all 0.2s; }
.tabs-header button:hover { color: #4f46e5; background: #f8fafc; }
.tabs-header button.active { color: #4f46e5; border-bottom-color: #4f46e5; background: white; font-weight: 600; }
.tabs-content { padding: 30px; flex: 1; display: flex; flex-direction: column; }
.tab-pane { flex: 1; }
.tab-pane.full-height { height: 100%; display: flex; flex-direction: column; }
.info-pane h2 { margin-top: 0; margin-bottom: 20px; font-size: 1.5rem; color: #1e293b; }
.desc { line-height: 1.8; color: #334155; font-size: 1.05rem; }
.text-muted { color: #94a3b8; font-style: italic; }
.comment-input-box { display: flex; gap: 15px; margin-bottom: 30px; align-items: flex-start; }
.comment-input-box textarea { flex: 1; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; resize: vertical; font-family: inherit; transition: border 0.2s; }
.comment-input-box textarea:focus { border-color: #4f46e5; outline: none; }
.comment-input-box button { padding: 10px 24px; background: #4f46e5; color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
.comment-input-box button:hover { background: #4338ca; }
.comment-list { list-style: none; padding: 0; margin: 0; }
.empty-msg { text-align: center; padding: 40px; color: #94a3b8; }
.playlist-sidebar { width: 320px; background: white; border-left: 1px solid #e5e7eb; display: flex; flex-direction: column; z-index: 10; }
.playlist-header { padding: 20px; border-bottom: 1px solid #e5e7eb; background: #f8fafc; }
.playlist-header h4 { margin: 0 0 5px 0; font-size: 1rem; color: #334155; }
.course-name-sub { font-size: 0.85rem; color: #64748b; }
.playlist-body { flex: 1; overflow-y: auto; padding: 10px 0; }
.module-block { margin-bottom: 5px; }
.module-title { padding: 12px 20px; background: #f1f5f9; font-size: 0.85rem; color: #475569; font-weight: 700; letter-spacing: 0.5px; }
.playlist-item { padding: 14px 20px; cursor: pointer; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #f1f5f9; transition: background 0.2s; }
.playlist-item:hover { background: #f8fafc; }
.playlist-item.playing { background: #e0e7ff; border-left: 3px solid #4f46e5; padding-left: 17px; }
.playlist-item.playing .item-title { color: #4f46e5; font-weight: 600; }
.status-icon { font-size: 0.8rem; color: #94a3b8; width: 15px; text-align: center; }
.playing .status-icon { color: #4f46e5; }
.item-title { font-size: 0.95rem; color: #334155; line-height: 1.4; }

.assignment-list { display: flex; flex-direction: column; gap: 15px; }
.assignment-card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; background: #fff; }
.assign-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.title-row { display: flex; align-items: center; gap: 10px; }
.type-tag { background: #e0e7ff; color: #4f46e5; font-size: 0.75rem; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
.assign-header h3 { margin: 0; font-size: 1.1rem; color: #333; }
.assign-date { font-size: 0.85rem; color: #999; }
.status-badge { font-size: 0.85rem; padding: 4px 8px; border-radius: 4px; font-weight: 500; }
.status-badge.pending { background: #f3f4f6; color: #6b7280; }
.status-badge.passed { background: #d1fae5; color: #059669; }
.status-badge.rejected { background: #fee2e2; color: #dc2626; }

.assign-desc { color: #666; font-size: 0.95rem; margin-bottom: 15px; line-height: 1.5; }
.download-btn { display: inline-block; margin-bottom: 15px; color: #4f46e5; text-decoration: none; font-weight: 500; font-size: 0.9rem; cursor: pointer; }
.download-btn:hover { text-decoration: underline; }
.link-download { color: #4f46e5; cursor: pointer; }

.btn-submit-toggle { background: #4f46e5; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 0.9rem; }
.btn-submit-toggle:hover { background: #4338ca; }
.btn-retry { background: #f59e0b; color: white; border: none; padding: 6px 12px; border-radius: 4px; font-size: 0.85rem; margin-top: 10px; cursor: pointer; }
.submission-form { margin-top: 15px; padding: 15px; background: #f9fafb; border-radius: 6px; }
.submission-form textarea { width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 6px; margin-bottom: 10px; font-family: inherit; }
.file-upload { margin-bottom: 15px; }
.hint { font-size: 0.8rem; color: #999; margin-top: 4px; }

.btn-confirm-submit { background: #10b981; color: white; border: none; padding: 8px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; }
.btn-confirm-submit:disabled { opacity: 0.6; cursor: not-allowed; }
.submission-result { margin-top: 10px; }
.result-box { background: #f0fdf4; border: 1px solid #bbf7d0; padding: 15px; border-radius: 6px; font-size: 0.95rem; color: #166534; }
.result-box p { margin: 5px 0; }

.choice-container { display: flex; flex-direction: column; gap: 20px; }
.question-block { background: white; padding: 15px; border-radius: 6px; border: 1px solid #e5e7eb; }
.q-title { font-weight: bold; margin-bottom: 10px; color: #1f2937; }
.radio-group { display: flex; flex-direction: column; gap: 8px; }
.radio-item { display: flex; align-items: center; gap: 10px; cursor: pointer; padding: 5px; border-radius: 4px; transition: background 0.2s; }
.radio-item:hover { background: #f3f4f6; }
.opt-text { color: #4b5563; }
.empty-quiz-msg { color: #ef4444; font-weight: bold; padding: 10px; }

@media (max-width: 1200px) {
  .watch-container { flex-direction: column; height: auto; overflow: visible; }
  .playlist-sidebar { width: 100%; border-left: none; border-top: 1px solid #e5e7eb; height: auto; max-height: 500px; }
  .content-wrapper { padding: 20px; }
}
</style>
