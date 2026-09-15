<script setup>
defineProps({
  post: { type: Object, required: true },
})

function formatDate(iso) {
  return new Date(iso).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <RouterLink :to="`/posts/${post.id}`" class="item rise">
    <div class="meta">
      <span class="tag">{{ post.category.name }}</span>
      <span class="muted">{{ formatDate(post.created_at) }}</span>
    </div>
    <h3>{{ post.title }}</h3>
    <p>{{ post.summary || '……' }}</p>
    <div class="foot">
      <span>{{ post.author.display_name }}</span>
      <span>{{ post.view_count }} 阅读 · {{ post.comment_count }} 评论</span>
    </div>
  </RouterLink>
</template>

<style scoped>
.item {
  display: grid;
  gap: 0.55rem;
  padding: 1.35rem 0;
  border-bottom: 1px solid var(--line);
  transition: padding-left 0.25s ease;
}

.item:hover {
  padding-left: 0.4rem;
}

.meta {
  display: flex;
  gap: 1rem;
  align-items: center;
  font-size: 0.85rem;
}

h3 {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 600;
  letter-spacing: 0.04em;
}

p {
  margin: 0;
  color: var(--ink-soft);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.foot {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  font-size: 0.88rem;
  color: var(--ink-soft);
}
</style>
