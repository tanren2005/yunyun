<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <footer class="footer">
    <div class="container inner">
      <p class="brand">云云</p>
      <p class="muted">云散 · 云说 · 诗歌 · 云笔 — 一处安静写字与互评的地方</p>
      <p class="contact muted">
        有疑问？
        <RouterLink to="/contact">联系我们</RouterLink>
        · 手机 17872364043 · QQ 389176505
      </p>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  border-top: 1px solid var(--line);
  padding: 2.2rem 0 2.8rem;
}
.inner {
  display: grid;
  gap: 0.35rem;
}
.brand {
  margin: 0;
  font-family: var(--font-brand);
  font-size: 1.35rem;
  letter-spacing: 0.16em;
}
.muted {
  margin: 0;
  font-size: 0.92rem;
}
.contact a {
  color: var(--leaf-deep);
  border-bottom: 1px solid rgba(47, 107, 92, 0.35);
}
</style>
