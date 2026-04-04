import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import dayjs from 'dayjs'

// https://vite.dev/config/
export default defineConfig({
  base: process.env.MJS_TIERMAKER_BASE_URL || './',
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  define: {
    __BUILD_TIME__: JSON.stringify(dayjs().format('YYYY-MM-DD'))
  }
})
