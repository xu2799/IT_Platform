<script setup>
const particlesOptions = {
  background: {
    color: {
      value: "transparent", // 透明背景，透出底层的白色或灰色
    },
  },
  fpsLimit: 120,
  interactivity: {
    events: {
      // 【核心交互】鼠标悬停时，主动“抓取”附近的粒子形成连线
      onHover: {
        enable: true,
        mode: "grab",
      },
      // 点击时，产生推力并增加少量粒子，增加趣味性
      onClick: {
        enable: true,
        mode: "push",
      },
      resize: true,
    },
    modes: {
      // 抓取连线的参数配置
      grab: {
        distance: 180, // 感应距离
        links: {
          opacity: 0.8, // 鼠标连线高亮，比普通连线更明显
          color: "#3498db" 
        },
      },
      push: {
        quantity: 4,
      },
    },
  },
  particles: {
    // 粒子颜色：使用您的品牌蓝
    color: {
      value: "#3498db",
    },
    // 【优雅感来源 1】纤细且半透明的背景连线
    links: {
      color: "#3498db",
      distance: 150,
      enable: true,
      opacity: 0.2, // 平时非常淡，不抢眼
      width: 1,
    },
    // 【优雅感来源 2】缓慢的移动速度
    move: {
      direction: "none",
      enable: true,
      outModes: {
        default: "bounce", // 碰到屏幕边缘反弹
      },
      random: false,
      speed: 1, // 速度设为 1，营造缓慢漂浮的氛围
      straight: false,
    },
    // 粒子数量适中，保持画面干净，不密集
    number: {
      density: {
        enable: true,
        area: 800,
      },
      value: 80,
    },
    // 粒子半透明
    opacity: {
      value: 0.6,
    },
    shape: {
      type: "circle",
    },
    // 粒子较小，显得精致
    size: {
      value: { min: 1, max: 3 },
    },
  },
  detectRetina: true, // 开启高清屏适配，粒子边缘更锐利
};
</script>

<template>
  <div class="particles-wrapper">
    <vue-particles
      id="tsparticles"
      :options="particlesOptions"
    />
  </div>
</template>

<style scoped>
.particles-wrapper {
  position: fixed; /* 固定定位，覆盖全屏 */
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0; /* 层级为 0，置于内容底部 */
  pointer-events: auto; /* 允许鼠标交互 */
}
</style>