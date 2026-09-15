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
const content = ref('')
const files = ref([])
const error = ref('')
const submitting = ref(false)
const openId = ref(null)
const comments = ref({})
const commentDraft = ref({})
const replyTo = ref({})

onMounted(load)

async function load() {
  items.value = await api.moments()
}

async function publish() {
  if (!auth.isLoggedIn) {
    router.push({ name: 'login', query: { redirect: '/moments' } })
    return
  }
  error.value = ''
  if (!content.value.trim() && !files.value.length) {
    error.value = '写一句，或选一个文件再发布'
    return
  }
  submitting.value = true
  try {
    const row = await api.createMoment({ content: content.value }, auth.token)
    if (files.value.length) {
      const up = await api.upload('moments', row.id, files.value, auth.token)
      row.attachments = up.files
    }
    items.value.unshift(row)
    content.value = ''
    files.value = []
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}

async function remove(item) {
  const asAdmin = auth.isAdmin && auth.user?.id !== item.author.id
  if (!confirm(asAdmin ? '以管理员身份删除这条公开动态？' : '删除这条公开动态？')) return
  await api.deleteMoment(item.id, auth.token)
  items.value = items.value.filter((x) => x.id !== item.id)
}

function canManage(item) {
  return auth.isAdmin || auth.user?.id === item.author.id
}

function canDeleteComment(c) {
  return auth.isLoggedIn && (auth.isAdmin || c.author?.id === auth.user?.id)
}

async function removeComment(item, c) {
  if (!confirm('确定删除这条回应？')) return
  await api.deleteMomentComment(item.id, c.id, auth.token)
  const list = comments.value[item.id] || []
  const drop = new Set([c.id])
  let grew = true
  while (grew) {
    grew = false
    for (const x of list) {
      if (x.parent_id && drop.has(x.parent_id) && !drop.has(x.id)) {
        drop.add(x.id)
        grew = true
      }
    }
  }
  comments.value[item.id] = list.filter((x) => !drop.has(x.id))
  item.comment_count = Math.max(0, item.comment_count - drop.size)
}

async function toggle(item) {
  if (openId.value === item.id) {
    openId.value = null
    return
  }
  openId.value = item.id
  comments.value[item.id] = await api.momentComments(item.id)
}

function startReply(item, c) {
  if (!auth.isLoggedIn) {
    router.push({ name: 'login', query: { redirect: '/moments' } })
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
  const text = (commentDraft.value[item.id] || '').trim()
  if (!text) return
  if (!auth.isLoggedIn) {
    router.push({ name: 'login', query: { redirect: '/moments' } })
    return
  }
  const payload = { content: text }
  const parent = replyTo.value[item.id]
  if (parent) payload.parent_id = parent.id
  const c = await api.createMomentComment(item.id, payload, auth.token)
  comments.value[item.id] = [...(comments.value[item.id] || []), c]
  item.comment_count += 1
  commentDraft.value[item.id] = ''
  cancelReply(item.id)
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
      <p class="tag">云间</p>
      <h1>公开动态</h1>
      <p class="muted">像朋友圈，却没有分组：站上每一位都是读友，动态对所有人可见。</p>
    </header>

    <form class="composer rise" @submit.prevent="publish">
      <div class="field">
        <label for="moment">此时想说</label>
        <textarea id="moment" v-model="content" maxlength="5000" placeholder="一句心情、一段见闻，或配上文件与短视频。" />
      </div>
      <FilePicker v-model="files" hint="图片、短视频、音频、Word 或文本都可以" />
      <p v-if="error" class="error">{{ error }}</p>
      <button class="btn btn-primary" type="submit" :disabled="submitting">
        {{ submitting ? '发布中…' : '发到云间' }}
      </button>
    </form>

    <article v-for="item in items" :key="item.id" class="card">
      <div class="who">
        <strong>{{ item.author.display_name }}</strong>
        <span class="muted">{{ formatDate(item.created_at) }}</span>
      </div>
      <p class="text">{{ item.content }}</p>
      <MediaBlock :files="item.attachments" />
      <div class="foot">
        <button class="btn btn-ghost" type="button" @click="toggle(item)">
          {{ openId === item.id ? '收起回应' : `回应 · ${item.comment_count}` }}
        </button>
        <button
          v-if="canManage(item)"
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
          <div class="c-actions">
            <button class="btn btn-ghost tiny" type="button" @click="startReply(item, c)">回复</button>
            <button
              v-if="canDeleteComment(c)"
              class="btn btn-ghost tiny danger"
              type="button"
              @click="removeComment(item, c)"
            >
              删除
            </button>
          </div>
        </div>
        <form class="reply" @submit.prevent="reply(item)">
          <input
            v-model="commentDraft[item.id]"
            :placeholder="replyTo[item.id] ? `回复 ${replyTo[item.id].author.display_name}` : '公开回应一句'"
            maxlength="5000"
          />
          <button v-if="replyTo[item.id]" class="btn btn-ghost" type="button" @click="cancelReply(item.id)">取消</button>
          <button class="btn btn-ghost" type="submit">发送</button>
        </form>
      </div>
    </article>
    <p v-if="!items.length" class="muted">云间还安静，来发第一条吧。</p>
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
.composer,
.card {
  display: grid;
  gap: 0.8rem;
  padding: 1.2rem 0;
  border-top: 1px solid var(--line);
}
.who,
.foot,
.reply {
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
  align-items: center;
}
.text {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.8;
}
.talk {
  display: grid;
  gap: 0.55rem;
  padding-left: 0.2rem;
}
.c-item {
  padding: 0.35rem 0;
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
.c-actions {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
}
.danger {
  color: #a33b2b;
}
.reply input {
  flex: 1;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0.55rem 0.8rem;
  background: rgba(255, 255, 255, 0.7);
}
</style>
