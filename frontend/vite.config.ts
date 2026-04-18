import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxy /api requests to backend (FastAPI on :8000).
// SSE works natively through Vite's proxy in dev.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
