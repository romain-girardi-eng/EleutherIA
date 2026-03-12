import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    passWithNoTests: true,
  },
  resolve: {
    alias: {
      '@/cosmograph/style.module.css': path.resolve(
        __dirname,
        './node_modules/@cosmograph/cosmograph/cosmograph/style.module.css.js',
      ),
      '@': path.resolve(__dirname, './src'),
    },
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'three',
    ],
  },
  server: {
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
        secure: true,
      },
    },
  },
  build: {
    // Disable source maps for smaller production bundle
    sourcemap: false,
    // Optimize chunk size
    chunkSizeWarningLimit: 1000,
    // Enable minification optimizations
    minify: 'esbuild',
    // Target modern browsers for smaller bundle
    target: 'es2020',
    rollupOptions: {
      output: {
        // Manual chunks for better code splitting and caching
        manualChunks: {
          // Cosmograph GPU graph stack
          'cosmograph-vendor': [
            '@cosmograph/react',
            '@cosmograph/cosmograph',
            '@cosmograph/ui',
            '@cosmos.gl/graph',
            '@uwdata/mosaic-core',
            'apache-arrow',
            '@supabase/supabase-js',
          ],
          // Three.js - heavy 3D library (loaded on demand)
          'three-vendor': ['three'],
          // Separate charting/data visualization libraries
          'charts-vendor': ['d3', 'recharts'],
          // Separate animation libraries
          'animation-vendor': ['framer-motion'],
          // Separate React ecosystem
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // Separate markdown and UI libraries
          'ui-vendor': ['react-markdown', 'lucide-react', '@radix-ui/react-hover-card', '@radix-ui/react-slot'],
        },
      },
    },
  },
})
