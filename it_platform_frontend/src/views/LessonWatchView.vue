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

// --- 4. 视频地址计算 (依赖 getFullCoverImagePath) ---
const videoUrl = computed(() => {
  const l = lesson.value
  if (!l) return null
  if (l.video_mp4_file) return getFullCoverImagePath(l.video_mp4_file)
  if (l.video_m3u8_url) return getFullCoverImagePath(l.video_m3u8_url)
  return null
})

// --- 5. 生命周期与监听 ---
onMounted(async () => {
  try { await courseStore.fetchCourseDetail(props.courseId) } catch (e) {}
  fetchComments(props.lessonId)
})

const handleTimeUpdate = (e) => { currentTime.value = e.target.currentTime }
const handleSeek = (time) => { if (videoPlayer.value) { videoPlayer.value.currentTime = time; videoPlayer.value.play() } }

watch(videoUrl, (newUrl) => { if (newUrl && videoPlayer.value) videoPlayer.value.load() })
watch(() => props.lessonId, (newId) => { if (newId) fetchComments(newId) })

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

// --- 其他占位函数 ---
const handleDownload = async (url) => { /* ... */ }
const toggleAssignmentForm = (assignId) => { /* ... */ }
const handleSubmissionFileChange = (event) => { /* ... */ }
const handleSubmitAssignment = async (assign) => { /* ... */ }
const parseAnswer = (jsonStr) => { /* ... */ }

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
               <div v-else>请在课程详情页查看作业</div>
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
.item-title { font-size: 0.95rem; color: #334155; line-height: 1.4; }

@media (max-width: 1200px) {
  .watch-container { flex-direction: column; height: auto; overflow: visible; }
  .playlist-sidebar { width: 100%; border-left: none; border-top: 1px solid #e5e7eb; height: auto; max-height: 500px; }
  .content-wrapper { padding: 20px; }
}
</style>
