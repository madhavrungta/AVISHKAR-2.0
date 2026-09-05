/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
        display: ['Space Grotesk', 'Plus Jakarta Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        space: {
          950: '#060913',
          900: '#0b1120',
          850: '#10182b',
          800: '#162238',
          700: '#223454',
        },
        cyan: {
          400: '#38bdf8',
          500: '#0ea5e9',
        },
        brand: {
          primary: '#0ea5e9',
          glow: 'rgba(14, 165, 233, 0.15)',
        }
      },
      boxShadow: {
        'glow-cyan': '0 0 25px rgba(14, 165, 233, 0.25)',
        'glow-red': '0 0 25px rgba(239, 68, 68, 0.35)',
        'glow-amber': '0 0 25px rgba(245, 158, 11, 0.3)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'ping-slow': 'ping 2.5s cubic-bezier(0, 0, 0.2, 1) infinite',
      }
    },
  },
  plugins: [],
}
