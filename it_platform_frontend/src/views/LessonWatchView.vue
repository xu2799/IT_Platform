<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useCourseStore } from '@/stores/courseStore'
import { useAuthStore } from '@/stores/authStore'
import apiClient from '@/api'
import { useRouter, useRoute, RouterLink } from 'vue-router'
import CommentItem from '@/components/CommentItem.vue'
import VideoNotes from '@/components/VideoNotes.vue'
import CodeSandbox from '@/components/CodeSandbox.vue'
import AITutor from '@/components/AITutor.vue'
import CustomVideoPlayer from '@/components/CustomVideoPlayer.vue'

const courseStore = useCourseStore()
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const props = defineProps({
  courseId: { type: String, required: true },
  lessonId: { type: String, required: true }
})

// --- 1. 工具函数 (移到最前面，防止 ReferenceError) ---
const getFullCoverImagePath = (path) => {
    if(!path) return ''
    const baseUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
    return path.startsWith('http') ? path : `${baseUrl}${path}`
}

// --- 2. 状态定义 ---
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

// 自动播放下一课
const showNextLessonPrompt = ref(false)
const nextLessonCountdown = ref(3)
let countdownTimer = null

// Toast提示
const toastMessage = ref('')
const showToast = ref(false)

// 笔记模式
const notesMode = ref('lesson') // 'lesson' = 本课笔记, 'global' = 全部笔记

// --- 3. 获取课程与课时数据 ---
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

// 计算下一课
const nextLesson = computed(() => {
  if (!course.value?.modules) return null
  
  let found = false
  for (const module of course.value.modules) {
    const lessons = getSafeLessons(module)
    for (let i = 0; i < lessons.length; i++) {
      if (found && lessons[i]) return lessons[i]
      if (lessons[i].id == props.lessonId) {
        found = true
      }
    }
  }
  return null
})

// --- 4. 视频地址计算 (依赖 getFullCoverImagePath) ---
const videoUrl = computed(() => {
  const l = lesson.value
  if (!l) return null
  if (l.video_mp4_file) return getFullCoverImagePath(l.video_mp4_file)
  if (l.video_m3u8_url) return getFullCoverImagePath(l.video_m3u8_url)
  return null
})

// --- 5. 生命周期与监听 ---
let progressSaveInterval = null

onMounted(async () => {
  // 强制刷新获取课程详情，确保数据最新
  try { 
    await courseStore.fetchCourseDetail(props.courseId, true) 
  } catch (e) {
    console.error('获取课程详情失败:', e)
  }
  
  // 获取评论
  fetchComments(props.lessonId)
  
  // 加载上次播放进度
  loadVideoProgress()
  
  // 每10秒保存一次进度
  progressSaveInterval = setInterval(() => {
    saveVideoProgress()
  }, 10000)
  
  // 添加键盘事件监听
  window.addEventListener('keydown', handleKeyPress)
})

onUnmounted(() => {
  // 离开时保存进度
  saveVideoProgress()
  if (progressSaveInterval) clearInterval(progressSaveInterval)
  window.removeEventListener('keydown', handleKeyPress)
  if (countdownTimer) clearInterval(countdownTimer)
})

// 加载视频播放进度
const loadVideoProgress = async () => {
  if (!authStore.isAuthenticated) return
  
  // 优先使用 URL query 参数中的时间点
  const queryTime = route.query.t ? parseInt(route.query.t) : null
  
  let targetPosition = queryTime
  
  // 如果没有 query 参数，尝试从 API 获取
  if (!targetPosition) {
    try {
      const res = await apiClient.get('/api/video-progress/get_progress/', {
        params: { lesson_id: props.lessonId }
      })
      if (res.data.last_position > 0) {
        targetPosition = res.data.last_position
      }
    } catch (e) { console.log('No saved progress') }
  }
  
  // 如果有目标时间点，等待播放器加载后跳转
  if (targetPosition && targetPosition > 0) {
    // 使用 MutationObserver 或轮询等待 CustomVideoPlayer 组件准备好
    const trySeek = () => {
      if (videoPlayer.value && typeof videoPlayer.value.seekTo === 'function') {
        // 使用 CustomVideoPlayer 的 seekTo 方法
        setTimeout(() => {
          videoPlayer.value.seekTo(targetPosition)
        }, 500)  // 给视频一点加载时间
      } else {
        // 如果组件还没准备好，稍后重试
        setTimeout(trySeek, 100)
      }
    }
    trySeek()
  }
}

// 保存视频播放进度
const saveVideoProgress = async () => {
  if (!authStore.isAuthenticated || !videoPlayer.value) return
  if (currentTime.value < 5) return // 播放不足5秒不保存
  try {
    await apiClient.post('/api/video-progress/', {
      lesson: parseInt(props.lessonId),
      last_position: Math.floor(currentTime.value),
      duration: Math.floor(videoPlayer.value.duration || 0)
    })
  } catch (e) {}
}

// 视频时间更新 (原生 video)
const handleTimeUpdate = (e) => {
  currentTime.value = e.target.currentTime
}

// 自定义播放器时间更新
const handleCustomTimeUpdate = (data) => {
  currentTime.value = data.currentTime
}

// 新增：视频结束处理
const handleVideoEnded = async () => {
  // 触发观看视频积分
  try {
    await apiClient.post('/api/points/add_points/', { action: 'watch' })
  } catch (e) {}
  
  if (nextLesson.value) {
    showNextLessonPrompt.value = true
    nextLessonCountdown.value = 3
    
    countdownTimer = setInterval(() => {
      nextLessonCountdown.value--
      if (nextLessonCountdown.value <= 0) {
        playNextLesson()
      }
    }, 1000)
  }
}

const playNextLesson = () => {
  if (countdownTimer) clearInterval(countdownTimer)
  showNextLessonPrompt.value = false
  
  if (nextLesson.value) {
    router.push({
      name: 'lesson-watch',
      params: { courseId: props.courseId, lessonId: nextLesson.value.id }
    })
  }
}

const cancelAutoPlay = () => {
  if (countdownTimer) clearInterval(countdownTimer)
  showNextLessonPrompt.value = false
}

// 新增：键盘快捷键
const handleKeyPress = (e) => {
  // 如果在输入框中，不响应快捷键
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return
  
  // CustomVideoPlayer 组件内部已处理键盘事件，这里只显示 toast 提示
  const video = videoPlayer.value?.videoRef
  if (!video) return
  
  switch(e.code) {
    case 'Space':
      // 播放/暂停由组件处理，这里只显示提示
      setTimeout(() => displayToast(video.paused ? '⏸ 已暂停' : '▶ 播放中'), 50)
      break
    case 'ArrowRight':
      displayToast('⏩ 快进 5 秒')
      break
    case 'ArrowLeft':
      displayToast('⏪ 后退 5 秒')
      break
    case 'ArrowUp':
      setTimeout(() => displayToast(`🔊 音量: ${Math.round(video.volume * 100)}%`), 50)
      break
    case 'ArrowDown':
      setTimeout(() => displayToast(`🔉 音量: ${Math.round(video.volume * 100)}%`), 50)
      break
    case 'KeyM':
      setTimeout(() => displayToast(video.muted ? '🔇 已静音' : '🔊 取消静音'), 50)
      break
  }
}

// 新增：Toast提示
const displayToast = (message) => {
  toastMessage.value = message
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 2000)
}

const handleSeek = (time) => { if (videoPlayer.value?.seekTo) { videoPlayer.value.seekTo(time) } }

// videoUrl 变化由 CustomVideoPlayer 组件内部处理

// --- 6. 评论功能 ---
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
    // 触发评论积分
    try {
      await apiClient.post('/api/points/add_points/', { action: 'comment' })
    } catch (e) {}
  } finally { isPostingComment.value = false }
}

// --- 7. 导航功能 ---
const goBack = () => {
  if (window.history.length > 1) {
    router.go(-1)
  } else {
    router.push({ name: 'course-detail', params: { id: props.courseId } })
  }
}

// 处理笔记导航（全局模式下点击笔记跳转）
const handleNoteNavigate = ({ lessonId, timestamp }) => {
  if (lessonId != props.lessonId) {
    router.push({
      name: 'lesson-watch',
      params: { courseId: props.courseId, lessonId: lessonId }
    })
  }
  // 如果是当前课时，直接跳转时间
  if (timestamp && videoPlayer.value?.seekTo) {
    videoPlayer.value.seekTo(timestamp)
  }
}

// 打开课时（当前课时不跳转，其他在新窗口打开）
const openLesson = (lessonId) => {
  if (lessonId == props.lessonId) return // 当前课时不操作
  const url = router.resolve({
    name: 'lesson-watch',
    params: { courseId: props.courseId, lessonId: lessonId }
  }).href
  window.open(url, '_blank')
}

// --- 作业与下载功能 ---
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
  } catch (error) { 
    window.open(url, '_blank') 
  } finally { 
    isDownloading.value = false 
  }
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

const handleSubmissionFileChange = (event) => {
  submissionFile.value = event.target.files ? event.target.files[0] : null
}

const handleSubmitAssignment = async (assign) => {
  let contentToSend = ''
  if (assign.assignment_type === 'choice') {
    if (!assign.quiz_questions || assign.quiz_questions.length === 0) {
      return alert('题目数据错误')
    }
    if (Object.keys(quizAnswers.value).length < assign.quiz_questions.length) {
      return alert('请完成所有选择题后再提交')
    }
    contentToSend = JSON.stringify(quizAnswers.value)
  } else {
    if (!submissionContent.value.trim() && !submissionFile.value) {
      return alert('请填写内容')
    }
    contentToSend = submissionContent.value
  }

  if (!authStore.isAuthenticated) {
    return router.push({ name: 'login' })
  }

  isSubmitting.value = true
  const formData = new FormData()
  formData.append('assignment', assign.id)
  formData.append('content', contentToSend)
  if (submissionFile.value) {
    formData.append('attachment', submissionFile.value)
  }

  try {
    await apiClient.post('/api/submissions/', formData, { 
      headers: { 'Content-Type': 'multipart/form-data' } 
    })
    alert(assign.assignment_type === 'choice' ? '提交成功！系统已自动批改。' : '提交成功！')
    activeAssignmentId.value = null
    // 触发提交作业积分
    try {
      await apiClient.post('/api/points/add_points/', { action: 'submit' })
    } catch (e) {}
    // 刷新课程数据以更新提交状态
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
      return Object.entries(obj)
        .map(([idx, ans]) => `第${parseInt(idx)+1}题:${ans}`)
        .join(';  ')
    }
    return jsonStr
  } catch {
    return jsonStr
  }
}

</script>

<template>
  <div class="watch-container">
    <div class="content-wrapper">
      <div class="main-column">

        <div class="nav-header">
          <div class="left-nav">
             <span class="course-name" @click="router.push({ name: 'course-detail', params: { id: props.courseId } })">
                {{ course?.title }}
             </span>
             <span class="separator">/</span>
             <span class="current-title">{{ lesson?.title || '加载中...' }}</span>
          </div>

          <div class="right-actions">
             <button @click="goBack" class="nav-btn-outline">⬅ 返回上一页</button>
             <button @click="router.push({ name: 'courses' })" class="nav-btn-primary">📚 全部课程</button>
          </div>
        </div>

        <div class="video-stage">
          <div v-if="videoUrl" class="video-wrapper">
            <CustomVideoPlayer 
              ref="videoPlayer" 
              :src="videoUrl" 
              :autoplay="true"
              @timeupdate="handleCustomTimeUpdate"
              @ended="handleVideoEnded"
            />
            
            <!-- 下一课提示 -->
            <div v-if="showNextLessonPrompt" class="next-lesson-overlay">
              <div class="next-lesson-card">
                <h3>播放完毕</h3>
                <p v-if="nextLesson">{{ nextLessonCountdown }} 秒后将自动播放下一课</p>
                <p v-else>已完成所有课程</p>
                <div class="next-lesson-info" v-if="nextLesson">
                  <strong>下一课：</strong>{{ nextLesson.title }}
                </div>
                <div class="next-lesson-actions">
                  <button v-if="nextLesson" @click="playNextLesson" class="btn-primary">立即播放</button>
                  <button @click="cancelAutoPlay" class="btn-secondary">取消</button>
                </div>
              </div>
            </div>
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
              <div class="notes-mode-switch">
                <button :class="{ active: notesMode === 'lesson' }" @click="notesMode = 'lesson'">📝 本课笔记</button>
                <button :class="{ active: notesMode === 'global' }" @click="notesMode = 'global'">📚 全部笔记</button>
              </div>
              <VideoNotes 
                :lesson-id="notesMode === 'lesson' ? props.lessonId : null" 
                :course-id="notesMode === 'global' ? props.courseId : null"
                :current-time="currentTime" 
                :global-mode="notesMode === 'global'"
                @seek="handleSeek" 
                @navigate="handleNoteNavigate"
              />
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

    <!-- Toast 提示 -->
    <Transition name="toast">
      <div v-if="showToast" class="toast-notification">
        {{ toastMessage }}
      </div>
    </Transition>

    <AITutor />
  </div>
</template>

<style scoped>
/* 核心布局 */
.watch-container { display: flex; height: calc(100vh - 70px); background: #f9fafb; overflow: hidden; }
.content-wrapper { flex: 1; display: flex; flex-direction: column; overflow-y: auto; padding: 20px 40px; }
.main-column { width: 100%; max-width: 1100px; margin: 0 auto; display: flex; flex-direction: column; }

/* 导航头部样式 */
.nav-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}
.left-nav {
    display: flex;
    align-items: center;
    gap: 10px;
}
.right-actions {
    display: flex;
    gap: 10px;
}
.course-name {
    font-weight: bold;
    color: #4f46e5;
    cursor: pointer;
}
.separator { color: #ccc; }
.current-title { font-weight: 600; color: #333; font-size: 1.1rem; }

/* 按钮样式 */
.nav-btn-outline {
    padding: 6px 15px;
    background: white;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    color: #374151;
    cursor: pointer;
    font-size: 0.9rem;
    transition: all 0.2s;
}
.nav-btn-outline:hover {
    background: #f3f4f6;
    border-color: #9ca3af;
}
.nav-btn-primary {
    padding: 6px 15px;
    background: #4f46e5;
    border: none;
    border-radius: 6px;
    color: white;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 500;
    transition: background 0.2s;
}
.nav-btn-primary:hover {
    background: #4338ca;
}

/* 播放器与Tabs样式 */
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
.item-title { font-size: 0.95rem; color: #334155; line-height: 1.4; flex: 1; }
.new-window-icon { font-size: 0.75rem; color: #94a3b8; opacity: 0; transition: opacity 0.2s; }
.playlist-item:hover .new-window-icon { opacity: 1; }

/* 新增样式 */

/* 下一课提示覆盖层 */
.next-lesson-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  animation: fadeIn 0.3s;
}

.next-lesson-card {
  background: white;
  padding: 40px;
  border-radius: 16px;
  text-align: center;
  max-width: 400px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.3);
}

.next-lesson-card h3 {
  margin: 0 0 15px 0;
  font-size: 1.5rem;
  color: #1f2937;
}

.next-lesson-card p {
  color: #64748b;
  margin-bottom: 20px;
  font-size: 1rem;
}

.next-lesson-info {
  background: #f8fafc;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 25px;
  text-align: left;
}

.next-lesson-info strong {
  color: #4f46e5;
}

.next-lesson-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.next-lesson-actions .btn-primary {
  padding: 12px 24px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.next-lesson-actions .btn-primary:hover {
  background: #4338ca;
}

.next-lesson-actions .btn-secondary {
  padding: 12px 24px;
  background: white;
  color: #64748b;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.next-lesson-actions .btn-secondary:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

/* Toast 通知 */
.toast-notification {
  position: fixed;
  bottom: 100px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.85);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 500;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(10px);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@media (max-width: 1200px) {
  .watch-container { flex-direction: column; height: auto; overflow: visible; }
  .playlist-sidebar { width: 100%; border-left: none; border-top: 1px solid #e5e7eb; height: auto; max-height: 500px; }
  .content-wrapper { padding: 20px; }
}

/* 作业模块样式 */
.assignment-list { display: flex; flex-direction: column; gap: 15px; }
.assignment-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; }
.assign-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 10px; }
.title-row { display: flex; align-items: center; gap: 10px; }
.assign-header h3 { margin: 0; font-size: 1.1rem; color: #1f2937; }
.type-tag { background: #e0e7ff; color: #4f46e5; font-size: 0.75rem; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
.status-badge { font-size: 0.85rem; padding: 4px 8px; border-radius: 4px; font-weight: 500; }
.status-badge.pending { background: #f3f4f6; color: #6b7280; }
.status-badge.passed { background: #d1fae5; color: #059669; }
.status-badge.rejected { background: #fee2e2; color: #dc2626; }
.assign-desc { color: #4b5563; margin-bottom: 10px; font-size: 0.95rem; line-height: 1.5; }
.assign-date { color: #9ca3af; font-size: 0.85rem; }
.attachment-link { margin-bottom: 15px; }
.download-btn { color: #4f46e5; font-size: 0.9rem; cursor: pointer; text-decoration: none; }
.download-btn:hover { text-decoration: underline; }
.btn-submit-toggle { background: #4f46e5; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 500; transition: background 0.2s; }
.btn-submit-toggle:hover { background: #4338ca; }
.btn-retry { background: #f59e0b; color: white; border: none; padding: 6px 12px; border-radius: 4px; margin-top: 10px; cursor: pointer; font-weight: 500; }
.btn-retry:hover { background: #d97706; }
.submission-form { margin-top: 15px; padding: 15px; background: #f9fafb; border-radius: 6px; }
.submission-form textarea { width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 6px; margin-bottom: 10px; font-family: inherit; resize: vertical; }
.submission-form textarea:focus { border-color: #4f46e5; outline: none; }
.form-group.file-upload { margin-bottom: 10px; }
.form-group.file-upload label { display: block; margin-bottom: 5px; color: #4b5563; font-size: 0.9rem; }
.btn-confirm-submit { background: #10b981; color: white; border: none; padding: 10px 24px; border-radius: 6px; cursor: pointer; font-weight: bold; margin-top: 10px; transition: background 0.2s; }
.btn-confirm-submit:hover { background: #059669; }
.btn-confirm-submit:disabled { background: #9ca3af; cursor: not-allowed; }
.choice-container { display: flex; flex-direction: column; gap: 20px; }
.question-block { background: white; padding: 15px; border-radius: 6px; border: 1px solid #e5e7eb; }
.q-title { font-weight: bold; margin-bottom: 10px; color: #1f2937; }
.radio-group { display: flex; flex-direction: column; gap: 8px; }
.radio-item { display: flex; align-items: center; gap: 10px; cursor: pointer; padding: 5px; border-radius: 4px; transition: background 0.2s; }
.radio-item:hover { background: #f3f4f6; }
.opt-text { color: #4b5563; }
.submission-result { margin-top: 15px; }
.result-box { background: #f0fdf4; border: 1px solid #bbf7d0; padding: 15px; border-radius: 6px; font-size: 0.95rem; color: #166534; }
.result-box p { margin: 5px 0; }
.result-box strong { color: #15803d; }

/* 笔记模式切换 */
.notes-mode-switch { display: flex; gap: 10px; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #e5e7eb; }
.notes-mode-switch button { padding: 8px 16px; background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 6px; color: #4b5563; cursor: pointer; font-size: 0.9rem; font-weight: 500; transition: all 0.2s; }
.notes-mode-switch button:hover { background: #e5e7eb; }
.notes-mode-switch button.active { background: #4f46e5; color: white; border-color: #4f46e5; }
</style>
