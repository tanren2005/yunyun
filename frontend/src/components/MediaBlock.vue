<script setup>
import { fileUrl } from '../api'

defineProps({
  files: { type: Array, default: () => [] },
})
</script>

<template>
  <div v-if="files.length" class="media">
    <template v-for="f in files" :key="f.id">
      <img v-if="f.kind === 'image'" :src="fileUrl(f.url)" :alt="f.original_name" />
      <video v-else-if="f.kind === 'video'" :src="fileUrl(f.url)" controls />
      <audio v-else-if="f.kind === 'audio'" :src="fileUrl(f.url)" controls />
      <a v-else class="doc" :href="fileUrl(f.url)" target="_blank" rel="noreferrer">
        下载附件 · {{ f.original_name }}
      </a>
    </template>
  </div>
</template>

<style scoped>
.media {
  display: grid;
  gap: 0.8rem;
  margin-top: 0.9rem;
}
img,
video {
  width: 100%;
  max-height: 420px;
  object-fit: contain;
  background: rgba(255, 255, 255, 0.4);
  border: 1px solid var(--line);
}
audio {
  width: 100%;
}
.doc {
  color: var(--leaf-deep);
  border-bottom: 1px solid rgba(47, 107, 92, 0.35);
  width: fit-content;
}
</style>
