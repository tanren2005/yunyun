<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const code = ref('')
const username = ref('')
const displayName = ref('')
const password = ref('')
const error = ref('')
const info = ref('')
const loading = ref(false)
const sending = ref(false)
const cooldown = ref(0)
let timer = null

async function sendCode() {
  error.value = ''
  info.value = ''
  sending.value = true
  try {
    const res = await api.sendCode(email.value)
    info.value = res.message
    if (res.dev_code) {
      code.value = res.dev_code
      info.value = `尚未配置发信，验证码是 ${res.dev_code}（已填入上方）`
    }
    cooldown.value = 60
    clearInterval(timer)
    timer = setInterval(() => {
      cooldown.value -= 1
      if (cooldown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (e) {
    error.value = e.message
  } finally {
    sending.value = false
  }
}

function passwordOk(value) {
  return value.length >= 8 && /[A-Z]/.test(value) && /[a-z]/.test(value)
}

async function submit() {
  error.value = ''
  if (!passwordOk(password.value)) {
    error.value = '密码至少 8 位，且须同时包含大写字母和小写字母'
    return
  }
  loading.value = true
  try {
    await auth.register({
      email: email.value,
      code: code.value,
      username: username.value,
      display_name: displayName.value,
      password: password.value,
    })
    router.replace('/')
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
      <h1>注册</h1>
      <p class="muted">需 QQ 邮箱验证码；同一邮箱最多两个账号。</p>

      <div class="field">
        <label for="email">QQ 邮箱</label>
        <div class="inline">
          <input id="email" v-model="email" type="email" required placeholder="you@qq.com" />
          <button
            class="btn btn-ghost"
            type="button"
            :disabled="sending || cooldown > 0"
            @click="sendCode"
          >
            {{ cooldown > 0 ? `${cooldown}s` : sending ? '发送中' : '获取验证码' }}
          </button>
        </div>
      </div>

      <div class="field">
        <label for="code">验证码</label>
        <input id="code" v-model="code" required maxlength="8" />
      </div>
      <div class="field">
        <label for="username">用户名</label>
        <input
          id="username"
          v-model="username"
          required
          minlength="2"
          maxlength="32"
          placeholder="全站唯一，如 TTTTTr、小云"
        />
        <span class="hint">登录用。中文、字母、数字都可以，须全站唯一。</span>
      </div>
      <div class="field">
        <label for="display">显示名</label>
        <input id="display" v-model="displayName" required maxlength="64" placeholder="作品旁展示的名字" />
      </div>
      <div class="field">
        <label for="password">密码</label>
        <input id="password" v-model="password" type="password" required minlength="8" />
        <span class="hint">至少 8 位，须同时包含大写和小写字母，如 Yunyun123。</span>
      </div>

      <p v-if="info" class="muted">{{ info }}</p>
      <p v-if="error" class="error">{{ error }}</p>

      <button class="btn btn-primary" type="submit" :disabled="loading">
        {{ loading ? '注册中…' : '创建云云' }}
      </button>
      <p class="switch muted">
        已有账号？
        <RouterLink to="/login">去登录</RouterLink>
      </p>
    </form>
  </section>
</template>

<style scoped>
.page {
  padding-top: 2.8rem;
  display: grid;
  place-items: start center;
}
.panel {
  width: min(100%, 460px);
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
.hint {
  font-size: 0.82rem;
  color: var(--ink-soft);
}
.inline {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.55rem;
}
.switch a {
  color: var(--leaf-deep);
  border-bottom: 1px solid rgba(47, 107, 92, 0.35);
}
</style>
