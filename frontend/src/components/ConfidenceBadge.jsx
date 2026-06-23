// Maps backend confidence ("high" | "medium" | "low") to a color-coded pill.
// Confidence colors are reserved for this badge only — independent of the cyan accent.
const STYLES = {
  high: {
    label: "High confidence",
    dot: "bg-emerald-400",
    text: "text-emerald-400",
    ring: "ring-emerald-500/30",
    bg: "bg-emerald-500/10",
  },
  medium: {
    label: "Medium confidence",
    dot: "bg-amber-400",
    text: "text-amber-400",
    ring: "ring-amber-500/30",
    bg: "bg-amber-500/10",
  },
  low: {
    label: "Low confidence",
    dot: "bg-rose-400",
    text: "text-rose-400",
    ring: "ring-rose-500/30",
    bg: "bg-rose-500/10",
  },
};

export default function ConfidenceBadge({ confidence }) {
  // Defensive: unknown values fall back to the muted "low" style.
  const style = STYLES[confidence] ?? STYLES.low;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ring-1 ${style.bg} ${style.text} ${style.ring}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
      {style.label}
    </span>
  );
}
