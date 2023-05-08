import react from '@vitejs/plugin-react';
import * as path from 'path';
import { defineConfig } from 'vite';

// https://vitejs.dev/config/
export default defineConfig({
  base: '/',
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000/api/v1/',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  css: {
    preprocessorOptions: {
      less: {
        javascriptEnabled: true,
        additionalData: '@root-entry-name: default;',
      },
    },
  },
  resolve: {
    alias: [
      { find: 'ui', replacement: path.resolve(__dirname, 'src/ui') },
      { find: 'utils', replacement: path.resolve(__dirname, 'src/utils') },
      {
        find: 'services',
        replacement: path.resolve(__dirname, 'src/services'),
      },
      { find: 'core', replacement: path.resolve(__dirname, 'src/core') },
      { find: 'utils', replacement: path.resolve(__dirname, 'src/utils') },
      { find: /^~/, replacement: '' },
    ],
  },
  build: {
    rollupOptions: {
      output: {
        entryFileNames: 'static/[name]-[hash].js',
        chunkFileNames: 'static/[name]-[hash].js',
        assetFileNames: 'static/[name]-[hash][extname]',
      },
    },
  },
});
