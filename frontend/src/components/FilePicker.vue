<script setup>
import { markRaw } from 'vue'

defineProps({
  modelValue: { type: Array, default: () => [] },
  hint: { type: String, default: '可上传 Word、文本、PDF、图片或短视频' },
})

const emit = defineEmits(['update:modelValue', 'error'])

function formatSize(n) {
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(1)} MB`
}

function onChange(e) {
  const picked = Array.from(e.target.files || []).map((f) => markRaw(f))
  const empty = picked.filter((f) => !f.size)
  if (empty.length) {
    emit(
      'error',
      `「${empty.map((f) => f.name).join('、')}」大小为 0 字节（空文件）。请先在记事本/Word 里保存内容，再重新选择。`,
    )
  } else {
    emit('error', '')
  }
  // 仍允许列表展示，但提交时会拦截空文件
  emit('update:modelValue', picked)
  e.target.value = ''
}
</script>

<template>
  <div class="field">
    <label>附件</label>
    <input type="file" multiple @change="onChange" />
    <span class="hint">{{ hint }}</span>
    <ul v-if="modelValue.length" class="names">
      <li v-for="f in modelValue" :key="f.name + f.size + f.lastModified">
        {{ f.name }}
        <span :class="f.size ? 'size' : 'size bad'">{{ formatSize(f.size) }}</span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.hint {
  font-size: 0.82rem;
  color: var(--ink-soft);
}
.names {
  margin: 0.3rem 0 0;
  padding-left: 1.1rem;
  color: var(--ink-soft);
  font-size: 0.88rem;
}
.size {
  margin-left: 0.45rem;
  font-size: 0.82rem;
  color: var(--ink-soft);
}
.size.bad {
  color: #a33b2b;
  font-weight: 600;
}
</style>
