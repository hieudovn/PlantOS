const statusColors: Record<string, string> = {
  active: "bg-status-normal/20 text-status-normal",
  running: "bg-status-running/20 text-status-running",
  warning: "bg-status-warning/20 text-status-warning",
  alarm: "bg-status-alarm/20 text-status-alarm",
  offline: "bg-status-offline/20 text-status-offline",
  simulated: "bg-status-simulated/20 text-status-simulated",
  inactive: "bg-gray-800 text-gray-500",
  good: "bg-status-normal/20 text-status-normal",
  bad: "bg-status-alarm/20 text-status-alarm",
  uncertain: "bg-status-warning/20 text-status-warning",
};

export function StatusBadge({ status }: { status: string }) {
  const color = statusColors[status] || statusColors.inactive;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${color}`}>
      {status}
    </span>
  );
}
