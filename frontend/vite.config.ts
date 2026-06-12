import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

const vendorGroups: Array<[string, string[]]> = [
  [
    'cosmograph-vendor',
    [
      '@cosmograph/react',
      '@cosmograph/cosmograph',
      '@cosmograph/ui',
      '@cosmos.gl/graph',
      '@uwdata/mosaic-core',
      'apache-arrow',
      '@supabase/supabase-js',
    ],
  ],
  ['three-vendor', ['three']],
  ['charts-vendor', ['d3', 'recharts']],
  ['animation-vendor', ['framer-motion']],
  ['react-vendor', ['react', 'react-dom', 'react-router-dom']],
  [
    'ui-vendor',
    [
      'react-markdown',
      'lucide-react',
      '@radix-ui/react-hover-card',
      '@radix-ui/react-slot',
      'class-variance-authority',
      'clsx',
      'tailwind-merge',
    ],
  ],
]

function matchesPackage(modulePath: string, packageName: string): boolean {
  return (
    modulePath === packageName ||
    modulePath.startsWith(`${packageName}/`) ||
    (packageName === 'd3' && modulePath.startsWith('d3-'))
  )
}

function manualChunks(id: string): string | undefined {
  if (id.includes('vite/preload-helper')) return 'preload-helper'

  const [, modulePath] = id.split('node_modules/')
  if (!modulePath) return undefined

  for (const [chunkName, packages] of vendorGroups) {
    if (packages.some((packageName) => matchesPackage(modulePath, packageName))) {
      return chunkName
    }
  }

  return undefined
}

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
    // Modulepreload only covers the entry's STATIC import graph (react/ui
    // vendors needed on every page) plus runtime preloading of a lazy
    // chunk's own deps. Heavy route-only chunks (cosmograph, three) are
    // lazy and never eagerly hinted. Disabling this created a 3-hop
    // network waterfall on every cold load.
    modulePreload: true,
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
        // Manual chunks for better code splitting and caching.
        manualChunks,
      },
    },
  },
})
