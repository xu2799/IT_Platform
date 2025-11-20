<script setup>
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router' 
import { useAuthStore } from '@/stores/authStore'
import ParticleBackground from '@/components/ParticleBackground.vue'

const authStore = useAuthStore()
const router = useRouter() 
const username = ref('')
const password = ref('')
const errorMessage = ref('') 
const isLoading = ref(false)

const handleSubmit = async () => {
  errorMessage.value = ''
  isLoading.value = true
  try {
    const result = await authStore.login(username.value, password.value)
    if (result.success) { router.push({ name: 'courses' }) } 
    else { errorMessage.value = result.error }
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="auth-wrapper">
    <ParticleBackground />
    
    <div class="auth-card">
      <div class="brand-section">
        <h2>欢迎回来</h2>
        <p>登录 IT Platform，继续你的学习之旅</p>
      </div>

      <form @submit.prevent="handleSubmit" class="auth-form">
        <div class="input-group">
          <label>用户名</label>
          <input type="text" v-model="username" placeholder="请输入用户名" required>
        </div>
        <div class="input-group">
          <label>密码</label>
          <input type="password" v-model="password" placeholder="请输入密码" required>
        </div>
        
        <div v-if="errorMessage" class="error-box">{{ errorMessage }}</div>

        <button type="submit" class="btn-submit" :disabled="isLoading">
          {{ isLoading ? '登录中...' : '立即登录' }}
        </button>
      </form>

      <div class="auth-footer">
        <p>还没有账号？ <RouterLink :to="{ name: 'register' }" class="link">免费注册</RouterLink></p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-wrapper {
  min-height: calc(100vh - 70px);
  display: flex; justify-content: center; align-items: center;
  padding: 20px; position: relative;
}
.auth-card {
  width: 100%; max-width: 420px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 40px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.1);
  z-index: 1;
  border: 1px solid rgba(255,255,255,0.5);
}
.brand-section { text-align: center; margin-bottom: 30px; }
.brand-section h2 { font-size: 1.8rem; font-weight: 800; color: var(--color-text-main); }
.brand-section p { color: var(--color-text-muted); margin-top: 5px; }

.input-group { margin-bottom: 20px; }
.input-group label { display: block; font-size: 0.9rem; font-weight: 600; margin-bottom: 8px; color: var(--color-text-main); }
.input-group input {
  width: 100%; padding: 12px 16px;
  border: 1px solid #e5e7eb; border-radius: 10px;
  background: #f9fafb; transition: all 0.2s; font-size: 1rem;
}
.input-group input:focus {
  background: white; border-color: var(--color-primary);
  box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.1); outline: none;
}

.btn-submit {
  width: 100%; padding: 14px;
  background: var(--color-primary); color: white;
  border: none; border-radius: 12px;
  font-size: 1rem; font-weight: 600; cursor: pointer;
  transition: background 0.2s; margin-top: 10px;
}
.btn-submit:hover { background: var(--color-primary-hover); }
.btn-submit:disabled { opacity: 0.7; cursor: not-allowed; }

.error-box {
  background: #fef2f2; color: var(--color-danger);
  padding: 10px; border-radius: 8px; font-size: 0.9rem; text-align: center; margin-bottom: 15px;
}
.auth-footer { text-align: center; margin-top: 25px; font-size: 0.9rem; color: var(--color-text-muted); }
.link { color: var(--color-primary); font-weight: 600; }
</style>