<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
let timer = null

onMounted(() => {
  if (auth.isLoggedIn) auth.refreshUnread()
  timer = setInterval(() => {
    if (auth.isLoggedIn) auth.refreshUnread()
  }, 20000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

function logout() {
  auth.logout()
  router.push('/')
}
</script>

<template>
  <header class="header">
    <div class="container bar">
      <RouterLink class="brand" to="/">
        <span class="mark" aria-hidden="true"></span>
        <span class="name">云云</span>
      </RouterLink>

      <nav class="nav">
        <RouterLink to="/c/prose">云散</RouterLink>
        <RouterLink to="/c/fiction">云说</RouterLink>
        <RouterLink to="/c/poetry">诗歌</RouterLink>
        <RouterLink to="/c/essay">云笔</RouterLink>
        <RouterLink to="/moments">云间</RouterLink>
        <RouterLink to="/club">云友会</RouterLink>
        <RouterLink to="/daily">每日一阅</RouterLink>
        <RouterLink to="/contact">联系</RouterLink>
      </nav>

      <div class="actions">
        <template v-if="auth.isLoggedIn">
          <RouterLink class="btn btn-primary" to="/write">写一篇</RouterLink>
          <RouterLink class="btn btn-ghost" to="/profile">资料</RouterLink>
          <RouterLink v-if="auth.isAdmin" class="btn btn-ghost" to="/admin">管理</RouterLink>
          <RouterLink class="who-link" to="/notifications" title="消息">
            <span class="who">{{ auth.user.display_name }}</span>
            <span v-if="auth.unread > 0" class="dot">{{ auth.unread > 99 ? '99+' : auth.unread }}</span>
          </RouterLink>
          <button class="btn btn-ghost" type="button" @click="logout">退出</button>
        </template>
        <template v-else>
          <RouterLink class="btn btn-ghost" to="/login">登录</RouterLink>
          <RouterLink class="btn btn-primary" to="/register">注册</RouterLink>
        </template>
      </div>
    </div>
  </header>
</template>

<style scoped>
.header {
  position: sticky;
  top: 0;
  z-index: 20;
  backdrop-filter: blur(12px);
  background: rgba(243, 247, 245, 0.78);
  border-bottom: 1px solid var(--line);
}

.bar {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 0.8rem 1rem;
  min-height: 4.2rem;
  padding: 0.45rem 0;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
}

.mark {
  width: 0.85rem;
  height: 0.85rem;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, #7db8a8, var(--leaf-deep));
  box-shadow: 0 0 0 6px rgba(47, 107, 92, 0.12);
  animation: drift 3.2s ease-in-out infinite alternate;
}

.name {
  font-family: var(--font-brand);
  font-size: 1.7rem;
  letter-spacing: 0.18em;
}

.nav {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.7rem 1.05rem;
  color: var(--ink-soft);
  font-size: 0.92rem;
}

.nav a.router-link-active {
  color: var(--leaf-deep);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 0.45rem;
  max-width: min(100%, 28rem);
}

.actions .btn {
  padding: 0.45rem 0.85rem;
  font-size: 0.88rem;
  white-space: nowrap;
}

.who-link {
  position: relative;
  display: inline-flex;
  align-items: center;
  padding-right: 0.35rem;
}

.who {
  font-size: 0.92rem;
  color: var(--ink-soft);
}

.dot {
  position: absolute;
  top: -0.35rem;
  right: -0.55rem;
  min-width: 1.05rem;
  height: 1.05rem;
  padding: 0 0.28rem;
  border-radius: 999px;
  background: #c45c48;
  color: #fff;
  font-size: 0.68rem;
  line-height: 1.05rem;
  text-align: center;
}

@media (max-width: 900px) {
  .bar {
    grid-template-columns: 1fr auto;
  }
  .nav {
    grid-column: 1 / -1;
    justify-content: flex-start;
  }
}
</style>
