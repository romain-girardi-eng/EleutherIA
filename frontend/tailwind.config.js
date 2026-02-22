/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  corePlugins: {
    preflight: true,
  },
  theme: {
    extend: {
      colors: {
        // Primary colors - warm amber-orange
        primary: {
          50: '#fff7ed',
          100: '#ffedd5',
          200: '#fed7aa',
          300: '#fdba74',
          400: '#fb923c',
          500: '#f97316',
          600: '#ea580c',
          700: '#c2410c',
          800: '#9a3412',
          900: '#7c2d12',
        },
        // Accent colors - ancient red
        accent: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#b61b21',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
        // Academic theme colors
        academic: {
          bg: '#fafaf9',
          paper: '#ffffff',
          text: '#1c1917',
          muted: '#78716c',
          border: '#e7e5e4',
          light: '#f5f5f4',
          dark: '#292524',
        },
        // Semantic colors
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
        danger: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
        // Orange accent — warm burnt-orange palette
        orange: {
          50: '#fff8f0',
          100: '#ffedd8',
          200: '#fed7aa',
          300: '#fdba74',
          400: '#fb923c',
          500: '#f97316',
          600: '#ea580c',
          700: '#c2410c',
          800: '#9a3412',
          900: '#7c2d12',
        },
        // Parchment — warm cream for scholarly backgrounds
        parchment: {
          50: '#fcf9f4',
          100: '#f8f3eb',
          200: '#f3ece0',
          300: '#fde8c8',
          400: '#fbd9a6',
          500: '#f8c980',
          600: '#f0b050',
          700: '#d48c2a',
          800: '#a86a1a',
          900: '#7c4d0f',
        },
        // CSS Variables
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        muted: {
          DEFAULT: '#78716c',
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
        ring: '#f97316',
        input: '#e7e5e4',
        brand: 'hsl(var(--brand))',
        'brand-foreground': 'hsl(var(--brand-foreground))',
      },
      fontFamily: {
        // Display headings — Instrument Serif (elegant academic serif)
        display: [
          '"Instrument Serif"',
          'Georgia',
          '"Times New Roman"',
          'serif',
        ],
        // Body text — DM Sans (clean modern sans)
        body: [
          '"DM Sans"',
          'system-ui',
          '-apple-system',
          'sans-serif',
        ],
        // UI elements - modern system fonts
        sans: [
          '"DM Sans"',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          '"Helvetica Neue"',
          'Arial',
          'sans-serif',
        ],
        // Body text - academic serif stack
        serif: [
          'Georgia',
          '"Times New Roman"',
          'Times',
          'serif',
        ],
        // Ancient Greek/Latin texts - classical serif stack
        ancient: [
          '"Palatino Linotype"',
          '"Book Antiqua"',
          'Palatino',
          'Georgia',
          'serif',
        ],
        // Monospace for code/data
        mono: [
          'ui-monospace',
          'SFMono-Regular',
          '"SF Mono"',
          'Menlo',
          'Consolas',
          '"Liberation Mono"',
          '"Courier New"',
          'monospace',
        ],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.875rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.75rem' }],
        '5xl': ['3rem', { lineHeight: '3.5rem' }],
        '6xl': ['3.75rem', { lineHeight: '4.25rem' }],
        '7xl': ['4.5rem', { lineHeight: '5rem' }],
        '8xl': ['6rem', { lineHeight: '6.5rem' }],
        '9xl': ['8rem', { lineHeight: '8.5rem' }],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
        '144': '36rem',
      },
      maxWidth: {
        '8xl': '88rem',
        '9xl': '96rem',
      },
      animation: {
        // Existing animations
        shine: "shine var(--duration) infinite linear",
        shimmer: "shimmer 2s infinite linear",
        // Aurora animation
        aurora: "aurora 60s linear infinite",
        // Fade animations
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'fade-out': 'fadeOut 0.5s ease-in-out',
        // Slide animations
        'slide-in': 'slideIn 0.3s ease-out',
        'slide-out': 'slideOut 0.3s ease-in',
        'slide-in-left': 'slideInLeft 0.3s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'slide-in-up': 'slideInUp 0.3s ease-out',
        'slide-in-down': 'slideInDown 0.3s ease-out',
        // Scale animations
        'scale-in': 'scaleIn 0.2s ease-out',
        'scale-out': 'scaleOut 0.2s ease-in',
        'bounce-in': 'bounceIn 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55)',
        // Loop animations
        'spin-slow': 'spin 3s linear infinite',
        'bounce-slow': 'bounce 2s infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'wiggle': 'wiggle 1s ease-in-out infinite',
        'appear-zoom': 'appear-zoom 0.5s ease-out forwards',
        // Premium background animations
        'orb-drift-1': 'orbDrift1 30s ease-in-out infinite',
        'orb-drift-2': 'orbDrift2 35s ease-in-out infinite',
        'orb-drift-3': 'orbDrift3 40s ease-in-out infinite',
        'vignette-breathe': 'vignetteBreathe 12s ease-in-out infinite',
        'light-sweep': 'lightSweep 25s ease-in-out infinite',
        'grid-spotlight': 'gridSpotlight 20s ease-in-out infinite',
        'contour-pulse': 'contourPulse 16s ease-in-out infinite',
        'letter-drift': 'letterDrift 24s ease-in-out infinite',
        'grid-fade': 'gridFade 10s ease-in-out infinite',
        'dust-float': 'dustFloat 20s linear infinite',
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
        shimmer: {
          "0%": {
            transform: "translateX(-100%)",
          },
          "100%": {
            transform: "translateX(100%)",
          },
        },
        aurora: {
          from: {
            backgroundPosition: "50% 50%, 50% 50%",
          },
          to: {
            backgroundPosition: "350% 50%, 350% 50%",
          },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeOut: {
          '0%': { opacity: '1' },
          '100%': { opacity: '0' },
        },
        slideIn: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideOut: {
          '0%': { transform: 'translateY(0)', opacity: '1' },
          '100%': { transform: 'translateY(-10px)', opacity: '0' },
        },
        slideInLeft: {
          '0%': { transform: 'translateX(-100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        slideInRight: {
          '0%': { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        slideInUp: {
          '0%': { transform: 'translateY(100%)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideInDown: {
          '0%': { transform: 'translateY(-100%)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        scaleOut: {
          '0%': { transform: 'scale(1)', opacity: '1' },
          '100%': { transform: 'scale(0.95)', opacity: '0' },
        },
        bounceIn: {
          '0%': { transform: 'scale(0.3)', opacity: '0' },
          '50%': { transform: 'scale(1.05)' },
          '70%': { transform: 'scale(0.9)' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        wiggle: {
          '0%, 100%': { transform: 'rotate(-3deg)' },
          '50%': { transform: 'rotate(3deg)' },
        },
        'appear-zoom': {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        // Premium background: drifting orbs with visible travel
        orbDrift1: {
          '0%': { transform: 'translate(0, 0) scale(1)' },
          '25%': { transform: 'translate(-25%, 30%) scale(1.15)' },
          '50%': { transform: 'translate(-10%, 50%) scale(0.9)' },
          '75%': { transform: 'translate(10%, 25%) scale(1.1)' },
          '100%': { transform: 'translate(0, 0) scale(1)' },
        },
        orbDrift2: {
          '0%': { transform: 'translate(0, 0) scale(1)' },
          '30%': { transform: 'translate(30%, -35%) scale(1.2)' },
          '60%': { transform: 'translate(15%, -15%) scale(0.85)' },
          '100%': { transform: 'translate(0, 0) scale(1)' },
        },
        orbDrift3: {
          '0%': { transform: 'translate(0, 0) scale(1)' },
          '20%': { transform: 'translate(-20%, 15%) scale(1.1)' },
          '50%': { transform: 'translate(15%, -25%) scale(0.9)' },
          '75%': { transform: 'translate(-8%, 10%) scale(1.15)' },
          '100%': { transform: 'translate(0, 0) scale(1)' },
        },
        vignetteBreathe: {
          '0%, 100%': { opacity: '0.5' },
          '50%': { opacity: '1' },
        },
        // Sweeping light beam — sunlight / scanner
        lightSweep: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(200%)' },
        },
        // Spotlight wandering over dot grid
        gridSpotlight: {
          '0%': { top: '10%', left: '10%' },
          '25%': { top: '60%', left: '70%' },
          '50%': { top: '30%', left: '50%' },
          '75%': { top: '70%', left: '20%' },
          '100%': { top: '10%', left: '10%' },
        },
        // Concentric rings pulse — expand and fade
        contourPulse: {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.5' },
          '50%': { transform: 'scale(1.08)', opacity: '0.9' },
        },
        // Philosophical terms — gentle drift + breathe
        letterDrift: {
          '0%': { transform: 'translateY(0)', opacity: '0.15' },
          '25%': { opacity: '1' },
          '50%': { transform: 'translateY(-20px)', opacity: '1' },
          '75%': { opacity: '1' },
          '100%': { transform: 'translateY(0)', opacity: '0.15' },
        },
        // Annotation crosses fade in/out
        gridFade: {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '1' },
        },
        // Dust motes floating upward
        dustFloat: {
          '0%': { transform: 'translateY(0) translateX(0)', opacity: '0' },
          '10%': { opacity: '0.6' },
          '50%': { transform: 'translateY(-50vh) translateX(20px)', opacity: '0.4' },
          '90%': { opacity: '0.2' },
          '100%': { transform: 'translateY(-110vh) translateX(-10px)', opacity: '0' },
        },
      },
      boxShadow: {
        // Layered shadows — contact + depth + ambient for realistic diffusion
        'xs': '0 1px 2px 0 rgb(0 0 0 / 0.04), 0 0 1px 0 rgb(0 0 0 / 0.06)',
        'sm': '0 1px 2px 0 rgb(0 0 0 / 0.06), 0 2px 6px -1px rgb(0 0 0 / 0.06), 0 0 1px 0 rgb(0 0 0 / 0.04)',
        DEFAULT: '0 2px 4px -1px rgb(0 0 0 / 0.06), 0 4px 10px -2px rgb(0 0 0 / 0.06), 0 0 2px 0 rgb(0 0 0 / 0.03)',
        'md': '0 2px 4px -1px rgb(0 0 0 / 0.06), 0 6px 16px -3px rgb(0 0 0 / 0.08), 0 0 2px 0 rgb(0 0 0 / 0.03)',
        'lg': '0 4px 6px -2px rgb(0 0 0 / 0.06), 0 12px 28px -4px rgb(0 0 0 / 0.09), 0 0 3px 0 rgb(0 0 0 / 0.03)',
        'xl': '0 8px 10px -4px rgb(0 0 0 / 0.06), 0 20px 44px -8px rgb(0 0 0 / 0.10), 0 0 4px 0 rgb(0 0 0 / 0.03)',
        '2xl': '0 12px 16px -6px rgb(0 0 0 / 0.08), 0 32px 64px -12px rgb(0 0 0 / 0.16), 0 0 6px 0 rgb(0 0 0 / 0.03)',
        'inner': 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
        'inner-lg': 'inset 0 2px 4px 0 rgb(0 0 0 / 0.06)',
        'soft': '0 2px 8px 0 rgb(0 0 0 / 0.04)',
        'medium': '0 4px 12px 0 rgb(0 0 0 / 0.08)',
        'hard': '0 10px 40px 0 rgb(0 0 0 / 0.15)',
        'glow': '0 0 20px rgb(249 115 22 / 0.3)',
        'glow-accent': '0 0 20px rgb(182 27 33 / 0.3)',
      },
      borderRadius: {
        '2xs': '0.125rem',
        '3xl': '1.5rem',
        '4xl': '2rem',
      },
      backdropBlur: {
        xs: '2px',
      },
      transitionDuration: {
        '400': '400ms',
        '600': '600ms',
        '800': '800ms',
        '900': '900ms',
      },
      transitionTimingFunction: {
        'in-expo': 'cubic-bezier(0.95, 0.05, 0.795, 0.035)',
        'out-expo': 'cubic-bezier(0.19, 1, 0.22, 1)',
        'spring': 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'gradient-soft': 'linear-gradient(135deg, var(--tw-gradient-stops))',
      },
      screens: {
        '3xl': '1920px',
        '4xl': '2560px',
      },
      zIndex: {
        '60': '60',
        '70': '70',
        '80': '80',
        '90': '90',
        '100': '100',
        '1000': '1000',
        '9999': '9999',
      },
      gridTemplateColumns: {
        '13': 'repeat(13, minmax(0, 1fr))',
        '14': 'repeat(14, minmax(0, 1fr))',
        '15': 'repeat(15, minmax(0, 1fr))',
        '16': 'repeat(16, minmax(0, 1fr))',
      },
      gridColumn: {
        'span-13': 'span 13 / span 13',
        'span-14': 'span 14 / span 14',
        'span-15': 'span 15 / span 15',
        'span-16': 'span 16 / span 16',
      },
      aspectRatio: {
        '4/3': '4 / 3',
        '3/2': '3 / 2',
        '2/3': '2 / 3',
        '3/4': '3 / 4',
        '5/4': '5 / 4',
        '4/5': '4 / 5',
        '9/16': '9 / 16',
        '21/9': '21 / 9',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    addVariablesForColors,
  ],
}

// This plugin adds each Tailwind color as a global CSS variable, e.g. var(--gray-200).
function addVariablesForColors({ addBase, theme }) {
  const flattenColorPalette = require("tailwindcss/lib/util/flattenColorPalette").default;
  let allColors = flattenColorPalette(theme("colors"));
  let newVars = Object.fromEntries(
    Object.entries(allColors).map(([key, val]) => [`--${key}`, val])
  );

  addBase({
    ":root": newVars,
  });
}
