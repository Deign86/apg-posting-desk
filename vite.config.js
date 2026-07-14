import { defineConfig } from "vite";

export default defineConfig({
  server: {
    host: "localhost",
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8001",
      "/prepared": "http://127.0.0.1:8001"
    }
  },
  preview: {
    host: "localhost",
    port: 4173
  }
});
