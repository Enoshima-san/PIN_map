import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Конфигурация Vite для локальной разработки фронта.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // В dev-режиме запросы /api и /media проксируются на Django, чтобы фронт обращался к одному origin.
    // Для production адреса и правила прокси должны задаваться конфигурацией сервера, а не этим dev-настройками.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/media': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
