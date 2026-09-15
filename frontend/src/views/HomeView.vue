<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'
import PostCard from '../components/PostCard.vue'

const posts = ref([])
const categories = ref([])
const daily = ref(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    ;[categories.value, posts.value, daily.value] = await Promise.all([
      api.categories(),
      api.posts({ limit: 8 }),
      api.daily().catch(() => null),
    ])
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section class="hero">
    <div class="container hero-grid">
      <div class="copy rise">
        <p class="eyebrow">文学小站</p>
        <h1 class="brand-title">云云</h1>
        <p class="lead">云散、云说、诗歌与云笔；云间动态对所有读友公开；每日一阅与云友会一起把日子过得更有字。</p>
        <div class="cta">
          <RouterLink class="btn btn-primary" to="/write">开始书写</RouterLink>
          <RouterLink class="btn btn-ghost" to="/moments">去云间</RouterLink>
          <RouterLink class="btn btn-ghost" to="/daily">今日一阅</RouterLink>
        </div>
      </div>
      <div class="visual rise" aria-hidden="true">
        <div class="orb"></div>
        <div class="panel">
          <span>云起时</span>
          <span>字落处</span>
        </div>
      </div>
    </div>
  </section>

  <section class="container section">
    <div class="section-head">
      <h2>栏目</h2>
      <p class="muted">按题材走进不同书架</p>
    </div>
    <div class="cats">
      <RouterLink v-for="c in categories" :key="c.id" class="cat" :to="`/c/${c.slug}`">
        <strong>{{ c.name }}</strong>
        <span>{{ c.description }}</span>
      </RouterLink>
    </div>
  </section>

  <section v-if="daily" class="container section">
    <div class="section-head">
      <h2>每日一阅</h2>
      <p class="muted">{{ daily.day }} · {{ daily.kind_label }}</p>
    </div>
    <RouterLink class="daily-card" to="/daily">
      <strong>{{ daily.title }}</strong>
      <p>{{ daily.body.slice(0, 160) }}{{ daily.body.length > 160 ? '…' : '' }}</p>
      <span>出处：{{ daily.source }} · 点进可读往期全文累积</span>
    </RouterLink>
  </section>

  <section class="container section">
    <div class="section-head">
      <h2>广场</h2>
      <p class="muted">动态、读书会与今日开卷</p>
    </div>
    <div class="cats">
      <RouterLink class="cat" to="/moments">
        <strong>云间</strong>
        <span>公开动态，人人都是好友</span>
      </RouterLink>
      <RouterLink class="cat" to="/club">
        <strong>云友会</strong>
        <span>把正在读的书递给别人</span>
      </RouterLink>
      <RouterLink class="cat" to="/daily">
        <strong>每日一阅</strong>
        <span>今日名句与出处</span>
      </RouterLink>
      <RouterLink class="cat" to="/write">
        <strong>写一篇</strong>
        <span>手打或上传 Word / 文本</span>
      </RouterLink>
    </div>
  </section>

  <section class="container section">
    <div class="section-head">
      <h2>最新作品</h2>
      <p class="muted">全站最近写下的文字</p>
    </div>
    <p v-if="loading" class="muted">加载中…</p>
    <p v-else-if="error" class="error">{{ error }}</p>
    <p v-else-if="!posts.length" class="muted">还没有作品，来写下第一篇吧。</p>
    <div v-else class="list">
      <PostCard v-for="p in posts" :key="p.id" :post="p" />
    </div>
  </section>
</template>

<style scoped>
.hero {
  padding: 4.5rem 0 2.5rem;
  min-height: min(72vh, 640px);
  display: grid;
  align-items: center;
}

.hero-grid {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 2rem;
  align-items: center;
}

.eyebrow {
  margin: 0 0 0.6rem;
  letter-spacing: 0.28em;
  color: var(--leaf-deep);
  font-size: 0.85rem;
}

.brand-title {
  margin: 0;
  font-family: var(--font-brand);
  font-size: clamp(3.6rem, 9vw, 6.2rem);
  letter-spacing: 0.22em;
  line-height: 1.05;
  font-weight: 400;
}

.lead {
  margin: 1rem 0 1.6rem;
  max-width: 28rem;
  font-size: 1.08rem;
  color: var(--ink-soft);
}

.cta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
}

.visual {
  position: relative;
  min-height: 280px;
}

.orb {
  position: absolute;
  inset: 12% 18% auto auto;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background:
    radial-gradient(circle at 35% 30%, rgba(255, 255, 255, 0.55), transparent 45%),
    radial-gradient(circle at 60% 70%, rgba(184, 92, 56, 0.28), rgba(47, 107, 92, 0.55));
  filter: blur(2px);
  animation: drift 4s ease-in-out infinite alternate;
}

.panel {
  position: absolute;
  right: 8%;
  bottom: 8%;
  display: grid;
  gap: 0.35rem;
  padding: 1.4rem 1.6rem;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid var(--line);
  backdrop-filter: blur(8px);
  font-family: var(--font-brand);
  letter-spacing: 0.22em;
  font-size: 1.2rem;
}

.section {
  padding: 2.2rem 0 1rem;
}

.section-head {
  margin-bottom: 1.2rem;
}

.section-head h2 {
  margin: 0;
  font-size: 1.55rem;
  letter-spacing: 0.08em;
}

.section-head p {
  margin: 0.25rem 0 0;
}

.cats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}

.cat {
  display: grid;
  gap: 0.45rem;
  padding: 1.2rem 1rem;
  border-top: 1px solid var(--line);
  transition: background 0.2s ease, transform 0.2s ease;
}

.cat:hover {
  background: rgba(255, 255, 255, 0.45);
  transform: translateY(-2px);
}

.cat strong {
  font-size: 1.15rem;
  letter-spacing: 0.12em;
}

.cat span {
  color: var(--ink-soft);
  font-size: 0.9rem;
}

.list {
  display: grid;
}

.daily-card {
  display: grid;
  gap: 0.5rem;
  padding: 1.2rem 0;
  border-top: 1px solid var(--line);
}

.daily-card p {
  margin: 0;
  color: var(--ink-soft);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.daily-card span {
  font-size: 0.9rem;
  color: var(--leaf-deep);
}

@media (max-width: 860px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }
  .visual {
    min-height: 200px;
  }
  .cats {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 520px) {
  .cats {
    grid-template-columns: 1fr;
  }
}
</style>
