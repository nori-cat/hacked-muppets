import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxy /upload to Flask so no CORS setup is needed in development.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/upload": "http://127.0.0.1:5000",
    },
  },
});
