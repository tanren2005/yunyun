<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useAuthStore } from '../stores/auth'
import FilePicker from '../components/FilePicker.vue'

const auth = useAuthStore()
const router = useRouter()

const categories = ref([])
const title = ref('')
const categoryId = ref(null)
const summary = ref('')
const content = ref('')
const files = ref([])
const error = ref('')
const submitting = ref(false)

onMounted(async () => {
  categories.value = await api.categories()
  if (categories.value.length) categoryId.value = categories.value[0].id
})

async function submit() {
  error.value = ''
  if (!content.value.trim() && !files.value.length) {
    error.value = '请写下正文，或上传 Word / 文本文件'
    return
  }
  const emptyFiles = files.value.filter((f) => !f.size)
  if (emptyFiles.length) {
    error.value = `「${emptyFiles.map((f) => f.name).join('、')}」大小为 0 字节。请先保存文件内容后再发布。`
    return
  }
  submitting.value = true
  try {
    const post = await api.createPost(
      {
        title: title.value,
        content: content.value,
        summary: summary.value,
        category_id: Number(categoryId.value),
      },
      auth.token,
    )
    if (files.value.length) {
      await api.upload('posts', post.id, files.value, auth.token)
    }
    router.push(`/posts/${post.id}`)
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="container page">
    <header class="head rise">
      <h1>写一篇</h1>
      <p class="muted">云散、云说、诗歌或云笔。可手打全文，也可上传 Word、文本或 PDF。</p>
    </header>

    <form class="form rise" @submit.prevent="submit">
      <div class="field">
        <label for="title">标题</label>
        <input id="title" v-model="title" required maxlength="200" placeholder="给文字一个名字" />
      </div>
      <div class="row">
        <div class="field">
          <label for="category">栏目</label>
          <select id="category" v-model="categoryId" required>
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div class="field">
          <label for="summary">摘要（可选）</label>
          <input id="summary" v-model="summary" maxlength="300" placeholder="列表里显示的一两句" />
        </div>
      </div>
      <div class="field">
        <label for="content">正文</label>
        <textarea id="content" v-model="content" maxlength="100000" placeholder="在这里写下全文，或留空后上传文件自动读入 Word/文本。" />
      </div>
      <FilePicker v-model="files" @error="error = $event" />
      <p v-if="error" class="error">{{ error }}</p>
      <button class="btn btn-primary" type="submit" :disabled="submitting">
        {{ submitting ? '发布中…' : '发布' }}
      </button>
    </form>
  </section>
</template>

<style scoped>
.page {
  padding-top: 2.4rem;
  max-width: 760px;
}
.head h1 {
  margin: 0;
  font-family: var(--font-brand);
  font-size: 2.4rem;
  letter-spacing: 0.16em;
  font-weight: 400;
}
.head p {
  margin: 0.4rem 0 1.4rem;
}
.form {
  display: grid;
  gap: 1rem;
}
.row {
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: 1rem;
}
@media (max-width: 640px) {
  .row {
    grid-template-columns: 1fr;
  }
}
</style>
