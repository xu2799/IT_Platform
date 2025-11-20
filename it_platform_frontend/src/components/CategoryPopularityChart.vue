<template>
  <div class="chart-container">
    <Pie v-if="loaded && chartData" :data="chartData" :options="chartOptions" />
    <p v-if="!loaded && !error" class="chart-loading">正在加载热度图表...</p>
    <p v-if="error" class="chart-error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
// 【【【修改】】】: 导入 Pie
import { Pie } from 'vue-chartjs'
// 【【【修改】】】: 导入 ArcElement, 移除 BarElement, LinearScale
import { Chart as ChartJS, Title, Tooltip, Legend, ArcElement, CategoryScale } from 'chart.js'
// 【【【新增】】】: 导入数据标签插件 (使用正确的包名)
import ChartDataLabels from 'chartjs-plugin-datalabels';
// 【【【新增，修复错误】】】: 导入 apiClient
import apiClient from '@/api'


// 【【【修改】】】: 注册 ArcElement 和 DataLabels 插件
ChartJS.register(Title, Tooltip, Legend, ArcElement, CategoryScale, ChartDataLabels)

const loaded = ref(false)
const error = ref(null)
const chartData = ref(null)
const totalAllLikes = ref(0) // 【【【新增】】】: 用于存储总点赞数
let updateInterval = null

// 【【【修改】】】: 扇形图的 Chart Options
const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    // 【【【修改】】】: 禁用默认图例，因为标签在图表内
    legend: {
      display: false,
    },
    title: {
      display: true,
      // 【【【修改】】】: 标题 (已移除 "按点赞数")
      text: '课程分类点赞占比',
      font: {
        size: 18,
        weight: 'bold',
      },
      padding: {
        bottom: 10
      }
    },
    // 【【【新增】】】: 副标题，用于显示总点赞数
    subtitle: {
        display: true,
        text: `本站所有课程总点赞数: ${totalAllLikes.value}`,
        font: {
            size: 14,
        },
        padding: {
            bottom: 20
        }
    },
    tooltip: {
      callbacks: {
        // 自定义提示框，显示百分比和原始票数
        label: function(context) {
          const label = context.label || '';
          const value = context.raw || 0;
          
          let percentage = '0%';
          if (totalAllLikes.value > 0) {
            percentage = (value / totalAllLikes.value * 100).toFixed(1) + '%';
          }
          
          return `${label}: ${percentage} (${value} 票)`;
        }
      }
    },
    // 【【【新增】】】: 配置数据标签 (显示在扇形图上)
    datalabels: {
        color: '#fff', // 标签颜色
        font: {
            weight: 'bold',
            size: 12,
        },
        backgroundColor: (context) => {
            // 给标签一个半透明的背景
            return 'rgba(0, 0, 0, 0.5)';
        },
        borderRadius: 4,
        padding: 6,
        formatter: (value, context) => {
            // 格式化标签内容
            const label = context.chart.data.labels[context.dataIndex];
            let percentage = '0%';
            if (totalAllLikes.value > 0) {
                 percentage = (value / totalAllLikes.value * 100).toFixed(1) + '%';
            }
            // 返回 "分类名\n百分比"
            return `${label}\n${percentage}`;
        }
    }
  }
}))

// 从后端获取数据的函数
const fetchData = async () => {
  try {
    // 调用 Category API (它现在包含了 'total_likes' 统计数据)
    const response = await apiClient.get('/api/categories/')
    
    const categories = (response.data.results || response.data)
    
    // 【【【新增】】】: 计算总点赞数 (使用所有分类)
    totalAllLikes.value = categories.reduce((sum, c) => sum + c.total_likes, 0);

    // 【【【修改】】】: 按 total_likes 过滤
    const filteredCategories = categories
      .filter(c => c.total_likes > 0)
      .slice(0, 6); // (最多显示6个分类)

    if (filteredCategories.length === 0) {
      // 【【【修改】】】: 更改错误消息
      error.value = "暂无课程点赞数据"
      loaded.value = true
      chartData.value = null // 清空旧数据
      return
    }

    // 格式化数据以适应 Chart.js
    chartData.value = {
      labels: filteredCategories.map(c => c.name),
      datasets: [
        {
          label: '总点赞数',
          backgroundColor: [
            '#3498db', '#2ecc71', '#f0ad4e', '#e74c3c', '#9b59b6', '#34495e'
          ],
          // 【【【修改】】】: 数据仍然是原始点赞数
          data: filteredCategories.map(c => c.total_likes),
        }
      ]
    }
    loaded.value = true
    error.value = null
  } catch (err) {
    console.error('加载图表数据失败:', err)
    error.value = '无法加载图表数据。'
    loaded.value = false
  }
}

// 组件挂载时
onMounted(() => {
  fetchData() // 1. 立即加载一次

  // 2. 设置定时器，实现“自动更新”
  updateInterval = setInterval(() => {
    console.log('正在自动更新图表数据...')
    fetchData()
  }, 60000) // 每 60 秒 (60000 毫秒) 更新一次
})

// 组件卸载时清除定时器，防止内存泄漏
onUnmounted(() => {
  if (updateInterval) {
    clearInterval(updateInterval)
  }
})
</script>

<style scoped>
.chart-container {
  position: relative;
  width: 100%;
  max-width: 900px;
  /* 【【【修改】】】: 增加高度以容纳扇形图和图例 */
  height: 500px; 
  margin: 40px auto;
  padding: 20px;
  border: 1px solid #eee;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  background-color: #fff;
}
.chart-loading,
.chart-error {
  text-align: center;
  font-size: 1.2rem;
  color: #777;
  margin-top: 150px;
}
.chart-error {
  color: #dc3545;
}
</style>