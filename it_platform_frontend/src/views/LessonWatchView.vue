<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useCourseStore } from '@/stores/courseStore'
import { useAuthStore } from '@/stores/authStore'
import apiClient from '@/api'
import BackButton from '@/components/BackButton.vue'
import CommentItem from '@/components/CommentItem.vue'
// 【优化】：导入工具函数，移除组件内冗余定义
import { getFullMediaUrl } from '@/utils/common'

const router = useRouter()
const route = useRoute()
const courseStore = useCourseStore()
const authStore = useAuthStore()

const props = defineProps({
  courseId: { type: String, required: true },
  lessonId: { type: String, required: true }
})

const videoPlayer = ref(null)
const videoError = ref(null)
const newComment = ref('')
const isPostingComment = ref(false)
const comments = ref([])

const isLikePending = ref(false)
const isFavoritePending = ref(false)
const likeJustChanged = ref(false)
const favoriteJustChanged = ref(false)

onMounted(async () => {
  try { await courseStore.fetchCourseDetail(props.courseId) } catch (e) {}
  fetchComments(props.lessonId)
})

const course = computed(() => courseStore.courses.find(c => c && c.id == props.courseId) || null)
const currentLikeCount = computed(() => course.value?.like_count || 0)
const currentIsLiked = computed(() => course.value?.is_liked || false)
const currentIsFavorited = computed(() => authStore.isCourseFavorited(props.courseId))

const lesson = computed(() => {
  if (!course.value?.modules) return null
  for (const m of course.value.modules) {
    for (const l of (m.lessons || [])) {
      if (l.id == props.lessonId) return l
    }
  }
  return null
})

const videoUrl = computed(() => {
  const l = lesson.value
  if (!l) return null
  if (l.video_mp4_file) return getFullMediaUrl(l.video_mp4_file)
  if (l.video_m3u8_url && !l.video_m3u8_url.includes('example.com')) return getFullMediaUrl(l.video_m3u8_url)
  return null
})

const safeModules = computed(() => (course.value?.modules || []).filter(m => m && typeof m === 'object'))
const getSafeLessons = (m) => (m?.lessons || []).filter(l => l && typeof l === 'object')

watch(videoUrl, (newUrl) => { if (newUrl && videoPlayer.value) videoPlayer.value.load() })
watch(() => props.lessonId, (newId) => { if (newId) fetchComments(newId) })

const handleVideoError = (e) => { videoError.value = `无法播放: ${e.target.error?.message || '未知错误'}` }

const goToNextLesson = () => {
    let foundCurrent = false;
    let nextLesson = null;
    for (const m of safeModules.value) {
        for (const l of getSafeLessons(m)) {
            if (foundCurrent) { nextLesson = l; break; }
            if (l.id == props.lessonId) foundCurrent = true;
        }
        if (nextLesson) break;
    }
    if (nextLesson) router.push({ name: 'lesson-watch', params: { courseId: props.courseId, lessonId: nextLesson.id } })
    else alert('恭喜，已学完所有课程！')
}

const fetchComments = async (id) => {
  if (!id) return;
  try {
    const res = await apiClient.get('/api/comments/', { params: { lesson_id: id } })
    comments.value = Array.isArray(res.data) ? res.data : []
  } catch (e) { comments.value = [] }
}

const handlePostComment = async () => {
  if (!newComment.value.trim()) return
  if (!authStore.isAuthenticated) { router.push({ name: 'login' }); return }
  isPostingComment.value = true
  try {
    const res = await apiClient.post('/api/comments/', {
      lesson: Number(props.lessonId), content: newComment.value, parent: null
    })
    comments.value.unshift(res.data)
    newComment.value = ''
  } finally { isPostingComment.value = false }
}

const handleLikeToggle = async () => {
    if (isLikePending.value || !authStore.isAuthenticated) return
    isLikePending.value = true
    try {
        const res = await apiClient.post(`/api/courses/${props.courseId}/like/`)
        courseStore.updateCourseLikeStatus(props.courseId, res.data.liked, res.data.like_count)
        likeJustChanged.value = true
        setTimeout(() => likeJustChanged.value = false, 1000)
    } finally { isLikePending.value = false }
}

const handleFavoriteToggle = async () => {
    if (isFavoritePending.value || !authStore.isAuthenticated) return
    isFavoritePending.value = true
    try {
        const { success, favorited } = await authStore.toggleFavorite(props.courseId)
        if (success) {
            courseStore.updateCourseFavoriteStatus(props.courseId, favorited)
            favoriteJustChanged.value = true
            setTimeout(() => favoriteJustChanged.value = false, 1000)
        }
    } finally { isFavoritePending.value = false }
}

// 获取当前用户头像 (用于评论输入框)
const myAvatarUrl = computed(() => {
  if (!authStore.isAuthenticated) return 'https://via.placeholder.com/40'
  if (authStore.user?.avatar) return getFullMediaUrl(authStore.user.avatar)
  return `https://ui-avatars.com/api/?name=${authStore.user?.username}&background=4f46e5&color=fff`
})
</script>

<template>
  <div class="watch-container">

    <div class="main-view">
      <div class="nav-header">
        <BackButton :fallback-route="{ name: 'course-detail', params: { id: props.courseId } }" text="返回详情" small inline />
        <span class="separator">/</span>
        <span class="current-title">{{ lesson?.title || '加载中...' }}</span>
      </div>

      <div class="video-stage">
        <div v-if="videoUrl" class="video-wrapper">
          <video ref="videoPlayer" :src="videoUrl" controls autoplay playsinline class="html5-player" @error="handleVideoError"></video>
        </div>
        <div v-else-if="lesson?.lesson_type === 'text'" class="text-reader"><div v-html="lesson.content"></div></div>
        <div v-else class="placeholder-screen">
          <div class="spinner" v-if="!videoError"></div>
          <p>{{ videoError || '正在加载资源...' }}</p>
        </div>
      </div>

      <div class="toolbar">
        <div class="tool-group">
          <button @click="handleLikeToggle" class="tool-btn" :class="{ active: currentIsLiked, pop: likeJustChanged }">
            <span class="icon">👍</span> {{ currentLikeCount }}
          </button>
          <button @click="handleFavoriteToggle" class="tool-btn" :class="{ active: currentIsFavorited, pop: favoriteJustChanged }">
            <span class="icon">⭐</span> {{ currentIsFavorited ? '已收藏' : '收藏' }}
          </button>
        </div>
        <button @click="goToNextLesson" class="next-pill-btn">
          下一课 <span class="arrow">→</span>
        </button>
      </div>

      <div class="discussion-area">
        <h3 class="area-title">学员讨论 <span class="count">({{ comments.length }})</span></h3>

        <div class="comment-input-row">
          <div class="my-avatar">
            <img :src="myAvatarUrl" alt="Me">
          </div>
          <div class="input-field-wrapper">
            <textarea v-model="newComment" placeholder="发一条友善的评论..." rows="2" :disabled="isPostingComment"></textarea>
            <button v-if="authStore.isAuthenticated" @click="handlePostComment" class="send-btn" :disabled="!newComment.trim() || isPostingComment">发布</button>
            <RouterLink v-else :to="{ name: 'login' }" class="login-link-btn">登录后评论</RouterLink>
          </div>
        </div>

        <ul class="comment-list">
          <CommentItem v-for="c in comments" :key="c.id" :comment="c" @comment-posted="fetchComments(props.lessonId)" />
          <li v-if="comments.length === 0" class="empty-state">还没有人评论，来坐沙发吧~</li>
        </ul>
      </div>
    </div>

    <div class="playlist-sidebar">
      <div class="playlist-header">
        <h4>课程目录</h4>
        <p>{{ course?.title }}</p>
      </div>
      <div class="playlist-body">
        <div v-for="module in safeModules" :key="module.id" class="module-block">
          <div class="module-title">{{ module.title }}</div>
          <ul>
            <li
              v-for="(l, idx) in getSafeLessons(module)"
              :key="l.id"
              class="playlist-item"
              :class="{ 'playing': l.id == props.lessonId }"
              @click="router.push({ name: 'lesson-watch', params: { courseId: props.courseId, lessonId: l.id } })"
            >
              <span class="status-icon">{{ l.id == props.lessonId ? '▶' : (idx + 1) }}</span>
              <span class="item-title">{{ l.title }}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.watch-container { display: flex; height: calc(100vh - 70px); background: #f9fafb; overflow: hidden; }
.main-view { flex: 1; overflow-y: auto; padding: 20px 40px; }
.nav-header { display: flex; align-items: center; gap: 10px; margin-bottom: 20px; }
.separator { color: #ccc; }
.current-title { font-weight: 600; font-size: 1.1rem; color: #1f2937; }

/* 限制视频播放器宽度，使其变小且居中 */
.video-stage {
  background: black;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 15px 35px rgba(0,0,0,0.15);
  margin-bottom: 20px;
  min-height: 300px;
  max-width: 900px;
  margin-left: auto;
  margin-right: auto;
  display: flex;
  flex-direction: column;
}
.video-wrapper { width: 100%; aspect-ratio: 16/9; background: black; }
.html5-player { width: 100%; height: 100%; display: block; }
.text-reader { background: white; flex-grow: 1; padding: 40px; overflow-y: auto; font-size: 1.1rem; line-height: 1.8; color: #333; min-height: 300px; }
.placeholder-screen { display: flex; flex-direction: column; align-items: center; justify-content: center; flex-grow: 1; color: #999; background: #1a1a1a; min-height: 300px; }

.toolbar { margin-top: 20px; display: flex; justify-content: space-between; align-items: center; padding-bottom: 20px; border-bottom: 1px solid #e5e7eb; max-width: 900px; margin-left: auto; margin-right: auto; }
.tool-group { display: flex; gap: 12px; }
.tool-btn { display: flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 20px; border: 1px solid #e5e7eb; background: white; color: #4b5563; cursor: pointer; font-weight: 500; transition: all 0.2s; }
.tool-btn:hover { background: #f3f4f6; }
.tool-btn.active { color: #ef4444; background: #fef2f2; border-color: #fecaca; }
.next-pill-btn { background: #4f46e5; color: white; padding: 10px 24px; border-radius: 30px; border: none; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px; box-shadow: 0 4px 10px rgba(79,70,229,0.3); transition: transform 0.2s; }
.next-pill-btn:hover { background: #4338ca; transform: translateY(-1px); }

.discussion-area { margin-top: 30px; max-width: 900px; margin-left: auto; margin-right: auto; }
.area-title { font-size: 1.25rem; font-weight: 700; margin-bottom: 20px; }
.count { color: #9ca3af; font-size: 1rem; font-weight: 400; }
.comment-input-row { display: flex; gap: 15px; margin-bottom: 30px; }
.my-avatar img { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; }
.input-field-wrapper { flex-grow: 1; position: relative; }
.input-field-wrapper textarea { width: 100%; padding: 12px; border-radius: 10px; border: 1px solid #e5e7eb; resize: none; font-family: inherit; transition: border-color 0.2s; }
.input-field-wrapper textarea:focus { border-color: #4f46e5; outline: none; }
.send-btn { position: absolute; bottom: 10px; right: 10px; background: #4f46e5; color: white; border: none; padding: 6px 14px; border-radius: 6px; font-size: 0.85rem; cursor: pointer; }
.login-link-btn { position: absolute; bottom: 12px; right: 12px; font-size: 0.9rem; color: #4f46e5; font-weight: 600; }
.empty-state { text-align: center; padding: 40px; color: #9ca3af; font-style: italic; }
.comment-list { list-style: none; padding: 0; margin-top: 50px; }

.playlist-sidebar { width: 350px; background: white; border-left: 1px solid #e5e7eb; display: flex; flex-direction: column; }
.playlist-header { padding: 20px; border-bottom: 1px solid #f3f4f6; background: #f9fafb; }
.playlist-header h4 { margin: 0; font-size: 1rem; font-weight: 700; color: #374151; }
.playlist-header p { margin: 5px 0 0; font-size: 0.85rem; color: #6b7280; }
.playlist-body { flex: 1; overflow-y: auto; padding: 10px 0; }
.module-block { margin-bottom: 5px; }
.module-title { padding: 8px 20px; font-size: 0.85rem; font-weight: 600; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px; }
.playlist-item { padding: 12px 20px; display: flex; align-items: center; gap: 12px; cursor: pointer; transition: background 0.2s; border-left: 3px solid transparent; }
.playlist-item:hover { background: #f9fafb; }
.playlist-item.playing { background: #eff6ff; border-left-color: #4f46e5; }
.playlist-item.playing .item-title { color: #4f46e5; font-weight: 600; }
.status-icon { font-size: 0.8rem; color: #9ca3af; width: 20px; text-align: center; }
.playing .status-icon { color: #4f46e5; }
.item-title { font-size: 0.95rem; color: #374151; }

@media (max-width: 1024px) {
  .watch-container { flex-direction: column; height: auto; overflow: visible; }
  .playlist-sidebar { width: 100%; height: auto; border-left: none; border-top: 1px solid #e5e7eb; }
  .main-view { padding: 20px; }
}
</style>
