import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:14200',
      '/poc': 'http://127.0.0.1:14200',
      '/business': {
        target: 'http://127.0.0.1:14202',
        rewrite: (path: string) => path.replace(/^\/business(?=\/)/, ''),
      },
    },
  },
})
