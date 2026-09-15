<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const items = ref([])
const error = ref('')

onMounted(async () => {
  try {
    // 累积展示：按时间倒序，一篇接一篇全文
    items.value = await api.dailyHistory(60)
  } catch (e) {
    error.value = e.message
  }
})
</script>

<template>
  <section class="container page">
    <header class="head rise">
      <p class="tag">每日一阅</p>
      <h1>开卷累积</h1>
      <p class="muted">
        每小时新开一篇完整的云散、云说、诗歌或名句（中学语文阅读篇幅），附出处与典故。新篇加在最上方，往下可继续读往期全文。
      </p>
    </header>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-else-if="!items.length" class="muted">暂无开卷内容。</p>

    <article v-for="(item, idx) in items" :key="item.id" class="card rise" :class="{ latest: idx === 0 }">
      <div class="meta">
        <span class="tag">{{ item.kind_label }}</span>
        <span class="muted">{{ item.day }}</span>
        <span v-if="idx === 0" class="now">本小时</span>
      </div>
      <h2>{{ item.title }}</h2>
      <div class="body">{{ item.body }}</div>
      <p class="source">出处：{{ item.source }}</p>
      <p v-if="item.note" class="note">
        <strong>典故与背景</strong>
        {{ item.note }}
      </p>
    </article>
  </section>
</template>

<style scoped>
.page {
  padding-top: 2.4rem;
  max-width: 720px;
}
.head h1 {
  margin: 0.35rem 0;
  font-family: var(--font-brand);
  font-size: 2.4rem;
  letter-spacing: 0.16em;
  font-weight: 400;
}
.card {
  padding: 1.6rem 0 2.2rem;
  border-top: 1px solid var(--line);
}
.card.latest {
  border-top-color: rgba(47, 107, 92, 0.45);
}
.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 1rem;
  margin-bottom: 0.8rem;
  align-items: center;
}
.now {
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  color: var(--leaf-deep);
  border: 1px solid rgba(47, 107, 92, 0.35);
  padding: 0.1rem 0.45rem;
}
h2 {
  margin: 0 0 1rem;
  letter-spacing: 0.06em;
}
.body {
  white-space: pre-wrap;
  font-size: 1.08rem;
  line-height: 2;
}
.source {
  margin-top: 1.4rem;
  color: var(--ink-soft);
  font-size: 0.92rem;
}
.note {
  margin: 1rem 0 0;
  padding: 1rem 1.1rem;
  background: rgba(47, 107, 92, 0.06);
  border-left: 3px solid var(--leaf-deep);
  line-height: 1.75;
  font-size: 0.95rem;
  color: var(--ink-soft);
}
.note strong {
  display: block;
  margin-bottom: 0.35rem;
  color: var(--leaf-deep);
  letter-spacing: 0.06em;
  font-size: 0.88rem;
}
</style>
