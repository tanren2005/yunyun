<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const items = ref([])
const error = ref('')

onMounted(load)

async function load() {
  if (!auth.isLoggedIn) {
    router.replace({ name: 'login', query: { redirect: '/notifications' } })
    return
  }
  try {
    items.value = await api.notifications(auth.token)
    await api.readAllNotifications(auth.token)
    auth.unread = 0
  } catch (e) {
    error.value = e.message
  }
}

function formatDate(iso) {
  return new Date(iso).toLocaleString('zh-CN')
}

function openItem(item) {
  if (item.link) router.push(item.link)
}
</script>

<template>
  <section class="container page">
    <header class="head">
      <h1>消息</h1>
      <p class="muted">别人回复你的作品、动态或读书分享会出现在这里。</p>
    </header>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-else-if="!items.length" class="muted">暂时没有消息。</p>
    <ul v-else class="list">
      <li v-for="n in items" :key="n.id" @click="openItem(n)">
        <strong>{{ n.title }}</strong>
        <p>{{ n.body }}</p>
        <span class="muted">{{ formatDate(n.created_at) }}</span>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.page {
  padding-top: 2.4rem;
  max-width: 720px;
}
.head h1 {
  margin: 0;
  font-family: var(--font-brand);
  letter-spacing: 0.14em;
  font-weight: 400;
}
.list {
  list-style: none;
  margin: 1rem 0 0;
  padding: 0;
}
.list li {
  padding: 1rem 0;
  border-top: 1px solid var(--line);
  cursor: pointer;
}
.list p {
  margin: 0.35rem 0;
  color: var(--ink-soft);
}
</style>
