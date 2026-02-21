/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'arabic': ['Cairo', 'sans-serif'],
        'english': ['Inter', 'sans-serif']
      }
    },
  },
  plugins: [],
}