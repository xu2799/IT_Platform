import './assets/base.css' // <--- 【关键】必须在 main.css 之前引入！
import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import Particles from "@tsparticles/vue3";
import { loadSlim } from "@tsparticles/slim";

async function initializeApp() {
  
  const app = createApp(App)

  // 1. 安装 Pinia
  app.use(createPinia())

  // 2. 预加载用户信息
  const { useAuthStore } = await import('@/stores/authStore')
  const authStore = useAuthStore()
  const token = localStorage.getItem('token')

  if (token) {
    try {
      await authStore.fetchUser()
    } catch (error) {
      authStore.logout()
    }
  }

  // 3. 初始化粒子插件
  app.use(Particles, {
    init: async (engine) => {
      await loadSlim(engine);
    },
  });

  // 4. 安装路由
  app.use(router)

  app.mount('#app')
}

initializeApp()