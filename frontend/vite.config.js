import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// CRA(react-scripts) → Vite 이전: 기존과 같은 포트(3000)·빌드 폴더(build) 유지
export default defineConfig({
  plugins: [react()],
  server: { port: 3000, host: true },
  preview: { port: 3000, host: true },
  build: { outDir: "build" },
});
