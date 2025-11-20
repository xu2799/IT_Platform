<script setup>
import BackButton from '@/components/BackButton.vue'
</script>

<template>
  <div class="page-container">
    <div class="header-section">
      <BackButton 
        :fallback-route="{ name: 'courses' }" 
        text="返回课程列表"
        small
      />
      <h1>关于我们</h1>
      <p class="subtitle">连接技术与未来，赋能每一位开发者</p>
    </div>

    <section class="intro-card">
      <div class="intro-content">
        <h2>我们的故事</h2>
        <p>
          IT 职业技能在线培训平台成立于 2025 年，是一个专注于程序员职业成长的在线教育社区。
          我们深知技术更新迭代的速度，因此我们要做的不仅仅是传授知识，更是培养解决问题的能力。
        </p>
        <p>
          在这里，我们拒绝枯燥的理论念经，坚持<strong>“项目驱动”</strong>的教学理念。
          每一门课程都旨在帮助你解决实际工作中的痛点，助你完成从“学院派”到“实战派”的华丽转身。
        </p>
      </div>
    </section>

    <section class="features-grid">
      <div class="feature-card">
        <div class="icon">⚡</div>
        <h3>实战导向</h3>
        <p>拒绝纸上谈兵，所有课程均源自一线互联网大厂的真实业务场景。</p>
      </div>
      <div class="feature-card">
        <div class="icon">📚</div>
        <h3>体系化课程</h3>
        <p>从 Python 入门到全栈架构，为你规划清晰的职业晋升学习路径。</p>
      </div>
      <div class="feature-card">
        <div class="icon">🤝</div>
        <h3>社群陪伴</h3>
        <p>加入学员专属交流群，与讲师和同学实时互动，学习路上不孤单。</p>
      </div>
      <div class="feature-card">
        <div class="icon">💎</div>
        <h3>严选师资</h3>
        <p>每一位讲师都经过严格筛选，确保不仅技术过硬，更懂得如何教学。</p>
      </div>
    </section>

    <section class="stats-bar">
      <div class="stat-item">
        <div class="number">10,000+</div>
        <div class="label">累计学员</div>
      </div>
      <div class="divider"></div>
      <div class="stat-item">
        <div class="number">500+</div>
        <div class="label">原创课时</div>
      </div>
      <div class="divider"></div>
      <div class="stat-item">
        <div class="number">99%</div>
        <div class="label">学员好评</div>
      </div>
    </section>

    <section class="contact-section">
      <h2>联系我们</h2>
      <p>无论是课程咨询、商务合作还是意见反馈，我们都随时欢迎您的来信。</p>
      <ul class="contact-list">
        <li>📧 <strong>官方邮箱：</strong> support@it-platform.com</li>
        <li>📞 <strong>客服热线：</strong> 400-123-4567 (工作日 9:00-18:00)</li>
        <li>🏢 <strong>总部地址：</strong> 中国上海市浦东新区科技园区 88 号</li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.page-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 40px 20px;
}

.header-section {
  text-align: center;
  margin-bottom: 50px;
}

.header-section h1 {
  font-size: 2.5rem;
  color: var(--color-text-main);
  margin: 10px 0;
  font-weight: 800;
}

.subtitle {
  font-size: 1.2rem;
  color: var(--color-text-muted);
}

/* 通用卡片样式 */
.intro-card, .feature-card, .contact-section, .stats-bar {
  background: white;
  border-radius: 16px;
  padding: 30px;
  box-shadow: var(--shadow-sm);
  margin-bottom: 30px;
  border: 1px solid #f3f4f6;
}

/* 介绍卡片 */
.intro-content h2 {
  font-size: 1.5rem;
  margin-bottom: 20px;
  color: var(--color-primary);
}
.intro-content p {
  font-size: 1.05rem;
  line-height: 1.8;
  color: var(--color-text-main);
  margin-bottom: 15px;
}

/* 核心优势 Grid */
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
  background: transparent; /* Grid 不需要背景，卡片有背景 */
  box-shadow: none;
  padding: 0;
  border: none;
}

.feature-card {
  text-align: center;
  transition: transform 0.3s;
  margin-bottom: 0; /* 覆盖通用样式 */
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-md);
}

.feature-card .icon {
  font-size: 2.5rem;
  margin-bottom: 15px;
}

.feature-card h3 {
  font-size: 1.2rem;
  margin-bottom: 10px;
  color: var(--color-text-main);
}

.feature-card p {
  font-size: 0.9rem;
  color: var(--color-text-muted);
  line-height: 1.5;
}

/* 统计栏 */
.stats-bar {
  display: flex;
  justify-content: space-around;
  align-items: center;
  background: linear-gradient(135deg, var(--color-primary) 0%, #8b5cf6 100%);
  color: white;
}

.stat-item {
  text-align: center;
}

.stat-item .number {
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 5px;
}

.stat-item .label {
  font-size: 1rem;
  opacity: 0.9;
}

.divider {
  width: 1px;
  height: 40px;
  background: rgba(255, 255, 255, 0.3);
}

/* 联系我们 */
.contact-section h2 {
  text-align: center;
  margin-bottom: 15px;
  font-size: 1.5rem;
}

.contact-section > p {
  text-align: center;
  color: var(--color-text-muted);
  margin-bottom: 30px;
}

.contact-list {
  list-style: none;
  padding: 0;
  max-width: 500px;
  margin: 0 auto;
}

.contact-list li {
  font-size: 1.1rem;
  padding: 15px 0;
  border-bottom: 1px dashed #eee;
  display: flex;
  align-items: center;
}

.contact-list li:last-child {
  border-bottom: none;
}

@media (max-width: 768px) {
  .features-grid {
    grid-template-columns: 1fr;
  }
  .stats-bar {
    flex-direction: column;
    gap: 20px;
  }
  .divider {
    width: 50px;
    height: 1px;
  }
}
</style>