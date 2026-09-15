<script setup>
</script>

<template>
  <section class="container page">
    <header class="head rise">
      <p class="tag">联系</p>
      <h1>有疑问，联系我们</h1>
      <p class="muted">注册、发帖或使用上遇到问题，欢迎通过下列方式联系站务。</p>
    </header>

    <div class="grid rise">
      <div class="item">
        <h2>手机</h2>
        <a class="value" href="tel:17872364043">17872364043</a>
      </div>
      <div class="item">
        <h2>QQ</h2>
        <p class="value">389176505</p>
      </div>
      <div class="item wide">
        <h2>微信</h2>
        <img class="qr" src="/wechat-qr.png" alt="微信二维码" />
      </div>
    </div>
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
  font-size: 2.2rem;
  letter-spacing: 0.12em;
  font-weight: 400;
}
.grid {
  display: grid;
  gap: 1.2rem;
  margin-top: 1.5rem;
  border-top: 1px solid var(--line);
  padding-top: 1.4rem;
}
.item {
  display: grid;
  gap: 0.35rem;
}
.item h2 {
  margin: 0;
  font-size: 1rem;
  letter-spacing: 0.08em;
  color: var(--ink-soft);
}
.value {
  margin: 0;
  font-size: 1.35rem;
  color: var(--leaf-deep);
}
.qr {
  margin-top: 0.35rem;
  width: min(100%, 260px);
  border: 1px solid var(--line);
  background: #fff;
}
</style>
