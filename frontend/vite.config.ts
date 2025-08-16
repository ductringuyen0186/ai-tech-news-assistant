import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      // Force Rollup to use JavaScript fallback instead of native binaries
      external: (id) => {
        // Skip external native binary dependencies that cause CI issues
        if (id.includes('@rollup/rollup-') && id.includes('-gnu')) {
          return true;
        }
        return false;
      },
    },
  },
  // Environment-specific configurations
  define: {
    // Force disable native Rollup in CI
    'process.env.ROLLUP_NO_NATIVE': JSON.stringify(process.env.ROLLUP_NO_NATIVE || ''),
  },
})
