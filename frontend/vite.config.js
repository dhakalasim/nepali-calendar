import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In Docker the API is reachable as http://backend:8000; locally it's localhost.
const apiTarget = process.env.VITE_API_PROXY || 'http://localhost:8000'
// PORT is set in docker-compose so the container port matches the host port.
const port = Number(process.env.PORT) || 5173

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port,
    strictPort: true,
    proxy: {
      '/api': { target: apiTarget, changeOrigin: true },
    },
  },
})
