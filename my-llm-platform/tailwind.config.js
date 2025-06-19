// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
      "./src/**/*.{js,jsx,ts,tsx}",
      "./public/index.html", // Include this if you have Tailwind classes directly in your HTML
    ],
    theme: {
      extend: {},
    },
    plugins: [],
  }