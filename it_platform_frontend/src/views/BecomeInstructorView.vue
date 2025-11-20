<script setup>
import { ref } from 'vue'
// 【【【修改】】】: 导入 apiClient
import apiClient from '@/api'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import BackButton from '@/components/BackButton.vue'

// (API_URL 已移至 apiClient)
const router = useRouter()
const authStore = useAuthStore()

const justification = ref('')
const errorMessage = ref('')
const successMessage = ref('')

const handleSubmitApplication = async () => {
    errorMessage.value = ''
    successMessage.value = ''
    
    try {
        // 【【【修改】】】: 使用 apiClient
        const response = await apiClient.post('/api/applications/', {
            justification: justification.value
        })
        
        successMessage.value = '申请提交成功！管理员将会审核您的请求。'
        
        setTimeout(() => {
            router.push({ name: 'courses' })
        }, 2000)

    } catch (error) {
        console.error('申请失败:', error.response?.data || error.message)
        
        // --- 【【【重点修改：增强错误处理】】】 ---
        const data = error.response?.data;
        if (data?.detail) {
            errorMessage.value = data.detail;
        } else if (data?.non_field_errors && Array.isArray(data.non_field_errors)) {
            // 捕获来自 serializer.validate() 的错误 (例如 "你已经提交过申请...")
            errorMessage.value = data.non_field_errors.join(' ');
        } else if (data?.justification && Array.isArray(data.justification)) {
            // 捕获 justification 字段本身的错误 (例如太短)
            errorMessage.value = data.justification.join(' ');
        } else if (Array.isArray(data) && data.length > 0) {
            // 捕获其他 DRF 验证错误
            errorMessage.value = data[0];
        } else {
            errorMessage.value = '提交失败，请稍后再试。';
        }
        // --- 【【【修改结束】】】 ---
    }
}
</script>

<template>
  <div class="application-page">
    <BackButton 
      :fallback-route="{ name: 'courses' }" 
      text="返回课程列表"
      small
    />
    <h1>申请成为讲师</h1>
    <p class="subtitle">
        分享你的知识，创建自己的课程。请告诉我们你为什么适合成为一名讲师。
    </p>

    <div v-if="successMessage" class="message success">{{ successMessage }}</div>
    <div v-if="errorMessage" class="message error">{{ errorMessage }}</div>

    <form @submit.prevent="handleSubmitApplication" class="application-form" v-if="!successMessage">
      <div class="form-group">
        <label for="justification">申请理由:</label>
        <p class="small-text">
            请详细描述你的专业背景、教学经验以及你希望创建的课程类型。
        </p>
        <textarea 
            id="justification" 
            v-model="justification" 
            rows="10"
            required
        ></textarea>
      </div>
      <button type="submit" class="submit-button">提交申请</button>
    </form>
  </div>
</template>

<style scoped>
/* 样式部分 (完全不变) */
.application-page { 
  max-width: 700px; 
  margin: 20px auto; 
  padding: 20px; 
}
.application-page h1 {
  margin-top: 0;
}
.subtitle { font-size: 1.1rem; color: #555; }
.application-form { display: flex; flex-direction: column; gap: 15px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; margin-top: 20px;}
.form-group label { display: block; margin-bottom: 5px; font-weight: bold; font-size: 1.2rem; }
.form-group .small-text { font-size: 0.9rem; color: #777; margin-top: 0; }
.form-group textarea { width: 100%; padding: 10px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; font-size: 1rem; font-family: inherit; }
.submit-button { padding: 12px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 1.1rem; }
.submit-button:hover { background-color: #0056b3; }
.message { padding: 15px; border-radius: 4px; margin-bottom: 15px; font-size: 1.1rem; text-align: center; }
.success { background-color: #d4edda; color: #155724; border-color: #c3e6cb; }
.error { background-color: #f8d7da; color: #721c24; border-color: #f5c6cb; }
</style>