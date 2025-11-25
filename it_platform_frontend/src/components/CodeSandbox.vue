<script setup>
import { ref, onMounted } from 'vue'

const code = ref('print("Hello, IT Platform!")\n\n# 计算 1 到 10 的和\ntotal = sum(range(1, 11))\nprint(f"Sum is: {total}")')
const output = ref('')
const isRunning = ref(false)
const pyodide = ref(null)
const isReady = ref(false)

onMounted(async () => {
  if (!window.loadPyodide) {
    output.value = '错误: 未加载 Pyodide 运行环境。请检查网络或 index.html 配置。'
    return
  }
  output.value = '正在初始化 Python 环境...\n'
  try {
    pyodide.value = await window.loadPyodide()
    pyodide.value.setStdout({ batched: (msg) => { output.value += msg + '\n' } })
    isReady.value = true
    output.value += 'Python 环境就绪! 点击“运行代码”开始。\n'
  } catch (e) {
    output.value += `初始化失败: ${e.message}`
  }
})

const runCode = async () => {
  if (!isReady.value) return
  isRunning.value = true
  output.value = '>>> 运行中...\n'
  try {
    await pyodide.value.runPythonAsync(code.value)
  } catch (err) {
    output.value += `Traceback (most recent call last):\n${err.message}\n`
  } finally {
    isRunning.value = false
  }
}
</script>

<template>
  <div class="sandbox-container">
    <div class="editor-pane">
      <div class="toolbar">
        <span>Python 代码编辑器</span>
        <button @click="runCode" :disabled="!isReady || isRunning" class="btn-run">
          {{ isRunning ? '运行中...' : '▶ 运行代码' }}
        </button>
      </div>
      <textarea v-model="code" class="code-input" spellcheck="false"></textarea>
    </div>
    <div class="output-pane">
      <div class="pane-title">运行结果终端</div>
      <pre class="terminal">{{ output }}</pre>
    </div>
  </div>
</template>

<style scoped>
.sandbox-container { display: flex; height: 100%; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }
.editor-pane { flex: 1; display: flex; flex-direction: column; border-right: 1px solid #ddd; }
.output-pane { flex: 1; display: flex; flex-direction: column; background: #1e1e1e; color: #d4d4d4; }
.toolbar { padding: 10px; background: #f3f4f6; border-bottom: 1px solid #ddd; display: flex; justify-content: space-between; align-items: center; font-weight: bold; }
.btn-run { background: #28a745; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-weight: 600; }
.btn-run:disabled { background: #94d3a2; cursor: not-allowed; }
.code-input { flex: 1; width: 100%; padding: 15px; font-family: 'Consolas', 'Monaco', monospace; font-size: 14px; border: none; outline: none; resize: none; background: #fafafa; line-height: 1.5; }
.pane-title { padding: 10px; background: #252526; border-bottom: 1px solid #333; font-size: 0.9rem; }
.terminal { flex: 1; padding: 15px; margin: 0; overflow: auto; font-family: 'Consolas', monospace; font-size: 14px; white-space: pre-wrap; }
</style>
