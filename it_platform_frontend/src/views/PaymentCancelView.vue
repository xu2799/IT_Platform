<script setup>
import { useRouter } from 'vue-router';
import BackButton from '@/components/BackButton.vue'

const router = useRouter();
</script>

<template>
  <div class="payment-result cancel">
    <BackButton 
      :fallback-route="{ name: 'courses' }" 
      text="返回课程列表"
      small
    />
    <h1>支付已取消或失败 😢</h1>
    <p>您的支付过程已终止。您可以随时返回重新尝试购买。</p>
  </div>
</template>

<style scoped>
.payment-result { max-width: 600px; margin: 50px auto; padding: 40px; text-align: center; border-radius: 8px; }
.cancel { background-color: #fff0f0; border: 1px solid #d9534f; }
h1 { color: #d9534f; }
.btn { padding: 10px 20px; margin-top: 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
</style>