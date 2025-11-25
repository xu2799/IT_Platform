<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import apiClient from '@/api'
import BackButton from '@/components/BackButton.vue'
import { getFullMediaUrl } from '@/utils/common'

const authStore = useAuthStore()

// 页面状态
const activeTab = ref('profile')

// 个人信息状态
const nickname = ref('')
const bio = ref('')
const avatarFile = ref(null)
const previewAvatar = ref(null)

// 密码修改状态
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const profileMsg = ref({ type: '', text: '' })
const passwordMsg = ref({ type: '', text: '' })
const isUpdatingProfile = ref(false)
const isUpdatingPassword = ref(false)

onMounted(() => {
  if (authStore.user) {
    nickname.value = authStore.user.nickname || ''
    bio.value = authStore.user.bio || ''
  }
})

const handleAvatarChange = (event) => {
  const file = event.target.files[0]
  if (file) {
    avatarFile.value = file
    const reader = new FileReader()
    reader.onload = (e) => { previewAvatar.value = e.target.result }
    reader.readAsDataURL(file)
  }
}

const handleProfileUpdate = async () => {
  profileMsg.value = { type: '', text: '' }
  isUpdatingProfile.value = true

  const formData = new FormData()
  formData.append('nickname', nickname.value)
  formData.append('bio', bio.value)
  if (avatarFile.value) {
    formData.append('avatar', avatarFile.value)
  }

  try {
    const response = await apiClient.patch('/api/users/me/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    authStore.user = response.data
    localStorage.setItem('user', JSON.stringify(response.data))

    profileMsg.value = { type: 'success', text: '保存成功！' }

    // 【关键修改】保存成功后，清空本地预览，强制显示后端返回的图片
    // 这样可以确保用户看到的图片是服务器真正保存成功的那一张
    avatarFile.value = null
    previewAvatar.value = null

  } catch (error) {
    profileMsg.value = { type: 'error', text: '保存失败，请重试。' }
  } finally {
    isUpdatingProfile.value = false
  }
}

const handlePasswordUpdate = async () => {
  passwordMsg.value = { type: '', text: '' }

  // 前端先做一次简单校验
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    passwordMsg.value = { type: 'error', text: '两次输入的新密码不一致' }
    return
  }

  isUpdatingPassword.value = true
  try {
    await apiClient.post('/api/users/change-password/', passwordForm.value)
    passwordMsg.value = { type: 'success', text: '密码修改成功！' }
    passwordForm.value = { old_password: '', new_password: '', confirm_password: '' }
  } catch (error) {
    console.error("修改密码错误详情:", error.response?.data) // 方便调试
    const errData = error.response?.data

    // 【核心修复】全面解析后端返回的错误字段
    let msg = '修改失败，请检查输入'

    if (errData) {
        if (errData.old_password) {
            msg = `当前密码错误: ${errData.old_password[0]}`
        } else if (errData.new_password) {
            msg = `新密码不符合要求: ${errData.new_password[0]}`
        } else if (errData.confirm_password) {
            msg = `确认密码错误: ${errData.confirm_password[0]}`
        } else if (errData.detail) {
            msg = errData.detail
        } else if (typeof errData === 'string') {
            msg = errData
        }
    }

    passwordMsg.value = { type: 'error', text: msg }
  } finally {
    isUpdatingPassword.value = false
  }
}

const currentAvatar = computed(() => {
  if (previewAvatar.value) return previewAvatar.value
  if (authStore.user?.avatar) return getFullMediaUrl(authStore.user.avatar)
  return `https://ui-avatars.com/api/?name=${authStore.user?.username}&background=4f46e5&color=fff&size=128`
})
</script>

<template>
  <div class="profile-page">
    <BackButton :fallback-route="{ name: 'courses' }" text="返回课程" small />

    <div class="settings-container">

      <aside class="settings-sidebar">
        <div class="user-summary">
          <div class="avatar-preview">
            <img :src="currentAvatar" alt="Avatar">
          </div>
          <h3>{{ authStore.user?.nickname || authStore.user?.username }}</h3>
          <p>@{{ authStore.user?.username }}</p>
        </div>

        <nav class="menu-list">
          <button
            class="menu-item"
            :class="{ active: activeTab === 'profile' }"
            @click="activeTab = 'profile'"
          >
            <span class="icon">👤</span> 基本资料
          </button>
          <button
            class="menu-item"
            :class="{ active: activeTab === 'security' }"
            @click="activeTab = 'security'"
          >
            <span class="icon">🛡️</span> 安全设置
          </button>
        </nav>
      </aside>

      <main class="settings-content">

        <div v-if="activeTab === 'profile'" class="content-panel fade-in">
          <div class="panel-header">
            <h2>编辑个人资料</h2>
            <p>更新您的个人详细信息</p>
          </div>

          <form @submit.prevent="handleProfileUpdate">
            <div class="form-row avatar-row">
              <div class="avatar-col">
                <img :src="currentAvatar" class="avatar-lg">
              </div>
              <div class="action-col">
                <label class="btn-upload">
                  更换头像
                  <input type="file" accept="image/*" @change="handleAvatarChange" hidden>
                </label>
                <p class="tip">支持 JPG, PNG 格式</p>
              </div>
            </div>

            <div class="form-group">
              <label>昵称</label>
              <input type="text" v-model="nickname" placeholder="您的昵称">
            </div>

            <div class="form-group">
              <label>个人简介</label>
              <textarea v-model="bio" rows="4" placeholder="写一句话介绍自己..."></textarea>
            </div>

            <div v-if="profileMsg.text" :class="['message', profileMsg.type]">
              {{ profileMsg.text }}
            </div>

            <div class="form-footer">
              <button type="submit" class="btn-primary" :disabled="isUpdatingProfile">
                {{ isUpdatingProfile ? '保存中...' : '保存更改' }}
              </button>
            </div>
          </form>
        </div>

        <div v-if="activeTab === 'security'" class="content-panel fade-in">
          <div class="panel-header">
            <h2>安全设置</h2>
            <p>管理您的账号密码</p>
          </div>

          <form @submit.prevent="handlePasswordUpdate">
            <div class="form-group">
              <label>当前密码</label>
              <input type="password" v-model="passwordForm.old_password" required placeholder="请输入当前使用的密码">
            </div>
            <div class="form-group">
              <label>新密码</label>
              <input type="password" v-model="passwordForm.new_password" required placeholder="设置新密码 (建议包含字母和数字)">
            </div>
            <div class="form-group">
              <label>确认新密码</label>
              <input type="password" v-model="passwordForm.confirm_password" required placeholder="再次输入新密码">
            </div>

            <div v-if="passwordMsg.text" :class="['message', passwordMsg.type]">
              {{ passwordMsg.text }}
            </div>

            <div class="form-footer">
              <button type="submit" class="btn-primary" :disabled="isUpdatingPassword">
                {{ isUpdatingPassword ? '提交中...' : '修改密码' }}
              </button>
            </div>
          </form>
        </div>

      </main>
    </div>
  </div>
</template>

<style scoped>
.profile-page { max-width: 1100px; margin: 30px auto; padding: 0 20px; }

/* 容器布局：左侧固定宽度，右侧自适应 */
.settings-container {
  display: flex;
  gap: 30px;
  min-height: 500px;
  align-items: flex-start;
}

/* --- 左侧侧边栏 --- */
.settings-sidebar {
  width: 280px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  padding: 30px 20px;
  flex-shrink: 0;
  border: 1px solid #f3f4f6;
}

.user-summary { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #f3f4f6; }
.avatar-preview img { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 3px solid #e0e7ff; }
.user-summary h3 { margin: 10px 0 5px; font-size: 1.1rem; color: #1f2937; }
.user-summary p { color: #9ca3af; font-size: 0.9rem; }

.menu-list { display: flex; flex-direction: column; gap: 5px; }
.menu-item {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 15px; border: none; background: transparent;
  text-align: left; font-size: 0.95rem; color: #4b5563;
  border-radius: 8px; cursor: pointer; transition: all 0.2s;
  font-weight: 500;
}
.menu-item:hover { background: #f9fafb; color: #4f46e5; }
.menu-item.active { background: #e0e7ff; color: #4f46e5; font-weight: 600; }
.menu-item .icon { font-size: 1.1rem; }

/* --- 右侧内容区 --- */
.settings-content {
  flex: 1;
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  border: 1px solid #f3f4f6;
  padding: 40px;
  min-height: 500px;
}

.panel-header { margin-bottom: 30px; border-bottom: 1px solid #f3f4f6; padding-bottom: 15px; }
.panel-header h2 { font-size: 1.5rem; color: #111827; margin: 0 0 5px 0; }
.panel-header p { color: #6b7280; font-size: 0.9rem; }

/* 表单通用样式 */
.form-group { margin-bottom: 24px; }
.form-group label { display: block; font-size: 0.9rem; font-weight: 600; color: #374151; margin-bottom: 8px; }
.form-group input, .form-group textarea {
  width: 100%; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 8px;
  font-size: 0.95rem; transition: border-color 0.2s;
}
.form-group input:focus, .form-group textarea:focus { border-color: #4f46e5; outline: none; box-shadow: 0 0 0 3px rgba(79,70,229,0.1); }

/* 头像上传行 */
.avatar-row { display: flex; align-items: center; gap: 20px; margin-bottom: 30px; }
.avatar-lg { width: 70px; height: 70px; border-radius: 50%; object-fit: cover; }
.btn-upload {
  display: inline-block; padding: 8px 16px; border: 1px solid #d1d5db; border-radius: 6px;
  font-size: 0.9rem; color: #374151; cursor: pointer; transition: all 0.2s;
  background: white; font-weight: 500;
}
.btn-upload:hover { background: #f9fafb; border-color: #9ca3af; }
.tip { font-size: 0.8rem; color: #9ca3af; margin-top: 5px; }

.form-footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #f3f4f6; text-align: right; }
.btn-primary {
  background: #4f46e5; color: white; border: none; padding: 10px 24px; border-radius: 8px;
  font-weight: 600; cursor: pointer; font-size: 0.95rem; transition: background 0.2s;
}
.btn-primary:hover { background: #4338ca; }
.btn-primary:disabled { opacity: 0.7; cursor: not-allowed; }

.message { padding: 10px; border-radius: 6px; margin-bottom: 20px; font-size: 0.9rem; text-align: center; }
.message.success { background: #ecfdf5; color: #065f46; }
.message.error { background: #fef2f2; color: #991b1b; }

.fade-in { animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }

@media (max-width: 768px) {
  .settings-container { flex-direction: column; }
  .settings-sidebar { width: 100%; }
}
</style>
