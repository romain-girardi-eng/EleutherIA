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
      '@': path.resolve(__dirname, './src'),
    },
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'three',
      '@cosmograph/react',
    ],
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
          // Three.js - heavy 3D library (loaded on demand)
          'three-vendor': ['three'],
          // Cosmograph for KG visualization
          'cosmograph-vendor': ['@cosmograph/react'],
          // Separate charting/data visualization libraries
          'charts-vendor': ['d3', 'recharts'],
          // Separate animation libraries
          'animation-vendor': ['framer-motion', 'canvas-confetti'],
          // Separate React ecosystem
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // Separate markdown and UI libraries
          'ui-vendor': ['react-markdown', 'lucide-react', '@radix-ui/react-hover-card', '@radix-ui/react-slot'],
        },
      },
    },
  },
})
