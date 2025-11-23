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
          DEFAULT: '#0099FF',
          light: '#E6F5FF',
          dark: '#0066CC',
        },
        accent: {
          purple: '#A78BFA',
          pink: '#FB7185',
          green: '#34D399',
          yellow: '#FCD34D',
          orange: '#FB923C',
          gold: '#F59E0B',
        },
        surface: {
          DEFAULT: '#F9FAFB',
          hover: '#F3F4F6',
        },
        border: {
          DEFAULT: '#E5E7EB',
          strong: '#D1D5DB',
        },
      },
      fontFamily: {
        sans: ['Pretendard', 'Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
