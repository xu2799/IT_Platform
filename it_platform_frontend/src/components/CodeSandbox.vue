<script setup>
import { ref, watch } from 'vue'

const selectedLanguage = ref('javascript')
const isRunning = ref(false)
const output = ref('')
const pyodide = ref(null)
const isPyodideReady = ref(false)

// 代码模板
const templates = {
  javascript: `// JavaScript 示例
console.log('Hello, World!');

function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

for (let i = 0; i < 10; i++) {
  console.log('F(' + i + ') = ' + fibonacci(i));
}`,
  
  html: `<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: Arial; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .card { background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: 0 auto; }
    button { background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
  </style>
</head>
<body>
  <div class="card">
    <h1>欢迎来到代码沙箱！</h1>
    <p>这是HTML/CSS/JS示例</p>
    <button onclick="sayHello()">点击我</button>
    <p id="output"></p>
  </div>
  <` + `script>
    function sayHello() {
      document.getElementById('output').innerHTML = '你好！' + new Date().toLocaleTimeString();
    }
  </script` + `>
</body>
</html>`,
  
  python: `# Python 示例
print("Hello, Python!")

total = sum(range(1, 101))
print(f"1到100的和: {total}")

squares = [x**2 for x in range(1, 11)]
print(f"前10个平方数: {squares}")`,

  css: `/* CSS 样式示例 */
body {
  margin: 0;
  font-family: 'Segoe UI', Tahoma, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
}

.container {
  background: white;
  padding: 50px;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  text-align: center;
}

h1 {
  color: #667eea;
  font-size: 2.5rem;
  margin: 0 0 20px 0;
  animation: fadeIn 1s ease-in;
}

button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 15px 30px;
  border-radius: 25px;
  font-size: 1rem;
  cursor: pointer;
  transition: transform 0.2s;
}

button:hover {
  transform: translateY(-3px);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}`,

  typescript: `// TypeScript 示例
interface Person {
  name: string;
  age: number;
  email?: string;
}

class Student implements Person {
  constructor(
    public name: string,
    public age: number,
    public grade: number
  ) {}

  introduce(): string {
    return \`我是 \${this.name}，今年 \${this.age} 岁，成绩是 \${this.grade}\`;
  }
}

const students: Student[] = [
  new Student('张三', 20, 95),
  new Student('李四', 22, 88),
  new Student('王五', 21, 92)
];

students.forEach(student => {
  console.log(student.introduce());
});

const avgGrade = students.reduce((sum, s) => sum + s.grade, 0) / students.length;
console.log(\`平均成绩: \${avgGrade.toFixed(2)}\`);`,

  markdown: `# Markdown 示例

## 标题和文本

这是一段普通文本。**粗体文本**和*斜体文本*。

## 列表

### 无序列表
- 项目 1
- 项目 2
  - 子项目 2.1
  - 子项目 2.2
- 项目 3

### 有序列表
1. 第一步
2. 第二步
3. 第三步

## 代码

行内代码: \`console.log('Hello')\`

代码块:
\`\`\`javascript
function greeting(name) {
  return \`Hello, \${name}!\`;
}
\`\`\`

## 链接和图片

[访问 Google](https://www.google.com)

## 引用

> 这是一段引用文本
> 可以跨多行

## 表格

| 姓名 | 年龄 | 城市 |
|------|------|------|
| 张三 | 25   | 北京 |
| 李四 | 30   | 上海 |
| 王五 | 28   | 深圳 |`,

  json: `{
  "name": "IT Platform",
  "version": "1.0.0",
  "description": "在线学习平台",
  "features": [
    "课程管理",
    "视频播放",
    "在线讨论",
    "代码沙箱"
  ],
  "users": [
    {
      "id": 1,
      "username": "student1",
      "role": "学生",
      "courses": ["Python", "JavaScript", "Web开发"]
    },
    {
      "id": 2,
      "username": "teacher1",
      "role": "讲师",
      "courses": ["数据结构", "算法"]
    }
  ],
  "settings": {
    "theme": "light",
    "language": "zh-CN",
    "notifications": true
  }
}`
}

const code = ref(templates[selectedLanguage.value])

const languages = [
  { value: 'javascript', label: 'JavaScript', icon: '📜' },
  { value: 'html', label: 'HTML/CSS/JS', icon: '🌐' },
  { value: 'python', label: 'Python', icon: '🐍' },
  { value: 'css', label: 'CSS', icon: '🎨' },
  { value: 'typescript', label: 'TypeScript', icon: '📘' },
  { value: 'markdown', label: 'Markdown', icon: '📝' },
  { value: 'json', label: 'JSON', icon: '📋' }
]

watch(selectedLanguage, (newLang) => {
  code.value = templates[newLang]
  output.value = ''
})

const initPyodide = async () => {
  if (isPyodideReady.value) return
  if (!window.loadPyodide) {
    output.value = '错误: 未加载 Pyodide\n'
    return
  }
  output.value = '正在初始化 Python...\n'
  try {
    pyodide.value = await window.loadPyodide()
    pyodide.value.setStdout({ batched: (msg) => { output.value += msg + '\n' } })
    isPyodideReady.value = true
    output.value = 'Python 就绪!\n'
  } catch (e) {
    output.value += `初始化失败: ${e.message}\n`
  }
}

const runCode = async () => {
  if (isRunning.value) return
  isRunning.value = true
  output.value = `>>> 运行 ${languages.find(l => l.value === selectedLanguage.value).label}...\n\n`
  
  try {
    if (selectedLanguage.value === 'javascript') {
      await runJavaScript()
    } else if (selectedLanguage.value === 'html') {
      await runHTML()
    } else if (selectedLanguage.value === 'python') {
      await runPython()
    } else if (selectedLanguage.value === 'css') {
      await runCSS()
    } else if (selectedLanguage.value === 'typescript') {
      await runTypeScript()
    } else if (selectedLanguage.value === 'markdown') {
      await runMarkdown()
    } else if (selectedLanguage.value === 'json') {
      await runJSON()
    }
  } catch (err) {
    output.value += `\n错误: ${err.message}\n`
  } finally {
    isRunning.value = false
  }
}

const runJavaScript = async () => {
  const originalLog = console.log
  const logs = []
  
  console.log = (...args) => {
    logs.push(args.map(arg => 
      typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
    ).join(' '))
  }
  
  try {
    const fn = new Function(code.value)
    fn()
    output.value += logs.join('\n')
  } catch (err) {
    output.value += `错误:\n${err.stack || err.message}`
  } finally {
    console.log = originalLog
  }
}

const runHTML = async () => {
  const iframe = document.getElementById('html-preview')
  if (iframe) {
    iframe.srcdoc = code.value
    output.value = '✓ HTML已渲染到预览窗口'
  }
}

const runPython = async () => {
  if (!isPyodideReady.value) {
    await initPyodide()
    if (!isPyodideReady.value) return
  }
  
  try {
    await pyodide.value.runPythonAsync(code.value)
  } catch (err) {
    output.value += `错误:\n${err.message}\n`
  }
}

const runCSS = async () => {
  const iframe = document.getElementById('html-preview')
  if (iframe) {
    const htmlDoc = `<!DOCTYPE html>
<html>
<head>
  <style>${code.value}</style>
</head>
<body>
  <div class="container">
    <h1>CSS 预览</h1>
    <p>这是一段测试文本</p>
    <button>测试按钮</button>
  </div>
</body>
</html>`
    iframe.srcdoc = htmlDoc
    output.value = '✓ CSS已应用到预览窗口'
  }
}

const runTypeScript = async () => {
  try {
    // 简单地将TypeScript当作JavaScript执行（实际应该编译）
    const originalLog = console.log
    const logs = []
    
    console.log = (...args) => {
      logs.push(args.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
      ).join(' '))
    }
    
    // 注意：这里直接执行，实际生产环境应该先编译
    const fn = new Function(code.value)
    fn()
    output.value += logs.join('\n')
    output.value += '\n\n注意：TypeScript代码直接作为JavaScript执行'
    
    console.log = originalLog
  } catch (err) {
    output.value += `错误:\n${err.stack || err.message}`
  }
}

const runMarkdown = async () => {
  const iframe = document.getElementById('html-preview')
  if (iframe) {
    // 简单的Markdown转HTML（仅支持基本语法）
    let html = code.value
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
      .replace(/\*(.*)\*/gim, '<em>$1</em>')
      .replace(/\`([^\`]+)\`/gim, '<code>$1</code>')
      .replace(/\n- (.*)/gim, '<li>$1</li>')
      .replace(/\n\d+\. (.*)/gim, '<li>$1</li>')
      .replace(/\n/gim, '<br>')
    
    const htmlDoc = `<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: Arial; padding: 30px; line-height: 1.6; max-width: 800px; margin: 0 auto; }
    h1 { color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
    h2 { color: #555; }
    h3 { color: #777; }
    code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
    li { margin: 5px 0; }
  </style>
</head>
<body>${html}</body>
</html>`
    iframe.srcdoc = htmlDoc
    output.value = '✓ Markdown已渲染到预览窗口'
  }
}

const runJSON = async () => {
  try {
    const parsed = JSON.parse(code.value)
    output.value = '✓ JSON 格式正确\n\n格式化输出:\n' + JSON.stringify(parsed, null, 2)
  } catch (err) {
    output.value = `✗ JSON 格式错误:\n${err.message}`
  }
}

const clearOutput = () => {
  output.value = ''
}
</script>

<template>
  <div class="sandbox-container">
    <div class="editor-pane">
      <div class="toolbar">
        <div class="language-selector">
          <button 
            v-for="lang in languages" 
            :key="lang.value"
            @click="selectedLanguage = lang.value"
            :class="{ active: selectedLanguage === lang.value }"
            class="lang-btn"
          >
            {{ lang.icon }} {{ lang.label }}
          </button>
        </div>
        <div class="action-buttons">
          <button @click="runCode" :disabled="isRunning" class="btn-run">
            {{ isRunning ? '运行中...' : '▶ 运行' }}
          </button>
        </div>
      </div>
      <textarea 
        v-model="code" 
        class="code-input" 
        spellcheck="false"
      ></textarea>
    </div>
    
    <div class="output-pane">
      <div class="pane-title">
        <span>{{ ['html', 'css', 'markdown'].includes(selectedLanguage) ? '渲染预览' : '运行结果' }}</span>
        <button @click="clearOutput" class="btn-clear-output">清空</button>
      </div>
      
      <iframe 
        v-if="['html', 'css', 'markdown'].includes(selectedLanguage)" 
        id="html-preview"
        class="html-preview"
        sandbox="allow-scripts"
      ></iframe>
      
      <pre v-else class="terminal">{{ output || '点击"运行"查看结果...' }}</pre>
    </div>
  </div>
</template>

<style scoped>
.sandbox-container { display: flex; height: 100%; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; background: white; }
.editor-pane { flex: 0 0 40%; display: flex; flex-direction: column; border-right: 1px solid #e2e8f0; min-width: 300px; }
.output-pane { flex: 1; display: flex; flex-direction: column; background: #1e1e1e; }
.toolbar { padding: 12px 15px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; gap: 15px; flex-wrap: wrap; }
.language-selector { display: flex; gap: 8px; flex-wrap: wrap; }
.lang-btn { padding: 8px 16px; border: 1px solid #e2e8f0; background: white; border-radius: 6px; cursor: pointer; font-size: 0.9rem; font-weight: 500; color: #64748b; transition: all 0.2s; }
.lang-btn:hover { background: #f1f5f9; border-color: #cbd5e1; }
.lang-btn.active { background: #4f46e5; color: white; border-color: #4f46e5; }
.action-buttons { display: flex; gap: 8px; }
.btn-run { background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; transition: background 0.2s; }
.btn-run:hover { background: #059669; }
.btn-run:disabled { background: #94d3a2; cursor: not-allowed; }
.btn-clear { background: #64748b; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; transition: background 0.2s; }
.btn-clear:hover { background: #475569; }
.code-input { flex: 1; width: 100%; padding: 20px; font-family: 'Consolas', 'Monaco', monospace; font-size: 14px; border: none; outline: none; resize: none; background: #fafafa; line-height: 1.6; color: #1f2937; }
.pane-title { padding: 12px 15px; background: #252526; border-bottom: 1px solid #333; font-size: 0.9rem; color: #d4d4d4; font-weight: 600; display: flex; justify-content: space-between; align-items: center; }
.btn-clear-output { background: #374151; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 0.85rem; font-weight: 600; transition: background 0.2s; }
.btn-clear-output:hover { background: #4b5563; }
.terminal { flex: 1; padding: 20px; margin: 0; overflow: auto; font-family: 'Consolas', monospace; font-size: 14px; white-space: pre-wrap; color: #d4d4d4; line-height: 1.6; }
.html-preview { flex: 1; width: 100%; border: none; background: white; }
</style>
