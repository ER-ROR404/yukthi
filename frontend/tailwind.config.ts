import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class',
  content: [
    './components/**/*.{vue,js,ts}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './composables/**/*.{js,ts}',
    './plugins/**/*.{js,ts}',
    './app.{js,ts,vue}'
  ],
  theme: {
    extend: {
      colors: {
        cockpit: {
          950: '#070A0F',
          900: '#0B0F17',
          850: '#0F1622',
          800: '#141D2C',
          750: '#1B263B',
          700: '#24324A',
          600: '#334460',
          500: '#485C7F',
          300: '#94A3B8',
          100: '#F1F5F9'
        },
        status: {
          emerald: '#10B981',
          amber: '#F59E0B',
          crimson: '#EF4444',
          blue: '#3B82F6'
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        mono: ['"Fira Code"', 'monospace']
      }
    }
  },
  plugins: []
} satisfies Config
