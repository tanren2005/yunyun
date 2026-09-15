<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import PostCard from '../components/PostCard.vue'

const route = useRoute()
const posts = ref([])
const categories = ref([])
const loading = ref(true)
const error = ref('')

const current = computed(() => categories.value.find((c) => c.slug === route.params.slug))

async function load() {
  loading.value = true
  error.value = ''
  try {
    if (!categories.value.length) categories.value = await api.categories()
    posts.value = await api.posts({ category: route.params.slug, limit: 30 })
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => route.params.slug, load)
</script>

<template>
  <section class="container page">
    <header class="head rise">
      <p class="tag">栏目</p>
      <h1>{{ current?.name || route.params.slug }}</h1>
      <p class="muted">{{ current?.description || '' }}</p>
    </header>

    <p v-if="loading" class="muted">加载中…</p>
    <p v-else-if="error" class="error">{{ error }}</p>
    <p v-else-if="!posts.length" class="muted">这个栏目还没有作品。</p>
    <div v-else class="list">
      <PostCard v-for="p in posts" :key="p.id" :post="p" />
    </div>
  </section>
</template>

<style scoped>
.page {
  padding-top: 2.5rem;
}
.head {
  margin-bottom: 1.5rem;
}
.head h1 {
  margin: 0.4rem 0;
  font-family: var(--font-brand);
  font-size: clamp(2rem, 5vw, 3rem);
  letter-spacing: 0.16em;
  font-weight: 400;
}
.head p {
  margin: 0;
}
</style>
