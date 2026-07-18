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
        },
        teal: {
          500: '#1f8a8a',
          300: '#70c5c5',
        },
      },
      boxShadow: {
        panel: '0 18px 50px rgba(2, 10, 20, 0.18)',
      },
    },
  },
  plugins: [],
}
