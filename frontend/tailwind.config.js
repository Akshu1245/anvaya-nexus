/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#07111f',
          900: '#0d1b2a',
          800: '#17324d',
          700: '#1f4368',
        },
        teal: {
          50: '#eefbfa',
          100: '#d6f5f2',
          200: '#b0e9e5',
          300: '#70c5c5',
          400: '#43aeae',
          500: '#1f8a8a',
          600: '#177474',
          700: '#155e5e',
          800: '#144b4b',
          900: '#123e3e',
        },
      },
      boxShadow: {
        panel: '0 18px 50px rgba(2, 10, 20, 0.18)',
        bubble: '0 2px 12px rgba(2, 10, 20, 0.06)',
        glow: '0 0 0 4px rgba(112, 197, 197, 0.25)',
      },
      keyframes: {
        'fade-in-up': {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'slide-in-right': {
          from: { opacity: '0', transform: 'translateX(16px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
        'scale-in': {
          from: { opacity: '0', transform: 'scale(0.96)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
        'pulse-ring': {
          '0%': { boxShadow: '0 0 0 0 rgba(239, 68, 68, 0.45)' },
          '70%': { boxShadow: '0 0 0 10px rgba(239, 68, 68, 0)' },
          '100%': { boxShadow: '0 0 0 0 rgba(239, 68, 68, 0)' },
        },
        shimmer: {
          from: { backgroundPosition: '200% 0' },
          to: { backgroundPosition: '-200% 0' },
        },
      },
      animation: {
        'fade-in-up': 'fade-in-up 0.35s cubic-bezier(0.21, 1.02, 0.73, 1) both',
        'fade-in': 'fade-in 0.4s ease-out both',
        'slide-in-right': 'slide-in-right 0.35s cubic-bezier(0.21, 1.02, 0.73, 1) both',
        'scale-in': 'scale-in 0.25s ease-out both',
        'pulse-ring': 'pulse-ring 1.5s cubic-bezier(0.66, 0, 0, 1) infinite',
        shimmer: 'shimmer 2.2s linear infinite',
      },
    },
  },
  plugins: [],
}
