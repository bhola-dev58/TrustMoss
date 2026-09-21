/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Theme: Developer Ember / Dark Obsidian
        obsidian: {
          bg: '#121212',
          surface: '#1E1E1E',
          surfaceAlt: '#242424',
          border: '#333333',
          borderLight: '#444444',
        },
        ember: {
          start: '#FF8C00',
          end: '#FFC107',
          50: '#FFF8E1',
          100: '#FFECB3',
          200: '#FFE082',
          300: '#FFD54F',
          400: '#FFCA28',
          500: '#FF8C00',
          600: '#F57C00',
          700: '#E65100',
        },
        // Mapped to Developer Ember / Dark Obsidian palette
        slate: {
          950: '#121212', // Obsidian Black background
          900: '#1E1E1E', // Charcoal Surface card fill
          850: '#242424', // Surface Alt
          800: '#242424', // Interactive container fill
          750: '#2C2C2C',
          700: '#333333', // Subtle Divider Grey
          600: '#4A4A4A',
          500: '#9AA0A6', // Muted Cool Grey
          400: '#9AA0A6', // Secondary Text
          300: '#D1D5DB',
          200: '#E5E7EB',
          100: '#FFFFFF', // Pure White Primary Text
          50: '#FFFFFF',
        },
        moss: {
          500: '#FF8C00',
          600: '#F57C00',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      backgroundImage: {
        'ember-gradient': 'linear-gradient(135deg, #FF8C00 0%, #FFC107 100%)',
        'ember-gradient-hover': 'linear-gradient(135deg, #FFA000 0%, #FFD54F 100%)',
      },
      boxShadow: {
        'ember-glow': '0 0 20px -5px rgba(255, 140, 0, 0.35)',
        'ember-glow-lg': '0 0 35px -5px rgba(255, 140, 0, 0.45)',
      },
    },
  },
  plugins: [],
}
