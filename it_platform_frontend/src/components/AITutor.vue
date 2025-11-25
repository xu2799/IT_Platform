<script setup>
import { ref, nextTick } from 'vue'
import apiClient from '@/api'

const isOpen = ref(false)
const messages = ref([
  { role: 'ai', content: '你好！我是你的 AI 学习助教。关于这节课，你有什么想问的吗？' }
])
const inputMsg = ref('')
const isLoading = ref(false)
const chatBody = ref(null)

const toggleChat = () => { isOpen.value = !isOpen.value }

const scrollToBottom = () => {
  nextTick(() => {
    if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
  })
}

const sendMessage = async () => {
  if (!inputMsg.value.trim() || isLoading.value) return
  const userQ = inputMsg.value
  messages.value.push({ role: 'user', content: userQ })
  inputMsg.value = ''
  scrollToBottom()
  isLoading.value = true
  try {
    const res = await apiClient.post('/api/ai/ask/', { question: userQ })
    messages.value.push({ role: 'ai', content: res.data.answer })
  } catch (e) {
    messages.value.push({ role: 'ai', content: '抱歉，我现在有点忙，请稍后再试。' })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}
</script>

<template>
  <div class="ai-tutor-wrapper">
    <button class="fab-btn" @click="toggleChat" v-if="!isOpen">🤖</button>
    <div class="chat-window" v-if="isOpen">
      <div class="chat-header">
        <span>🤖 AI 智能助教</span>
        <button class="close-btn" @click="toggleChat">×</button>
      </div>
      <div class="chat-body" ref="chatBody">
        <div v-for="(msg, idx) in messages" :key="idx" class="message-row" :class="msg.role">
          <div class="bubble">{{ msg.content }}</div>
        </div>
        <div v-if="isLoading" class="message-row ai">
          <div class="bubble loading">AI 正在思考...</div>
        </div>
      </div>
      <div class="chat-footer">
        <input v-model="inputMsg" @keyup.enter="sendMessage" placeholder="输入问题..." :disabled="isLoading" />
        <button @click="sendMessage" :disabled="isLoading">发送</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ai-tutor-wrapper { position: fixed; bottom: 30px; right: 30px; z-index: 2000; }
.fab-btn { width: 60px; height: 60px; border-radius: 50%; background: linear-gradient(135deg, #6366f1, #a855f7); color: white; border: none; font-size: 30px; cursor: pointer; box-shadow: 0 4px 15px rgba(0,0,0,0.3); transition: transform 0.2s; display: flex; align-items: center; justify-content: center; }
.fab-btn:hover { transform: scale(1.1); }
.chat-window { width: 350px; height: 500px; background: white; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); display: flex; flex-direction: column; overflow: hidden; animation: slideUp 0.3s ease; }
@keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
.chat-header { background: #6366f1; color: white; padding: 15px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; }
.close-btn { background: none; border: none; color: white; font-size: 1.5rem; cursor: pointer; }
.chat-body { flex: 1; padding: 15px; overflow-y: auto; background: #f9fafb; display: flex; flex-direction: column; gap: 10px; }
.message-row { display: flex; }
.message-row.user { justify-content: flex-end; }
.message-row.ai { justify-content: flex-start; }
.bubble { max-width: 80%; padding: 10px 14px; border-radius: 12px; font-size: 0.9rem; line-height: 1.5; }
.user .bubble { background: #6366f1; color: white; border-bottom-right-radius: 2px; }
.ai .bubble { background: white; color: #333; border: 1px solid #eee; border-bottom-left-radius: 2px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
.loading { font-style: italic; color: #888; }
.chat-footer { padding: 10px; border-top: 1px solid #eee; display: flex; gap: 10px; background: white; }
.chat-footer input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 20px; outline: none; }
.chat-footer button { background: #6366f1; color: white; border: none; padding: 8px 16px; border-radius: 20px; cursor: pointer; }
.chat-footer button:disabled { opacity: 0.6; }
</style>
