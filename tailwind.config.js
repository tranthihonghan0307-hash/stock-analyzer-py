/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef7f7",
          100: "#d7ecec",
          500: "#2f6f6d",
          600: "#255957",
          700: "#1c4442",
        },
        up: "#16a34a",
        down: "#dc2626",
      },
    },
  },
  plugins: [],
};
