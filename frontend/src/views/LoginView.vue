<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const account = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(account.value, password.value)
    router.replace(route.query.redirect || '/')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="container page">
    <form class="panel rise" @submit.prevent="submit">
      <h1>登录</h1>
      <p class="muted">使用用户名或 QQ 邮箱登录云云</p>
      <div class="field">
        <label for="account">账号</label>
        <input id="account" v-model="account" required autocomplete="username" />
      </div>
      <div class="field">
        <label for="password">密码</label>
        <input id="password" v-model="password" type="password" required minlength="6" autocomplete="current-password" />
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <button class="btn btn-primary" type="submit" :disabled="loading">
        {{ loading ? '登录中…' : '进入云云' }}
      </button>
      <p class="switch muted">
        <RouterLink to="/forgot-password">忘记密码？</RouterLink>
        · 还没有账号？
        <RouterLink to="/register">去注册</RouterLink>
      </p>
    </form>
  </section>
</template>

<style scoped>
.page {
  padding-top: 3.5rem;
  display: grid;
  place-items: start center;
}
.panel {
  width: min(100%, 420px);
  display: grid;
  gap: 0.9rem;
  padding: 1.8rem 1.5rem;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid var(--line);
  backdrop-filter: blur(8px);
}
h1 {
  margin: 0;
  font-family: var(--font-brand);
  letter-spacing: 0.16em;
  font-weight: 400;
}
.muted {
  margin: 0;
}
.switch a {
  color: var(--leaf-deep);
  border-bottom: 1px solid rgba(47, 107, 92, 0.35);
}
</style>
