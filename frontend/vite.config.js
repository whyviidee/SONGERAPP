import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8888',
      '/stream': 'http://127.0.0.1:8888',
      '/setup': 'http://127.0.0.1:8888',
      '/callback': 'http://127.0.0.1:8888',
      '/disconnect': 'http://127.0.0.1:8888',
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
