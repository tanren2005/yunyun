<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const displayName = ref('')
const code = ref('')
const newPassword = ref('')
const info = ref('')
const error = ref('')
const pwdInfo = ref('')
const pwdError = ref('')
const saving = ref(false)
const sending = ref(false)
const changing = ref(false)

onMounted(() => {
  if (!auth.isLoggedIn) {
    router.replace({ name: 'login', query: { redirect: '/profile' } })
    return
  }
  displayName.value = auth.user.display_name
})

async function saveProfile() {
  error.value = ''
  info.value = ''
  saving.value = true
  try {
    const u = await api.updateProfile({ display_name: displayName.value }, auth.token)
    auth.user = u
    auth.persist()
    info.value = '资料已保存'
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}

async function sendCode() {
  pwdError.value = ''
  pwdInfo.value = ''
  sending.value = true
  try {
    const res = await api.sendPasswordCode(auth.token)
    pwdInfo.value = res.message
    if (res.dev_code) {
      code.value = res.dev_code
      pwdInfo.value = `验证码：${res.dev_code}（已填入）`
    }
  } catch (e) {
    pwdError.value = e.message
  } finally {
    sending.value = false
  }
}

function passwordOk(value) {
  return value.length >= 8 && /[A-Z]/.test(value) && /[a-z]/.test(value)
}

async function changePwd() {
  pwdError.value = ''
  pwdInfo.value = ''
  if (!passwordOk(newPassword.value)) {
    pwdError.value = '新密码至少 8 位，且须同时有大写和小写字母'
    return
  }
  changing.value = true
  try {
    await api.changePassword({ code: code.value, new_password: newPassword.value }, auth.token)
    auth.logout()
    router.replace({ name: 'login', query: { redirect: '/profile' } })
  } catch (e) {
    pwdError.value = e.message
  } finally {
    changing.value = false
  }
}
</script>

<template>
  <section class="container page">
    <header class="head">
      <h1>我的资料</h1>
      <p class="muted">查看账号信息，可改显示名；改密码需邮箱验证码。</p>
    </header>

    <div v-if="auth.user" class="panel">
      <div class="row"><span>用户名</span><strong>{{ auth.user.username }}</strong></div>
      <div class="row"><span>邮箱</span><strong>{{ auth.user.email }}</strong></div>
      <div class="field">
        <label>显示名</label>
        <input v-model="displayName" maxlength="64" />
      </div>
      <p v-if="info" class="muted">{{ info }}</p>
      <p v-if="error" class="error">{{ error }}</p>
      <button class="btn btn-primary" type="button" :disabled="saving" @click="saveProfile">
        {{ saving ? '保存中…' : '保存资料' }}
      </button>
    </div>

    <div class="panel">
      <h2>修改密码</h2>
      <p class="muted">验证码会发到你的注册 QQ 邮箱。</p>
      <div class="field">
        <label>验证码</label>
        <div class="inline">
          <input v-model="code" maxlength="8" />
          <button class="btn btn-ghost" type="button" :disabled="sending" @click="sendCode">
            {{ sending ? '发送中' : '获取验证码' }}
          </button>
        </div>
      </div>
      <div class="field">
        <label>新密码</label>
        <input v-model="newPassword" type="password" minlength="8" />
      </div>
      <p v-if="pwdInfo" class="muted">{{ pwdInfo }}</p>
      <p v-if="pwdError" class="error">{{ pwdError }}</p>
      <button class="btn btn-primary" type="button" :disabled="changing" @click="changePwd">
        {{ changing ? '提交中…' : '确认修改' }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.page {
  padding-top: 2.4rem;
  max-width: 560px;
}
.head h1 {
  margin: 0;
  font-family: var(--font-brand);
  letter-spacing: 0.14em;
  font-weight: 400;
}
.panel {
  display: grid;
  gap: 0.85rem;
  margin-top: 1.4rem;
  padding: 1.2rem 0;
  border-top: 1px solid var(--line);
}
.row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  color: var(--ink-soft);
}
.inline {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.5rem;
}
h2 {
  margin: 0;
  font-size: 1.15rem;
}
</style>
