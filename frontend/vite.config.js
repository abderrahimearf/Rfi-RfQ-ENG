import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Cette règle redirige tous les appels API (ex: /api/templates-files)
      // vers votre backend Flask sur le port 5000.
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      // Cette règle est cruciale. Elle redirige la tentative de connexion
      // de Socket.IO vers le serveur WebSocket du backend.
      '/socket.io': {
        target: 'http://localhost:5000',
        ws: true, // Indique qu'il s'agit d'une connexion WebSocket
         changeOrigin: true
      },
    }
  }
})
