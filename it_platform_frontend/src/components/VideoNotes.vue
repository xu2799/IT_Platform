<script setup>
import { ref, onMounted, watch } from 'vue'
import apiClient from '@/api'
import { formatDate } from '@/utils/common'

const props = defineProps({
  lessonId: { type: [String, Number], required: true },
  currentTime: { type: Number, default: 0 }
})

const emit = defineEmits(['seek'])

const notes = ref([])
const content = ref('')
const isSubmitting = ref(false)

const fetchNotes = async () => {
  try {
    const res = await apiClient.get('/api/notes/', { params: { lesson_id: props.lessonId } })
    notes.value = res.data.results || res.data
  } catch (e) {
    console.error('获取笔记失败', e)
  }
}

const handleAddNote = async () => {
  if (!content.value.trim()) return
  isSubmitting.value = true
  try {
    const res = await apiClient.post('/api/notes/', {
      lesson: props.lessonId,
      content: content.value,
      video_timestamp: props.currentTime
    })
    notes.value.unshift(res.data)
    content.value = ''
  } catch (e) {
    alert('笔记保存失败')
  } finally {
    isSubmitting.value = false
  }
}

const handleDelete = async (id) => {
  if(!confirm('删除此笔记？')) return
  try {
    await apiClient.delete(`/api/notes/${id}/`)
    notes.value = notes.value.filter(n => n.id !== id)
  } catch(e) { alert('删除失败') }
}

const formatTime = (seconds) => {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

watch(() => props.lessonId, fetchNotes, { immediate: true })
</script>

<template>
  <div class="notes-container">
    <div class="input-area">
      <div class="time-badge">当前进度: {{ formatTime(currentTime) }}</div>
      <textarea v-model="content" placeholder="记录当下的灵感..." rows="3"></textarea>
      <button @click="handleAddNote" :disabled="isSubmitting">记笔记</button>
    </div>
    <ul class="notes-list">
      <li v-for="note in notes" :key="note.id" class="note-item">
        <div class="note-header">
          <span class="timestamp" @click="emit('seek', note.video_timestamp)">
            ▶ {{ formatTime(note.video_timestamp) }}
          </span>
          <span class="date">{{ formatDate(note.created_at) }}</span>
          <button class="btn-del" @click="handleDelete(note.id)">×</button>
        </div>
        <p class="note-content">{{ note.content }}</p>
      </li>
      <li v-if="notes.length === 0" class="empty">暂无笔记</li>
    </ul>
  </div>
</template>

<style scoped>
.notes-container { display: flex; flex-direction: column; height: 100%; }
.input-area { padding: 15px; border-bottom: 1px solid #eee; background: #f9fafb; }
.time-badge { font-size: 0.8rem; color: #4f46e5; font-weight: bold; margin-bottom: 5px; }
textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; resize: vertical; font-family: inherit; }
.input-area button { margin-top: 8px; width: 100%; background: #4f46e5; color: white; border: none; padding: 8px; border-radius: 4px; cursor: pointer; }
.input-area button:disabled { opacity: 0.6; }
.notes-list { flex: 1; overflow-y: auto; list-style: none; padding: 0; margin: 0; }
.note-item { padding: 15px; border-bottom: 1px solid #f3f4f6; }
.note-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
.timestamp { color: #4f46e5; cursor: pointer; font-weight: bold; font-size: 0.9rem; background: #e0e7ff; padding: 2px 6px; border-radius: 4px; }
.timestamp:hover { background: #c7d2fe; }
.date { font-size: 0.75rem; color: #9ca3af; }
.btn-del { border: none; background: none; color: #999; cursor: pointer; font-size: 1.2rem; line-height: 1; }
.btn-del:hover { color: #ef4444; }
.note-content { margin: 0; font-size: 0.9rem; color: #374151; white-space: pre-wrap; }
.empty { text-align: center; padding: 20px; color: #9ca3af; }
</style>
