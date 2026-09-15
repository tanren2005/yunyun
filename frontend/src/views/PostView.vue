<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { useAuthStore } from '../stores/auth'
import MediaBlock from '../components/MediaBlock.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const post = ref(null)
const comments = ref([])
const loading = ref(true)
const error = ref('')
const commentText = ref('')
const commentError = ref('')
const submitting = ref(false)
const replyTo = ref(null)

const canDelete = computed(() => auth.isLoggedIn && post.value?.author?.id === auth.user?.id)

const roots = computed(() => comments.value.filter((c) => !c.parent_id))

function formatDate(iso) {
  return new Date(iso).toLocaleString('zh-CN')
}

function findComment(id) {
  return comments.value.find((c) => c.id === id)
}

/** 某条顶层评论下的全部回复（含对回复的回复），按时间排 */
function threadReplies(rootId) {
  const inThread = new Set([rootId])
  let grew = true
  while (grew) {
    grew = false
    for (const c of comments.value) {
      if (c.parent_id && inThread.has(c.parent_id) && !inThread.has(c.id)) {
        inThread.add(c.id)
        grew = true
      }
    }
  }
  inThread.delete(rootId)
  return comments.value
    .filter((c) => inThread.has(c.id))
    .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
}

function startReply(c) {
  if (!auth.isLoggedIn) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  replyTo.value = c
  commentText.value = ''
}

function cancelReply() {
  replyTo.value = null
}

async function load() {
  loading.value = true
  error.value = ''
  replyTo.value = null
  commentText.value = ''
  try {
    post.value = await api.post(route.params.id)
    comments.value = await api.comments(route.params.id)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function submitComment() {
  if (!auth.isLoggedIn) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  commentError.value = ''
  submitting.value = true
  try {
    const payload = { content: commentText.value }
    if (replyTo.value) payload.parent_id = replyTo.value.id
    const c = await api.createComment(route.params.id, payload, auth.token)
    comments.value.push(c)
    commentText.value = ''
    replyTo.value = null
    if (post.value) post.value.comment_count += 1
  } catch (e) {
    commentError.value = e.message
  } finally {
    submitting.value = false
  }
}

async function removePost() {
  if (!confirm('确定删除这篇作品？')) return
  await api.deletePost(post.value.id, auth.token)
  router.push('/')
}

onMounted(load)
watch(() => route.params.id, load)
</script>

<template>
  <section class="container page">
    <p v-if="loading" class="muted">加载中…</p>
    <p v-else-if="error" class="error">{{ error }}</p>
    <article v-else-if="post" class="article rise">
      <header class="head">
        <span class="tag">{{ post.category.name }}</span>
        <h1>{{ post.title }}</h1>
        <div class="meta muted">
          <span>{{ post.author.display_name }}</span>
          <span>{{ formatDate(post.created_at) }}</span>
          <span>{{ post.view_count }} 阅读</span>
        </div>
        <button v-if="canDelete" class="btn btn-ghost danger" type="button" @click="removePost">
          删除
        </button>
      </header>
      <div class="content">{{ post.content }}</div>
      <MediaBlock :files="post.attachments || []" />
    </article>

    <section v-if="post" class="comments">
      <h2>评论 · {{ comments.length }}</h2>
      <form class="composer" @submit.prevent="submitComment">
        <div class="field">
          <label for="comment">{{ replyTo ? `回复 ${replyTo.author.display_name}` : '写下你的想法' }}</label>
          <textarea
            id="comment"
            v-model="commentText"
            required
            maxlength="5000"
            :placeholder="replyTo ? '认真回一句…' : '像早期论坛那样，认真回一句。'"
          />
        </div>
        <div v-if="replyTo" class="reply-bar">
          <span class="muted">正在回复：{{ replyTo.content.slice(0, 48) }}{{ replyTo.content.length > 48 ? '…' : '' }}</span>
          <button class="btn btn-ghost" type="button" @click="cancelReply">取消回复</button>
        </div>
        <p v-if="commentError" class="error">{{ commentError }}</p>
        <button class="btn btn-primary" type="submit" :disabled="submitting">
          {{ submitting ? '发送中…' : replyTo ? '发表回复' : '发表评论' }}
        </button>
      </form>

      <div v-if="!comments.length" class="muted empty">还没有评论。</div>
      <ul v-else class="list">
        <li v-for="c in roots" :key="c.id" class="thread">
          <div class="c-head">
            <strong>{{ c.author.display_name }}</strong>
            <span class="muted">{{ formatDate(c.created_at) }}</span>
          </div>
          <p>{{ c.content }}</p>
          <button class="btn btn-ghost reply-btn" type="button" @click="startReply(c)">回复</button>
          <ul v-if="threadReplies(c.id).length" class="replies">
            <li v-for="r in threadReplies(c.id)" :key="r.id">
              <div class="c-head">
                <strong>{{ r.author.display_name }}</strong>
                <span class="muted">
                  回复 {{ findComment(r.parent_id)?.author?.display_name || '' }} · {{ formatDate(r.created_at) }}
                </span>
              </div>
              <p>{{ r.content }}</p>
              <button class="btn btn-ghost reply-btn" type="button" @click="startReply(r)">回复</button>
            </li>
          </ul>
        </li>
      </ul>
    </section>
  </section>
</template>

<style scoped>
.page {
  padding-top: 2.4rem;
  max-width: 760px;
}
.article {
  margin-bottom: 3rem;
}
.head h1 {
  margin: 0.7rem 0 0.8rem;
  font-size: clamp(1.8rem, 4vw, 2.6rem);
  letter-spacing: 0.06em;
  line-height: 1.35;
}
.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.9rem;
  font-size: 0.92rem;
  margin-bottom: 1rem;
}
.danger {
  margin-top: 0.6rem;
}
.content {
  white-space: pre-wrap;
  font-size: 1.08rem;
  line-height: 1.95;
  letter-spacing: 0.02em;
}
.comments h2 {
  margin: 0 0 1rem;
  font-size: 1.25rem;
  letter-spacing: 0.08em;
}
.composer {
  display: grid;
  gap: 0.8rem;
  margin-bottom: 1.6rem;
}
.reply-bar {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 0.6rem;
  align-items: center;
}
.list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.thread {
  padding: 1rem 0;
  border-top: 1px solid var(--line);
}
.c-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.35rem;
}
.list p {
  margin: 0;
  white-space: pre-wrap;
}
.reply-btn {
  margin-top: 0.45rem;
  padding: 0.25rem 0.55rem;
  font-size: 0.85rem;
}
.replies {
  list-style: none;
  margin: 0.7rem 0 0;
  padding: 0 0 0 1rem;
  border-left: 2px solid rgba(47, 107, 92, 0.25);
}
.replies li {
  padding: 0.75rem 0 0.15rem 0.85rem;
}
.empty {
  padding: 0.5rem 0 1rem;
}
</style>
