<script setup>
import { ref, onMounted, nextTick } from 'vue'
import apiClient from '@/api'
import { useAuthStore } from '@/stores/authStore'
import { getFullMediaUrl } from '@/utils/common'
import BackButton from '@/components/BackButton.vue'

const authStore = useAuthStore()
const friends = ref([])
const activeContact = ref(null)
const messages = ref([])
const messageInput = ref('')
const chatBodyRef = ref(null)

// 搜索与添加好友
const searchQuery = ref('')
const searchResults = ref([])
const showSearchDropdown = ref(false)

// 新朋友申请
const pendingRequests = ref([])
const showRequestsModal = ref(false)

// 1. 获取数据
const initData = async () => {
  await fetchFriends()
  await fetchPendingRequests()
}

const fetchFriends = async () => {
  try {
    const res = await apiClient.get('/api/friendships/friends/')
    friends.value = res.data
  } catch (e) { console.error(e) }
}

const fetchPendingRequests = async () => {
  try {
    const res = await apiClient.get('/api/friendships/pending_requests/')
    pendingRequests.value = res.data
  } catch (e) { console.error(e) }
}

// 2. 选择好友开始聊天
const selectContact = async (contact) => {
  activeContact.value = contact
  messages.value = []
  try {
    const res = await apiClient.get('/api/messages/history/', {
      params: { target_id: contact.id }
    })
    messages.value = res.data
    scrollToBottom()
  } catch (e) { console.error(e) }
}

// 3. 发送消息
const sendMessage = async () => {
  if (!messageInput.value.trim() || !activeContact.value) return
  const content = messageInput.value
  messageInput.value = ''

  try {
    const res = await apiClient.post('/api/messages/', {
      receiver_username: activeContact.value.username,
      content: content
    })
    messages.value.push(res.data)
    scrollToBottom()
  } catch (e) {
    alert('发送失败: ' + (e.response?.data?.detail || '可能不是好友'))
  }
}

// 4. 搜索用户
const handleSearch = async () => {
    if (!searchQuery.value.trim()) return
    try {
        const res = await apiClient.get('/api/users/search/', { params: { q: searchQuery.value } })
        searchResults.value = res.data
        showSearchDropdown.value = true
    } catch(e) {}
}

// 5. 发送好友申请
const sendFriendRequest = async (user) => {
    try {
        await apiClient.post('/api/friendships/', { to_username: user.username })
        alert('申请已发送')
        handleSearch() // 刷新状态
    } catch(e) {
        alert(e.response?.data?.to_username || '发送失败')
    }
}

// 6. 处理好友申请
const handleRequestAction = async (reqId, action) => {
    try {
        await apiClient.post(`/api/friendships/${reqId}/${action}/`)
        fetchPendingRequests()
        if (action === 'accept') fetchFriends()
    } catch(e) { alert('操作失败') }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatBodyRef.value) chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
  })
}

const getAvatar = (user) => {
    if (user?.avatar) return getFullMediaUrl(user.avatar)
    return `https://ui-avatars.com/api/?name=${user?.username || 'U'}&background=random`
}

onMounted(initData)
</script>

<template>
  <div class="chat-page">
    <BackButton :fallback-route="{ name: 'courses' }" text="返回" small class="back-btn-float" />

    <div class="chat-layout">
      <aside class="sidebar">
        <div class="search-bar">
            <input v-model="searchQuery" @keyup.enter="handleSearch" placeholder="🔍 搜索用户ID/昵称" />
            <div v-if="showSearchDropdown" class="search-results" @mouseleave="showSearchDropdown = false">
                <div v-if="searchResults.length === 0" class="no-result">无结果</div>
                <div v-for="u in searchResults" :key="u.id" class="search-item">
                    <img :src="getAvatar(u)" class="avatar-xs">
                    <div class="info">
                        <div class="name">{{ u.nickname || u.username }}</div>
                        <div class="status-text">
                            {{ u.friendship_status === 'friend' ? '已是好友' : (u.friendship_status === 'sent' ? '已申请' : '') }}
                        </div>
                    </div>
                    <button v-if="u.friendship_status === 'none'" @click="sendFriendRequest(u)" class="btn-add">添加</button>
                    <button v-if="u.friendship_status === 'friend'" @click="selectContact(u); showSearchDropdown=false" class="btn-chat">发消息</button>
                </div>
            </div>
        </div>

        <div class="new-friends-entry" @click="showRequestsModal = true">
            <div class="icon-box">👤</div>
            <span>新的朋友</span>
            <span v-if="pendingRequests.length > 0" class="badge">{{ pendingRequests.length }}</span>
        </div>

        <div class="friends-list">
            <div class="list-header">我的好友 ({{ friends.length }})</div>
            <div
                v-for="friend in friends"
                :key="friend.id"
                class="friend-item"
                :class="{ active: activeContact?.id === friend.id }"
                @click="selectContact(friend)"
            >
                <img :src="getAvatar(friend)" class="avatar-sm">
                <span class="name">{{ friend.nickname || friend.username }}</span>
            </div>
        </div>
      </aside>

      <main class="chat-area">
        <div v-if="activeContact" class="chat-window">
            <header class="header">
                <span class="title">{{ activeContact.nickname || activeContact.username }}</span>
            </header>
            <div class="messages" ref="chatBodyRef">
                <div v-for="msg in messages" :key="msg.id" class="msg-row" :class="{ mine: msg.sender.id === authStore.user.id }">
                    <div class="bubble">{{ msg.content }}</div>
                </div>
                <div v-if="messages.length === 0" class="empty-chat">开始聊天吧</div>
            </div>
            <div class="input-area">
                <input v-model="messageInput" @keyup.enter="sendMessage" placeholder="输入消息..." />
                <button @click="sendMessage">发送</button>
            </div>
        </div>
        <div v-else class="empty-state">
            <p>请选择一位好友开始聊天</p>
        </div>
      </main>
    </div>

    <div v-if="showRequestsModal" class="modal-overlay" @click.self="showRequestsModal = false">
        <div class="modal">
            <h3>好友申请</h3>
            <div v-if="pendingRequests.length === 0" class="no-req">暂无新申请</div>
            <div v-for="req in pendingRequests" :key="req.id" class="req-item">
                <img :src="getAvatar(req.from_user)" class="avatar-sm">
                <span class="name">{{ req.from_user.username }}</span>
                <div class="actions">
                    <button @click="handleRequestAction(req.id, 'accept')" class="btn-accept">接受</button>
                    <button @click="handleRequestAction(req.id, 'reject')" class="btn-reject">拒绝</button>
                </div>
            </div>
            <button class="btn-close" @click="showRequestsModal = false">关闭</button>
        </div>
    </div>
  </div>
</template>

<style scoped>
.chat-page { height: calc(100vh - 70px); padding: 20px; background: #f2f2f2; display: flex; flex-direction: column; }
.back-btn-float { width: fit-content; margin-bottom: 10px; }
.chat-layout { flex: 1; display: flex; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }

/* Sidebar */
.sidebar { width: 280px; border-right: 1px solid #eee; display: flex; flex-direction: column; background: #fafafa; }
.search-bar { padding: 15px; position: relative; border-bottom: 1px solid #eee; }
.search-bar input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
.search-results { position: absolute; top: 50px; left: 10px; right: 10px; background: white; box-shadow: 0 4px 10px rgba(0,0,0,0.1); z-index: 10; border-radius: 4px; padding: 5px; }
.search-item { display: flex; align-items: center; padding: 8px; border-bottom: 1px solid #f5f5f5; }
.search-item .info { flex: 1; margin-left: 8px; }
.search-item .status-text { font-size: 0.75rem; color: #999; }
.btn-add, .btn-chat { padding: 4px 8px; font-size: 0.8rem; cursor: pointer; border: none; border-radius: 4px; }
.btn-add { background: #4f46e5; color: white; }
.btn-chat { background: #10b981; color: white; }

.new-friends-entry { display: flex; align-items: center; padding: 15px; cursor: pointer; border-bottom: 1px solid #eee; transition: background 0.2s; }
.new-friends-entry:hover { background: #f0f0f0; }
.icon-box { width: 36px; height: 36px; background: #faad14; color: white; border-radius: 4px; display: flex; align-items: center; justify-content: center; margin-right: 10px; }
.badge { background: #ef4444; color: white; font-size: 0.75rem; padding: 2px 6px; border-radius: 10px; margin-left: auto; }

.friends-list { flex: 1; overflow-y: auto; }
.list-header { padding: 10px 15px; font-size: 0.85rem; color: #999; }
.friend-item { display: flex; align-items: center; padding: 10px 15px; cursor: pointer; transition: background 0.2s; }
.friend-item:hover { background: #f0f0f0; }
.friend-item.active { background: #e6f7ff; }
.friend-item .name { margin-left: 10px; font-weight: 500; }

/* Chat Area */
.chat-area { flex: 1; display: flex; flex-direction: column; background: #f5f5f5; }
.chat-window { display: flex; flex-direction: column; height: 100%; }
.header { padding: 15px 20px; background: white; border-bottom: 1px solid #eee; font-weight: bold; font-size: 1.1rem; }
.messages { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
.msg-row { display: flex; }
.msg-row.mine { justify-content: flex-end; }
.bubble { padding: 8px 12px; background: white; border-radius: 8px; max-width: 70%; font-size: 0.95rem; }
.mine .bubble { background: #95ec69; }
.input-area { padding: 15px; background: white; border-top: 1px solid #eee; display: flex; gap: 10px; }
.input-area input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
.input-area button { padding: 0 20px; background: #4f46e5; color: white; border: none; border-radius: 4px; cursor: pointer; }
.empty-state, .empty-chat { display: flex; align-items: center; justify-content: center; height: 100%; color: #ccc; }

/* Modal */
.modal-overlay { position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal { background: white; width: 400px; padding: 20px; border-radius: 8px; max-height: 80vh; overflow-y: auto; }
.req-item { display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid #eee; }
.req-item .name { flex: 1; margin-left: 10px; font-weight: bold; }
.btn-accept { background: #10b981; color: white; border: none; padding: 4px 10px; border-radius: 4px; cursor: pointer; margin-right: 5px; }
.btn-reject { background: #ef4444; color: white; border: none; padding: 4px 10px; border-radius: 4px; cursor: pointer; }
.btn-close { margin-top: 15px; width: 100%; padding: 8px; background: #eee; border: none; cursor: pointer; }

.avatar-sm { width: 36px; height: 36px; border-radius: 4px; object-fit: cover; }
.avatar-xs { width: 30px; height: 30px; border-radius: 4px; object-fit: cover; }
</style>
