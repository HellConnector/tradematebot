/** @type {import("prettier").Config} */
export default {
  plugins: ["prettier-plugin-astro"],
  singleQuote: false,
  overrides: [
    {
      files: "*.astro",
      options: {
        parser: "astro",
      },
    },
  ],
};
