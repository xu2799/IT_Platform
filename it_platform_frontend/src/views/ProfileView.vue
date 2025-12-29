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

// 积分与勋章状态
const pointsData = ref({
  total_points: 0,
  level: 1,
  continuous_days: 0,
  badges: []
})
const pointRecords = ref([])

onMounted(async () => {
  if (authStore.user) {
    nickname.value = authStore.user.nickname || ''
    bio.value = authStore.user.bio || ''
  }
  fetchPointsData()
})

const fetchPointsData = async () => {
  try {
    const [pointsRes, recordsRes] = await Promise.all([
      apiClient.get('/api/points/my_points/'),
      apiClient.get('/api/points/records/')
    ])
    pointsData.value = pointsRes.data
    pointRecords.value = recordsRes.data.slice(0, 10)
  } catch (e) { console.log('Points not available') }
}

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
            :class="{ active: activeTab === 'points' }"
            @click="activeTab = 'points'"
          >
            <span class="icon">🏆</span> 积分与勋章
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

        <!-- 积分与勋章 -->
        <div v-if="activeTab === 'points'" class="content-panel fade-in">
          <div class="panel-header">
            <h2>积分与勋章</h2>
            <p>查看您的学习成就</p>
          </div>

          <div class="points-overview">
            <div class="points-card">
              <div class="points-value">{{ pointsData.total_points }}</div>
              <div class="points-label">总积分</div>
            </div>
            <div class="points-card level">
              <div class="points-value">Lv.{{ pointsData.level }}</div>
              <div class="points-label">当前等级</div>
            </div>
            <div class="points-card streak">
              <div class="points-value">{{ pointsData.continuous_days }}</div>
              <div class="points-label">连续学习天数</div>
            </div>
          </div>

          <div class="badges-section">
            <h3>🏅 我的勋章</h3>
            <div v-if="pointsData.badges.length > 0" class="badges-grid">
              <div v-for="ub in pointsData.badges" :key="ub.id" class="badge-item">
                <span class="badge-icon">{{ ub.badge.icon }}</span>
                <span class="badge-name">{{ ub.badge.name }}</span>
              </div>
            </div>
            <div v-else class="empty-badges">
              <p>🌟 还没有勋章，继续学习解锁吧！</p>
            </div>
          </div>

          <div class="records-section">
            <h3>📝 最近积分记录</h3>
            <div v-if="pointRecords.length > 0" class="records-list">
              <div v-for="rec in pointRecords" :key="rec.id" class="record-item">
                <span class="record-action">{{ rec.action_display }}</span>
                <span class="record-points">+{{ rec.points }}分</span>
              </div>
            </div>
            <div v-else class="empty-records">
              <p>暂无积分记录</p>
            </div>
          </div>

          <!-- 积分规则 -->
          <div class="rules-section">
            <h3>📚 积分获取规则</h3>
            <div class="rules-grid">
              <div class="rule-item">
                <span class="rule-icon">🎬</span>
                <div class="rule-content">
                  <span class="rule-name">观看视频</span>
                  <span class="rule-points">+5 积分</span>
                </div>
              </div>
              <div class="rule-item">
                <span class="rule-icon">💬</span>
                <div class="rule-content">
                  <span class="rule-name">发表评论</span>
                  <span class="rule-points">+3 积分</span>
                </div>
              </div>
              <div class="rule-item">
                <span class="rule-icon">📝</span>
                <div class="rule-content">
                  <span class="rule-name">提交作业</span>
                  <span class="rule-points">+10 积分</span>
                </div>
              </div>
              <div class="rule-item">
                <span class="rule-icon">📅</span>
                <div class="rule-content">
                  <span class="rule-name">每日登录</span>
                  <span class="rule-points">+2 积分</span>
                </div>
              </div>
            </div>
            <div class="level-info">
              <p>💡 <strong>等级规则：</strong>每累计 100 积分升 1 级，连续学习可解锁特殊勋章！</p>
            </div>
          </div>
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

/* 积分与勋章样式 */
.points-overview {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.points-card {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  color: white;
  padding: 25px;
  border-radius: 12px;
  text-align: center;
}

.points-card.level {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.points-card.streak {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.points-value {
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 5px;
}

.points-label {
  font-size: 0.9rem;
  opacity: 0.9;
}

.badges-section, .records-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #f3f4f6;
}

.badges-section h3, .records-section h3 {
  font-size: 1.1rem;
  margin-bottom: 15px;
  color: #374151;
}

.badges-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.badge-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f8fafc;
  padding: 10px 15px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.badge-icon {
  font-size: 1.5rem;
}

.badge-name {
  font-weight: 600;
  color: #374151;
}

.empty-badges, .empty-records {
  color: #9ca3af;
  text-align: center;
  padding: 20px;
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.record-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 15px;
  background: #f9fafb;
  border-radius: 8px;
}

.record-action {
  color: #4b5563;
}

.record-points {
  color: #10b981;
  font-weight: 600;
}

/* 积分规则样式 */
.rules-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #f3f4f6;
}

.rules-section h3 {
  font-size: 1.1rem;
  margin-bottom: 15px;
  color: #374151;
}

.rules-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.rule-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 15px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  transition: transform 0.2s, box-shadow 0.2s;
}

.rule-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.rule-icon {
  font-size: 1.5rem;
}

.rule-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.rule-name {
  font-weight: 600;
  color: #374151;
  font-size: 0.95rem;
}

.rule-points {
  color: #10b981;
  font-weight: 700;
  font-size: 0.9rem;
}

.level-info {
  margin-top: 20px;
  padding: 15px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-radius: 8px;
  border: 1px solid #fcd34d;
}

.level-info p {
  margin: 0;
  color: #92400e;
  font-size: 0.9rem;
}

@media (max-width: 600px) {
  .rules-grid { grid-template-columns: 1fr; }
}
</style>
