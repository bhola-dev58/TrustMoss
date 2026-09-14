/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        moss: {
          50: '#f2f9f3',
          100: '#e1f2e4',
          200: '#c5e5cc',
          300: '#99d2a6',
          400: '#66b87b',
          500: '#3d9c55',
          600: '#2d7c42',
          700: '#256336',
          800: '#204f2d',
          900: '#1c4127',
          950: '#0c2314',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
