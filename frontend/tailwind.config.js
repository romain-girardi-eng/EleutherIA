/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f3f7f5',
          100: '#e2ebe7',
          200: '#c5d7cf',
          300: '#a8c3b7',
          400: '#8baf9f',
          500: '#769687',
          600: '#769687',
          700: '#5d7769',
          800: '#475a4f',
          900: '#313d36',
        },
        academic: {
          bg: '#fafaf9',
          paper: '#ffffff',
          text: '#1c1917',
          muted: '#78716c',
          border: '#e7e5e4',
        },
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        muted: {
          DEFAULT: '#78716c',
          foreground: '#1c1917',
        },
        accent: {
          DEFAULT: '#e7e5e4',
          foreground: '#1c1917',
        },
        destructive: {
          DEFAULT: '#ef4444',
          foreground: '#ffffff',
        },
        secondary: {
          DEFAULT: '#f3f4f6',
          foreground: '#1c1917',
        },
        ring: '#769687',
        input: '#e7e5e4',
      },
      fontFamily: {
        serif: ['Georgia', 'Palatino', 'Times New Roman', 'serif'],
      },
      animation: {
        shine: "shine var(--duration) infinite linear",
      },
      keyframes: {
        shine: {
          "0%": {
            "background-position": "0% 0%",
          },
          "50%": {
            "background-position": "100% 100%",
          },
          to: {
            "background-position": "0% 0%",
          },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
