import axios from "axios";

export const http = axios.create({ baseURL: "/", timeout: 15000 });

/** 서버가 돌려준 사유(`detail`)나 연결 오류를 사람이 읽을 문장으로 바꾼다. */
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail) return detail;
    if (error.response) return `서버가 요청을 처리하지 못했습니다 (${error.response.status})`;
    return "서버에 연결할 수 없습니다";
  }
  return error instanceof Error ? error.message : "알 수 없는 오류가 났습니다";
}
