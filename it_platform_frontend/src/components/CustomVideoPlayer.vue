<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  src: { type: String, required: true },
  poster: { type: String, default: '' },
  autoplay: { type: Boolean, default: true }
})

const emit = defineEmits(['timeupdate', 'ended', 'play', 'pause'])

// Refs
const videoRef = ref(null)
const playerRef = ref(null)
const progressRef = ref(null)

// 状态
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(1)
const isMuted = ref(false)
const isFullscreen = ref(false)
const showControls = ref(true)
const playbackRate = ref(1)
const showRateMenu = ref(false)
const showVolumeSlider = ref(false)
const bufferedPercent = ref(0)
const hoverTime = ref(0)
const hoverTimeDisplay = ref('')
const showHoverTime = ref(false)
const hoverPosition = ref(0)

let controlsTimer = null
const rates = [0.5, 0.75, 1, 1.25, 1.5, 2]

// 计算属性
const progress = computed(() => (duration.value ? (currentTime.value / duration.value) * 100 : 0))

const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) {
    return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }
  return `${m}:${s.toString().padStart(2, '0')}`
}

const currentTimeFormatted = computed(() => formatTime(currentTime.value))
const durationFormatted = computed(() => formatTime(duration.value))

// 方法
const togglePlay = () => {
  if (!videoRef.value) return
  if (isPlaying.value) {
    videoRef.value.pause()
  } else {
    videoRef.value.play()
  }
}

const handleTimeUpdate = () => {
  if (!videoRef.value) return
  currentTime.value = videoRef.value.currentTime
  emit('timeupdate', { currentTime: currentTime.value })
}

const handleLoadedMetadata = () => {
  if (!videoRef.value) return
  duration.value = videoRef.value.duration
}

const handlePlay = () => {
  isPlaying.value = true
  emit('play')
}

const handlePause = () => {
  isPlaying.value = false
  emit('pause')
}

const handleEnded = () => {
  isPlaying.value = false
  emit('ended')
}

const handleProgress = () => {
  if (!videoRef.value) return
  const buffered = videoRef.value.buffered
  if (buffered.length > 0) {
    bufferedPercent.value = (buffered.end(buffered.length - 1) / duration.value) * 100
  }
}

const seek = (e) => {
  if (!progressRef.value || !videoRef.value) return
  const rect = progressRef.value.getBoundingClientRect()
  const percent = (e.clientX - rect.left) / rect.width
  videoRef.value.currentTime = percent * duration.value
}

const handleProgressHover = (e) => {
  if (!progressRef.value) return
  const rect = progressRef.value.getBoundingClientRect()
  const percent = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
  hoverTime.value = percent * duration.value
  hoverTimeDisplay.value = formatTime(hoverTime.value)
  hoverPosition.value = e.clientX - rect.left
  showHoverTime.value = true
}

const hideHoverTime = () => {
  showHoverTime.value = false
}

const setVolume = (e) => {
  const val = parseFloat(e.target.value)
  volume.value = val
  if (videoRef.value) {
    videoRef.value.volume = val
    isMuted.value = val === 0
  }
}

const toggleMute = () => {
  if (!videoRef.value) return
  isMuted.value = !isMuted.value
  videoRef.value.muted = isMuted.value
}

const setRate = (rate) => {
  playbackRate.value = rate
  if (videoRef.value) {
    videoRef.value.playbackRate = rate
  }
  showRateMenu.value = false
}

const toggleFullscreen = async () => {
  if (!playerRef.value) return
  if (!document.fullscreenElement) {
    await playerRef.value.requestFullscreen()
    isFullscreen.value = true
  } else {
    await document.exitFullscreen()
    isFullscreen.value = false
  }
}

const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
}

const showControlsTemporarily = () => {
  showControls.value = true
  clearTimeout(controlsTimer)
  controlsTimer = setTimeout(() => {
    if (isPlaying.value) showControls.value = false
  }, 3000)
}

const handleKeydown = (e) => {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return
  
  switch (e.code) {
    case 'Space':
      e.preventDefault()
      togglePlay()
      break
    case 'ArrowRight':
      e.preventDefault()
      if (videoRef.value) videoRef.value.currentTime = Math.min(duration.value, currentTime.value + 5)
      break
    case 'ArrowLeft':
      e.preventDefault()
      if (videoRef.value) videoRef.value.currentTime = Math.max(0, currentTime.value - 5)
      break
    case 'ArrowUp':
      e.preventDefault()
      volume.value = Math.min(1, volume.value + 0.1)
      if (videoRef.value) videoRef.value.volume = volume.value
      break
    case 'ArrowDown':
      e.preventDefault()
      volume.value = Math.max(0, volume.value - 0.1)
      if (videoRef.value) videoRef.value.volume = volume.value
      break
    case 'KeyF':
      e.preventDefault()
      toggleFullscreen()
      break
    case 'KeyM':
      e.preventDefault()
      toggleMute()
      break
  }
}

// 暴露方法给父组件
const seekTo = (time) => {
  if (videoRef.value) {
    videoRef.value.currentTime = time
    videoRef.value.play()
  }
}

defineExpose({ seekTo, videoRef })

onMounted(() => {
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  document.removeEventListener('keydown', handleKeydown)
  clearTimeout(controlsTimer)
})

watch(() => props.src, () => {
  if (videoRef.value) {
    videoRef.value.load()
    currentTime.value = 0
    duration.value = 0
  }
})
</script>

<template>
  <div 
    ref="playerRef"
    class="custom-player"
    :class="{ fullscreen: isFullscreen }"
    @mousemove="showControlsTemporarily"
    @mouseleave="showControls = false"
  >
    <!-- 视频层 -->
    <video
      ref="videoRef"
      :src="src"
      :poster="poster"
      :autoplay="autoplay"
      playsinline
      @timeupdate="handleTimeUpdate"
      @loadedmetadata="handleLoadedMetadata"
      @play="handlePlay"
      @pause="handlePause"
      @ended="handleEnded"
      @progress="handleProgress"
      @click="togglePlay"
    ></video>

    <!-- 中央播放按钮 -->
    <div v-if="!isPlaying" class="center-play" @click="togglePlay">
      <div class="play-circle">
        <span class="play-icon">▶</span>
      </div>
    </div>

    <!-- 控制栏 -->
    <div class="controls" :class="{ visible: showControls || !isPlaying }">
      <!-- 进度条 -->
      <div 
        ref="progressRef"
        class="progress-bar"
        @click="seek"
        @mousemove="handleProgressHover"
        @mouseleave="hideHoverTime"
      >
        <div class="progress-buffered" :style="{ width: bufferedPercent + '%' }"></div>
        <div class="progress-played" :style="{ width: progress + '%' }"></div>
        <div class="progress-thumb" :style="{ left: progress + '%' }"></div>
        
        <!-- 悬浮时间 -->
        <div 
          v-if="showHoverTime" 
          class="hover-time"
          :style="{ left: hoverPosition + 'px' }"
        >
          {{ hoverTimeDisplay }}
        </div>
      </div>

      <!-- 控制按钮区 -->
      <div class="controls-bottom">
        <div class="controls-left">
          <!-- 播放/暂停 -->
          <button class="ctrl-btn" @click="togglePlay">
            <span v-if="isPlaying">⏸</span>
            <span v-else>▶</span>
          </button>

          <!-- 时间 -->
          <span class="time-display">
            {{ currentTimeFormatted }} / {{ durationFormatted }}
          </span>
        </div>

        <div class="controls-right">
          <!-- 倍速 -->
          <div class="rate-wrapper">
            <button class="ctrl-btn rate-btn" @click="showRateMenu = !showRateMenu">
              {{ playbackRate }}x
            </button>
            <div v-if="showRateMenu" class="rate-menu">
              <button 
                v-for="r in rates" 
                :key="r" 
                :class="{ active: playbackRate === r }"
                @click="setRate(r)"
              >
                {{ r }}x
              </button>
            </div>
          </div>

          <!-- 音量 -->
          <div class="volume-wrapper" @mouseenter="showVolumeSlider = true" @mouseleave="showVolumeSlider = false">
            <button class="ctrl-btn" @click="toggleMute">
              <span v-if="isMuted || volume === 0">🔇</span>
              <span v-else-if="volume < 0.5">🔉</span>
              <span v-else>🔊</span>
            </button>
            <div v-if="showVolumeSlider" class="volume-slider">
              <input 
                type="range" 
                min="0" 
                max="1" 
                step="0.05" 
                :value="isMuted ? 0 : volume"
                @input="setVolume"
              >
            </div>
          </div>

          <!-- 全屏 -->
          <button class="ctrl-btn" @click="toggleFullscreen">
            <span v-if="isFullscreen">⛶</span>
            <span v-else>⛶</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-player {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  user-select: none;
}

.custom-player.fullscreen {
  border-radius: 0;
}

video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  cursor: pointer;
}

/* 中央播放按钮 */
.center-play {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  cursor: pointer;
  z-index: 10;
}

.play-circle {
  width: 70px;
  height: 70px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.play-circle:hover {
  background: rgba(79, 70, 229, 0.8);
  transform: scale(1.1);
}

.play-icon {
  font-size: 1.8rem;
  color: white;
  margin-left: 5px;
}

/* 控制栏 */
.controls {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0,0,0,0.8));
  padding: 20px 15px 12px;
  opacity: 0;
  transition: opacity 0.3s;
}

.controls.visible {
  opacity: 1;
}

/* 进度条 */
.progress-bar {
  position: relative;
  height: 4px;
  background: rgba(255,255,255,0.2);
  border-radius: 2px;
  cursor: pointer;
  margin-bottom: 10px;
  transition: height 0.15s;
}

.progress-bar:hover {
  height: 6px;
}

.progress-buffered {
  position: absolute;
  height: 100%;
  background: rgba(255,255,255,0.3);
  border-radius: 2px;
}

.progress-played {
  position: absolute;
  height: 100%;
  background: #4f46e5;
  border-radius: 2px;
  z-index: 1;
}

.progress-thumb {
  position: absolute;
  top: 50%;
  width: 12px;
  height: 12px;
  background: #4f46e5;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  opacity: 0;
  transition: opacity 0.15s;
  z-index: 2;
}

.progress-bar:hover .progress-thumb {
  opacity: 1;
}

.hover-time {
  position: absolute;
  bottom: 15px;
  transform: translateX(-50%);
  background: rgba(0,0,0,0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  pointer-events: none;
}

/* 控制按钮区 */
.controls-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.controls-left, .controls-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ctrl-btn {
  background: none;
  border: none;
  color: white;
  font-size: 1.1rem;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 4px;
  transition: background 0.2s;
}

.ctrl-btn:hover {
  background: rgba(255,255,255,0.1);
}

.time-display {
  color: rgba(255,255,255,0.9);
  font-size: 0.85rem;
  font-family: monospace;
}

/* 倍速菜单 */
.rate-wrapper {
  position: relative;
}

.rate-btn {
  font-size: 0.85rem;
  min-width: 40px;
}

.rate-menu {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0,0,0,0.9);
  border-radius: 6px;
  padding: 6px;
  margin-bottom: 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.rate-menu button {
  background: none;
  border: none;
  color: white;
  padding: 6px 12px;
  font-size: 0.85rem;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
}

.rate-menu button:hover {
  background: rgba(255,255,255,0.1);
}

.rate-menu button.active {
  color: #4f46e5;
  font-weight: bold;
}

/* 音量控制 */
.volume-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.volume-slider {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%) rotate(-90deg);
  transform-origin: center;
  background: rgba(0,0,0,0.9);
  padding: 10px 5px;
  border-radius: 6px;
  margin-bottom: 60px;
}

.volume-slider input[type="range"] {
  width: 80px;
  height: 4px;
  -webkit-appearance: none;
  background: rgba(255,255,255,0.3);
  border-radius: 2px;
}

.volume-slider input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  background: #4f46e5;
  border-radius: 50%;
  cursor: pointer;
}
</style>
