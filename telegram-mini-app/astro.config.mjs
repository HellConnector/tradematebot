// @ts-check
import { defineConfig, envField } from "astro/config";
import htmx from "astro-htmx";

import cloudflare from "@astrojs/cloudflare";

// https://astro.build/config
export default defineConfig({
  output: "server",
  devToolbar: {
    enabled: false,
  },
  adapter: cloudflare({
    imageService: "cloudflare",
  }),
  vite: {
    plugins: [],
    server: {
      allowedHosts: [".tradematebot.app"],
    },
    build: {
      minify: true,
    },
  },
  integrations: [htmx()],
  env: {
    schema: {
      MINI_APP_API_URL: envField.string({
        context: "server",
        access: "secret",
      }),
    },
  },
});
