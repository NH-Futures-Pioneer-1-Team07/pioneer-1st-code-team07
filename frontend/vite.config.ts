import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 백엔드(FastAPI)는 로컬 8000번 포트에서 실행한다. 화면은 같은 주소로 API와 웹소켓을 부른다.
const backend = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
const proxy = {
  "/api": { target: backend },
  "/ws": { target: backend, ws: true },
};

export default defineConfig({
  plugins: [react()],
  server: { proxy },
  preview: { proxy },
});
