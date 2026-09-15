<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useAuthStore } from '../stores/auth'
import FilePicker from '../components/FilePicker.vue'
import MediaBlock from '../components/MediaBlock.vue'

const auth = useAuthStore()
const router = useRouter()
const items = ref([])
const form = ref({ book_title: '', book_author: '', content: '' })
const files = ref([])
const error = ref('')
const submitting = ref(false)
const openId = ref(null)
const comments = ref({})
const draft = ref({})
const replyTo = ref({})

onMounted(async () => {
  items.value = await api.books()
})

async function publish() {
  if (!auth.isLoggedIn) {
    router.push({ name: 'login', query: { redirect: '/club' } })
    return
  }
  error.value = ''
  submitting.value = true
  try {
    const row = await api.createBook(form.value, auth.token)
    if (files.value.length) {
      const up = await api.upload('books', row.id, files.value, auth.token)
      row.attachments = up.files
    }
    items.value.unshift(row)
    form.value = { book_title: '', book_author: '', content: '' }
    files.value = []
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}

async function toggle(item) {
  if (openId.value === item.id) {
    openId.value = null
    return
  }
  openId.value = item.id
  comments.value[item.id] = await api.bookComments(item.id)
}

function startReply(item, c) {
  if (!auth.isLoggedIn) {
    router.push({ name: 'login', query: { redirect: '/club' } })
    return
  }
  replyTo.value = { ...replyTo.value, [item.id]: c }
}

function cancelReply(itemId) {
  const next = { ...replyTo.value }
  delete next[itemId]
  replyTo.value = next
}

async function reply(item) {
  const text = (draft.value[item.id] || '').trim()
  if (!text) return
  if (!auth.isLoggedIn) {
    router.push({ name: 'login', query: { redirect: '/club' } })
    return
  }
  const payload = { content: text }
  const parent = replyTo.value[item.id]
  if (parent) payload.parent_id = parent.id
  const c = await api.createBookComment(item.id, payload, auth.token)
  comments.value[item.id] = [...(comments.value[item.id] || []), c]
  item.comment_count += 1
  draft.value[item.id] = ''
  cancelReply(item.id)
}

async function remove(item) {
  if (!confirm('删除这篇读书分享？')) return
  await api.deleteBook(item.id, auth.token)
  items.value = items.value.filter((x) => x.id !== item.id)
}

function formatDate(iso) {
  return new Date(iso).toLocaleString('zh-CN')
}

function findAuthor(list, parentId) {
  return list?.find((x) => x.id === parentId)?.author?.display_name || ''
}
</script>

<template>
  <section class="container page">
    <header class="head rise">
      <p class="tag">云友会</p>
      <h1>把一本书递给别人</h1>
      <p class="muted">分享书名、作者与读后感。封面图、摘录文件都可以附上。</p>
    </header>

    <form class="form rise" @submit.prevent="publish">
      <div class="row">
        <div class="field">
          <label>书名</label>
          <input v-model="form.book_title" required maxlength="200" placeholder="例如：边城" />
        </div>
        <div class="field">
          <label>作者</label>
          <input v-model="form.book_author" maxlength="120" placeholder="例如：沈从文" />
        </div>
      </div>
      <div class="field">
        <label>分享</label>
        <textarea v-model="form.content" maxlength="20000" placeholder="为何想把这本书交给读友…" />
      </div>
      <FilePicker v-model="files" hint="封面、笔记扫描件、摘录 Word 等" />
      <p v-if="error" class="error">{{ error }}</p>
      <button class="btn btn-primary" type="submit" :disabled="submitting">
        {{ submitting ? '发布中…' : '分享给读友' }}
      </button>
    </form>

    <article v-for="item in items" :key="item.id" class="card">
      <div class="who">
        <span class="tag">书</span>
        <span class="muted">{{ item.author.display_name }} · {{ formatDate(item.created_at) }}</span>
      </div>
      <h2>{{ item.book_title }}</h2>
      <p v-if="item.book_author" class="muted">{{ item.book_author }} 著</p>
      <p class="text">{{ item.content }}</p>
      <MediaBlock :files="item.attachments" />
      <div class="foot">
        <button class="btn btn-ghost" type="button" @click="toggle(item)">
          {{ openId === item.id ? '收起讨论' : `讨论 · ${item.comment_count}` }}
        </button>
        <button
          v-if="auth.user?.id === item.author.id"
          class="btn btn-ghost"
          type="button"
          @click="remove(item)"
        >
          删除
        </button>
      </div>
      <div v-if="openId === item.id" class="talk">
        <div v-for="c in comments[item.id] || []" :key="c.id" class="c-item" :class="{ nested: c.parent_id }">
          <div class="c-head">
            <strong>{{ c.author.display_name }}</strong>
            <span class="muted">
              <template v-if="c.parent_id">回复 {{ findAuthor(comments[item.id], c.parent_id) }} · </template>
              {{ formatDate(c.created_at) }}
            </span>
          </div>
          <p>{{ c.content }}</p>
          <button class="btn btn-ghost tiny" type="button" @click="startReply(item, c)">回复</button>
        </div>
        <form class="reply" @submit.prevent="reply(item)">
          <input
            v-model="draft[item.id]"
            :placeholder="replyTo[item.id] ? `回复 ${replyTo[item.id].author.display_name}` : '写下你的读法'"
          />
          <button v-if="replyTo[item.id]" class="btn btn-ghost" type="button" @click="cancelReply(item.id)">取消</button>
          <button class="btn btn-ghost" type="submit">发送</button>
        </form>
      </div>
    </article>
  </section>
</template>

<style scoped>
.page {
  padding-top: 2.4rem;
  max-width: 760px;
}
.head h1 {
  margin: 0.35rem 0;
  font-family: var(--font-brand);
  font-size: 2.2rem;
  letter-spacing: 0.12em;
  font-weight: 400;
}
.form,
.card {
  display: grid;
  gap: 0.75rem;
  padding: 1.2rem 0;
  border-top: 1px solid var(--line);
}
.row {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 1rem;
}
h2 {
  margin: 0;
  letter-spacing: 0.04em;
}
.text {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.85;
}
.who,
.foot,
.reply {
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
  align-items: center;
}
.talk {
  display: grid;
  gap: 0.5rem;
}
.c-item {
  padding: 0.4rem 0;
  border-top: 1px dashed var(--line);
}
.c-item.nested {
  margin-left: 0.9rem;
  padding-left: 0.75rem;
  border-left: 2px solid rgba(47, 107, 92, 0.22);
}
.c-head {
  display: flex;
  justify-content: space-between;
  gap: 0.6rem;
  font-size: 0.9rem;
}
.c-item p {
  margin: 0.25rem 0;
  white-space: pre-wrap;
}
.tiny {
  padding: 0.2rem 0.45rem;
  font-size: 0.82rem;
}
.reply input {
  flex: 1;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0.55rem 0.8rem;
}
@media (max-width: 640px) {
  .row {
    grid-template-columns: 1fr;
  }
}
</style>
