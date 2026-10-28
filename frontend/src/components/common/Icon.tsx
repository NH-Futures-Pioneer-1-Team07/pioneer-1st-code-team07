type IconName =
  | "chart"
  | "flask"
  | "arrow"
  | "play"
  | "stop"
  | "shield"
  | "close"
  | "spinner"
  | "check"
  | "info";

const paths: Record<IconName, string> = {
  chart: "M3 3v18h18M7 14V9m4 8V6m4 7V3m4 14V9",
  flask: "M9 3h6m-5 0v6L4 19a1 1 0 0 0 1 2h14a1 1 0 0 0 1-2L14 9V3M7 15h10",
  arrow: "M5 12h14m-5-5 5 5-5 5",
  play: "M8 5.6v12.8a.9.9 0 0 0 1.37.77l10.2-6.4a.9.9 0 0 0 0-1.54L9.37 4.83A.9.9 0 0 0 8 5.6Z",
  stop: "M8 6h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2Z",
  shield: "m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6ZM8 12l3 3 5-6",
  close: "m6 6 12 12M6 18 18 6",
  spinner: "M21 12a9 9 0 1 1-6.2-8.55",
  check: "m5 12.5 4.5 4.5L19 7.5",
  info: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Zm0-10v6m0-9.5v.01",
};

const filled: IconName[] = ["play", "stop"];

export default function Icon({
  name,
  size = 18,
  spin = false,
}: {
  name: IconName;
  size?: number;
  spin?: boolean;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill={filled.includes(name) ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={spin ? "icon-spin" : undefined}
    >
      <path d={paths[name]} />
    </svg>
  );
}
