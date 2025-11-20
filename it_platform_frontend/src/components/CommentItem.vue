<template>
  <li class="comment-item">
    <div class="avatar-box">
      <img
        :src="`https://ui-avatars.com/api/?name=${comment.user?.username}&background=random&color=fff&size=128`"
        class="user-avatar"
        alt="User"
      >
    </div>

    <div class="comment-main">
      <div class="comment-header">
        <span class="username">{{ comment.user?.username || '未知用户' }}</span>
        <span class="time">{{ formatDate(comment.created_at) }}</span>
      </div>

      <div class="comment-body">
        <p>{{ comment.content || '' }}</p>
      </div>

      <div class="comment-actions">
        <button @click="toggleReplyForm(comment.user)" class="action-link">
          {{ showReplyForm ? '取消' : '回复' }}
        </button>
      </div>

      <div v-if="showReplyForm" class="reply-form-box">
        <textarea
          v-model="newReplyContent"
          :placeholder="`回复 @${replyToUser?.username}...`"
          rows="2"
        ></textarea>
        <div class="reply-btn-group">
          <button @click="handleReplySubmit" class="btn-submit" :disabled="!newReplyContent.trim() || isSubmitting">
            {{ isSubmitting ? '发送中...' : '发送' }}
          </button>
        </div>
      </div>

      <ul v-if="comment.replies && comment.replies.length > 0" class="sub-comment-list">
        <li v-for="reply in comment.replies" :key="reply.id" class="sub-comment-item">
          <div class="avatar-box small">
            <img
              :src="`https://ui-avatars.com/api/?name=${reply.user?.username}&background=random&color=fff&size=64`"
              class="user-avatar"
            >
          </div>
          <div class="sub-main">
            <div class="comment-header">
              <span class="username">{{ reply.user?.username }}</span>
              <span v-if="reply.reply_to_user" class="reply-tag">
                回复 <span class="at-user">@{{ reply.reply_to_user.username }}</span>
              </span>
              <span class="time">{{ formatDate(reply.created_at) }}</span>
            </div>
            <p class="sub-content">{{ reply.content }}</p>
            <div class="comment-actions">
              <button @click="toggleReplyForm(reply.user)" class="action-link">
                 {{ (showReplyForm && replyToUser?.id === reply.user.id) ? '取消' : '回复' }}
              </button>
            </div>
          </div>
        </li>
      </ul>
    </div>
  </li>
</template>

<script setup>
import { ref } from 'vue'
import apiClient from '@/api'
import { useAuthStore } from '@/stores/authStore'
import { useRouter } from 'vue-router'

const props = defineProps({
  comment: { type: Object, required: true }
})

const emit = defineEmits(['comment-posted'])
const authStore = useAuthStore()
const router = useRouter()

const showReplyForm = ref(false)
const newReplyContent = ref('')
const replyToUser = ref(null)
const isSubmitting = ref(false)

const toggleReplyForm = (targetUser) => {
  if (!authStore.isAuthenticated) { router.push({ name: 'login' }); return; }

  if (showReplyForm.value && replyToUser.value?.id === targetUser.id) {
    showReplyForm.value = false
    replyToUser.value = null
  } else {
    showReplyForm.value = true
    replyToUser.value = targetUser
    newReplyContent.value = ''
  }
}

const handleReplySubmit = async () => {
  if (!newReplyContent.value.trim() || !replyToUser.value) return;
  isSubmitting.value = true;
  try {
    await apiClient.post('/api/comments/', {
      lesson: props.comment.lesson,
      content: newReplyContent.value,
      parent: props.comment.id,
      reply_to_user_id: replyToUser.value.id
    });
    newReplyContent.value = '';
    showReplyForm.value = false;
    emit('comment-posted');
  } catch (error) {
    alert('回复失败');
  } finally {
    isSubmitting.value = false;
  }
}

const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  const now = new Date();
  const diff = (now - date) / 1000;

  if (diff < 60) return '刚刚';
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`;
  return date.toISOString().split('T')[0];
}
</script>

<style scoped>
.comment-item {
  display: flex;
  gap: 15px;
  padding: 20px 0;
  border-bottom: 1px solid #f3f4f6;
}
.avatar-box { flex-shrink: 0; }
.user-avatar { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; }
.avatar-box.small .user-avatar { width: 30px; height: 30px; }

.comment-main { flex-grow: 1; }
.comment-header { margin-bottom: 6px; font-size: 0.9rem; }
.username { font-weight: 600; color: #333; margin-right: 10px; }
.time { font-size: 0.8rem; color: #999; }

.comment-body { color: #4b5563; line-height: 1.6; font-size: 0.95rem; }

.comment-actions { margin-top: 8px; }
.action-link {
  background: none; border: none; color: #6b7280; font-size: 0.85rem; cursor: pointer; padding: 0; font-weight: 500;
}
.action-link:hover { color: #4f46e5; text-decoration: underline; }

.reply-form-box { margin-top: 10px; background: #f9fafb; padding: 10px; border-radius: 8px; }
.reply-form-box textarea {
  width: 100%; border: 1px solid #e5e7eb; border-radius: 6px; padding: 8px; font-size: 0.9rem; resize: vertical;
}
.reply-btn-group { text-align: right; margin-top: 8px; }
.btn-submit {
  background: #4f46e5; color: white; border: none; padding: 6px 16px; border-radius: 4px; cursor: pointer; font-size: 0.85rem;
}

/* 子评论 */
.sub-comment-list { list-style: none; padding: 0; margin-top: 15px; }
.sub-comment-item { display: flex; gap: 10px; padding-top: 10px; }
.reply-tag { font-size: 0.85rem; color: #666; margin: 0 5px; }
.at-user { color: #4f46e5; font-weight: 500; }
.sub-content { font-size: 0.9rem; color: #555; }
</style>
