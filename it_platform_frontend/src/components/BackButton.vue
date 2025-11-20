<template>
  <button 
    @click="handleBack" 
    class="back-button"
    :class="{ 'back-button-small': small, 'back-button-inline': inline }"
    :title="title"
  >
    <span class="back-icon">←</span>
    <span v-if="!iconOnly">{{ text }}</span>
  </button>
</template>

<script setup>
import { useRouter } from 'vue-router'

const props = defineProps({
  text: {
    type: String,
    default: '返回'
  },
  title: {
    type: String,
    default: '返回上一页'
  },
  fallbackRoute: {
    type: [String, Object],
    default: null
  },
  small: {
    type: Boolean,
    default: false
  },
  inline: {
    type: Boolean,
    default: false
  },
  iconOnly: {
    type: Boolean,
    default: false
  }
})

const router = useRouter()

const handleBack = () => {
  // 优先使用浏览器历史记录返回（如果历史记录存在且来源页面不是空）
  // 注意：在某些情况下，直接访问URL时可能没有历史记录
  try {
    if (window.history.length > 1) {
      router.go(-1)
      return
    }
  } catch (e) {
    console.warn('无法使用浏览器历史记录:', e)
  }
  
  // 如果有指定的回退路由，使用它
  if (props.fallbackRoute) {
    if (typeof props.fallbackRoute === 'string') {
      router.push(props.fallbackRoute)
    } else {
      router.push(props.fallbackRoute)
    }
  } else {
    // 默认返回课程列表
    router.push({ name: 'courses' })
  }
}
</script>

<style scoped>
.back-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.2s;
  margin-bottom: 20px;
}

.back-button:hover {
  background-color: #5a6268;
  transform: translateX(-2px);
}

.back-button:active {
  transform: translateX(0);
}

.back-button-small {
  padding: 6px 12px;
  font-size: 0.9rem;
  margin-bottom: 15px;
}

.back-button-inline {
  margin-bottom: 0;
  margin-right: 10px;
}

.back-icon {
  font-size: 1.2em;
  font-weight: bold;
  line-height: 1;
}

.back-button-small .back-icon {
  font-size: 1.1em;
}
</style>

