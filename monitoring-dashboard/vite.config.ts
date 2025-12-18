import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    // Output directly to orchestrator api/static folder
    outDir: '../src/casare_rpa/infrastructure/orchestrator/api/static',
    emptyOutDir: true,
    // Generate sourcemaps for debugging
    sourcemap: false,
  },
  server: {
    port: 5173,
    // Proxy API calls to local orchestrator during development
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
      },
    },
  },
})
