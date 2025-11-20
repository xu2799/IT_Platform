<script setup>
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/authStore';
import BackButton from '@/components/BackButton.vue'

const router = useRouter();
const authStore = useAuthStore();

onMounted(() => {
  // 【【【建议 1 修复】】】
  // 支付成功, 立即从后端获取最新的用户信息
  // (此时 Webhook 已执行, authStore.user 将包含新的 'enrollments')
  console.log('支付成功: 正在获取更新后的用户信息...');
  authStore.fetchUser();
  
  // (你原有的注释...)
  // 真实项目中, 这里会调用后端 API 验证 session_id, 
  // 并在数据库中创建 Enrollment 记录。
  // (备注: 你的 Webhook 已经做了这件事, 所以这里 fetchUser() 即可)
});
</script>

<template>
  <div class="payment-result success">
    <BackButton 
      :fallback-route="{ name: 'courses' }" 
      text="返回课程列表"
      small
    />
    <h1>支付成功！🎉</h1>
    <p>感谢您购买本课程。您的学习之旅即将开始。</p>
    <p class="small-text">（注意：订单创建将在后端 Webhook 验证后完成）</p>
  </div>
</template>

<style scoped>
/* (Style 保持不变) */
.payment-result { max-width: 600px; margin: 50px auto; padding: 40px; text-align: center; border-radius: 8px; }
.success { background-color: #e6ffe6; border: 1px solid #5cb85c; }
h1 { color: #5cb85c; }
.small-text { margin-top: 20px; font-style: italic; color: #555; }
.btn { padding: 10px 20px; margin-top: 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
</style>