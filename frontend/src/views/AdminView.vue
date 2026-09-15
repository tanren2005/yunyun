<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const users = ref([])
const q = ref('')
const error = ref('')
const info = ref('')

onMounted(async () => {
  if (!auth.isLoggedIn) {
    router.replace({ name: 'login', query: { redirect: '/admin' } })
    return
  }
  await auth.refreshMe()
  if (!auth.isAdmin) {
    error.value = '需要管理员权限，请使用管理员账号登录'
    return
  }
  await load()
})

async function load() {
  error.value = ''
  try {
    users.value = await api.adminUsers(auth.token, q.value)
  } catch (e) {
    error.value = e.message
  }
}

async function toggleActive(u) {
  info.value = ''
  try {
    const updated = await api.adminUpdateUser(u.id, { is_active: !u.is_active }, auth.token)
    Object.assign(u, updated)
    info.value = `已${updated.is_active ? '启用' : '禁用'} ${u.username}`
  } catch (e) {
    error.value = e.message
  }
}

async function toggleAdmin(u) {
  info.value = ''
  try {
    const updated = await api.adminUpdateUser(u.id, { is_admin: !u.is_admin }, auth.token)
    Object.assign(u, updated)
    info.value = `已${updated.is_admin ? '设为' : '取消'}管理员：${u.username}`
  } catch (e) {
    error.value = e.message
  }
}

async function kick(u) {
  try {
    await api.adminKickUser(u.id, auth.token)
    info.value = `已强制 ${u.username} 下线`
  } catch (e) {
    error.value = e.message
  }
}

async function removeUser(u) {
  if (u.id === auth.user?.id) {
    error.value = '不能删除自己'
    return
  }
  if (!confirm(`确定永久删除用户「${u.username}」及其作品、评论等全部数据？此操作不可恢复。`)) {
    return
  }
  info.value = ''
  try {
    await api.adminDeleteUser(u.id, auth.token)
    users.value = users.value.filter((x) => x.id !== u.id)
    info.value = `已永久删除 ${u.username}`
  } catch (e) {
    error.value = e.message
  }
}

function formatDate(iso) {
  return new Date(iso).toLocaleString('zh-CN')
}
</script>

<template>
  <section class="container page">
    <header class="head">
      <h1>管理端</h1>
      <p class="muted">管理全部账号：启用/禁用、管理员、强制下线、永久删除。</p>
    </header>

    <form class="search" @submit.prevent="load">
      <input v-model="q" placeholder="搜用户名 / 邮箱 / 显示名" />
      <button class="btn btn-primary" type="submit">搜索</button>
    </form>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="info" class="muted">{{ info }}</p>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>显示名</th>
            <th>邮箱</th>
            <th>状态</th>
            <th>角色</th>
            <th>注册时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>{{ u.id }}</td>
            <td>{{ u.username }}</td>
            <td>{{ u.display_name }}</td>
            <td>{{ u.email }}</td>
            <td>{{ u.is_active ? '正常' : '禁用' }}</td>
            <td>{{ u.is_admin ? '管理员' : '用户' }}</td>
            <td>{{ formatDate(u.created_at) }}</td>
            <td class="ops">
              <button class="btn btn-ghost" type="button" @click="toggleActive(u)">
                {{ u.is_active ? '禁用' : '启用' }}
              </button>
              <button class="btn btn-ghost" type="button" @click="toggleAdmin(u)">
                {{ u.is_admin ? '取消管理' : '设管理' }}
              </button>
              <button class="btn btn-ghost" type="button" @click="kick(u)">踢下线</button>
              <button class="btn btn-ghost danger" type="button" @click="removeUser(u)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.page {
  padding-top: 2.4rem;
}
.head h1 {
  margin: 0;
  font-family: var(--font-brand);
  letter-spacing: 0.14em;
  font-weight: 400;
}
.search {
  display: flex;
  gap: 0.6rem;
  margin: 1.2rem 0;
}
.search input {
  flex: 1;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0.7rem 0.9rem;
  background: rgba(255, 255, 255, 0.7);
}
.table-wrap {
  overflow-x: auto;
  border-top: 1px solid var(--line);
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.92rem;
}
th,
td {
  text-align: left;
  padding: 0.75rem 0.5rem;
  border-bottom: 1px solid var(--line);
  vertical-align: top;
}
.ops {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.danger {
  color: #a33b2b;
}
</style>
