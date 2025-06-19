  // postcss.config.js
module.exports = {
    plugins: {
      // This is the crucial change based on the error message
      '@tailwindcss/postcss': {},
      autoprefixer: {},
    },
  };