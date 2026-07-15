import { fileURLToPath, URL } from "node:url";

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import vueDevTools from "vite-plugin-vue-devtools";
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import timezone from "dayjs/plugin/timezone";

dayjs.extend(utc);
dayjs.extend(timezone);

// https://vite.dev/config/
export default defineConfig({
  base: process.env.MJS_TIERMAKER_BASE_URL || "./",
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  define: {
    __BUILD_TIME__: JSON.stringify(
      dayjs().tz("Asia/Shanghai").format("YYYY-MM-DD"),
    ),
  },
  build: {
    rolldownOptions: {
      output: {
        codeSplitting: {
          minSize: 20000,
          groups: [
            {
              name: "large-libs",
              test: /node_modules/,
              minSize: 100000,
              maxSize: 250000,
              priority: 10,
            },
          ],
        },
      },
    },
  },
});
