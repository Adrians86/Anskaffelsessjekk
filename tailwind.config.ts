import type { Config } from 'tailwindcss'

export default {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#0F1B2D',
          700: '#1F3A5F',
          500: '#3C5B8A',
        },
        gold: {
          bright: '#D9B24A',
        },
        semantic: {
          success: '#2E7D32',
          warning: '#B58900',
          danger: '#C62828',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config
