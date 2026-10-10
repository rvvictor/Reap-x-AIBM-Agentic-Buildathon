import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Each worktree gets its own ports: the API listens on $UAK_PORT and the web on $UAK_PORT+1.
const apiPort = process.env.UAK_PORT ?? "8000";
const webPort = process.env.UAK_PORT ? Number(process.env.UAK_PORT) + 1 : 5173;

// /api goes to FastAPI in dev; in the demo FastAPI serves web/dist (one process).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: webPort, proxy: { "/api": `http://127.0.0.1:${apiPort}` } },
});
