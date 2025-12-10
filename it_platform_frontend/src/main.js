import './assets/base.css'
import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
// 【还原】引入粒子库
import Particles from "@tsparticles/vue3";
import { loadSlim } from "@tsparticles/slim";

async function initializeApp() {

  const app = createApp(App)

  app.use(createPinia())

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

  // 【还原】初始化粒子插件
  app.use(Particles, {
    init: async (engine) => {
      await loadSlim(engine);
    },
  });

  app.use(router)

  app.mount('#app')
}

initializeApp()
