import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    // 允许用公网 IP / 域名访问，避免 Host 校验拦掉
    allowedHosts: true,
    proxy: {
      // 容器内 localhost 不是 backend，要走 compose 服务名
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/uploads': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})
