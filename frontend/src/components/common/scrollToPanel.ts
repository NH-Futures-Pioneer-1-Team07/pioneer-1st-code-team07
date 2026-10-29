/** 상세 패널이 펼쳐져 높이가 늘어난 뒤, 패널 영역이 화면 위쪽에 오도록 페이지를 스크롤한다. */
export function scrollToPanel(element: HTMLElement | null) {
  if (!element) return;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  requestAnimationFrame(() =>
    element.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" }),
  );
}
