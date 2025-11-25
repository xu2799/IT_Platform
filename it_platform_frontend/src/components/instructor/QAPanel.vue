<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '@/api'
import { formatDate } from '@/utils/common'

const comments = ref([])
const replyContent = ref('')
const activeReplyId = ref(null)

const fetchQA = async () => {
  try {
    const res = await apiClient.get('/api/instructor/qa/')
    comments.value = res.data.results || res.data
  } catch (e) { console.error(e) }
}

const handleReply = async (comment) => {
  if (!replyContent.value.trim()) return
  try {
    await apiClient.post('/api/comments/', {
      lesson: comment.lesson,
      content: replyContent.value,
      parent: comment.id,
      reply_to_user_id: comment.user.id
    })
    alert('回复成功！')
    replyContent.value = ''
    activeReplyId.value = null
    fetchQA()
  } catch (e) { alert('回复失败') }
}

onMounted(fetchQA)
</script>

<template>
  <div class="qa-panel">
    <div v-if="comments.length === 0" class="empty">暂无待处理提问</div>
    <ul class="qa-list">
      <li v-for="c in comments" :key="c.id" class="qa-item">
        <div class="qa-header">
          <span class="user">{{ c.user.username }}</span>
          <span class="course">在课程 #{{ c.lesson }} 提问</span>
          <span class="time">{{ formatDate(c.created_at) }}</span>
        </div>
        <p class="qa-content">{{ c.content }}</p>

        <div class="qa-actions">
          <button v-if="activeReplyId !== c.id" @click="activeReplyId = c.id" class="btn-reply">回复</button>
          <div v-else class="reply-box">
            <textarea v-model="replyContent" placeholder="输入讲师回复..."></textarea>
            <div class="btn-group">
              <button @click="handleReply(c)" class="btn-send">发送</button>
              <button @click="activeReplyId = null" class="btn-cancel">取消</button>
            </div>
          </div>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.qa-list { list-style: none; padding: 0; }
.qa-item { background: white; padding: 20px; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 15px; }
.qa-header { font-size: 0.85rem; color: #6b7280; margin-bottom: 8px; }
.qa-header .user { font-weight: bold; color: #333; margin-right: 10px; }
.qa-content { font-size: 1rem; color: #1f2937; margin-bottom: 15px; }
.btn-reply { color: #4f46e5; background: none; border: none; cursor: pointer; font-weight: 600; }
.reply-box textarea { width: 100%; border: 1px solid #ddd; border-radius: 6px; padding: 10px; margin-bottom: 10px; }
.btn-group { display: flex; gap: 10px; }
.btn-send { background: #4f46e5; color: white; padding: 5px 15px; border-radius: 4px; border: none; cursor: pointer; }
.btn-cancel { background: #eee; color: #333; padding: 5px 15px; border-radius: 4px; border: none; cursor: pointer; }
.empty { text-align: center; padding: 40px; color: #999; }
</style>
