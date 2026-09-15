<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import SiteHeader from './components/SiteHeader.vue'
import SiteFooter from './components/SiteFooter.vue'

const auth = useAuthStore()
onMounted(() => auth.refreshMe())
</script>

<template>
  <div class="shell">
    <SiteHeader />
    <main class="main">
      <RouterView />
    </main>
    <SiteFooter />
  </div>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  display: grid;
  grid-template-rows: auto 1fr auto;
}
.main {
  padding-bottom: 4rem;
}
</style>
