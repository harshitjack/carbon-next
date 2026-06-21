import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#059669', // emerald-600
          dark: '#047857',
          light: '#10b981',
          50: '#ecfdf5',
          100: '#d1fae5',
          200: '#a7f3d0',
          300: '#6ee7b7',
          400: '#34d399',
          500: '#10b981',
          600: '#059669',
          700: '#047857',
          800: '#065f46',
          900: '#064e3b',
        },
        secondary: {
          DEFAULT: '#0891b2', // cyan-600
          50: '#ecfeff',
          100: '#cffafe',
          200: '#a5f3fc',
          300: '#67e8f9',
          400: '#22d3ee',
          500: '#06b6d4',
          600: '#0891b2',
          700: '#0e7490',
          800: '#155e75',
          900: '#164e63',
        },
        carbon: {
          low: '#059669', // emerald
          medium: '#f59e0b',
          high: '#dc2626',
          excellent: '#047857',
        },
        slate: {
          50: '#020617',
          100: '#0f172a',
          200: '#111827',
          300: '#1f2937',
          400: '#374151',
          500: '#4b5563',
          600: '#6b7280',
          700: '#9ca3af',
          800: '#e2e8f0',
          900: '#f8fafc',
          950: '#ffffff',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'breathing': 'breathing 8s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        breathing: {
          '0%, 100%': { opacity: '0.4', transform: 'scale(1)' },
          '50%': { opacity: '0.7', transform: 'scale(1.05)' },
        },
      },
      boxShadow: {
        'vercel': '0 0 0 1px rgba(255,255,255,0.08), 0 4px 24px -8px rgba(0,0,0,0.5)',
        'vercel-hover': '0 0 0 1px rgba(255,255,255,0.15), 0 8px 32px -8px rgba(0,0,0,0.6)',
      },
    },
  },
  plugins: [],
} satisfies Config;
