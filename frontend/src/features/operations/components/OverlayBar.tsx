import { useState } from "react";
import { Circle, Triangle, Diamond } from "lucide-react";

type Toggle = "status" | "alarm" | "quality";

const toggleConfig: Record<Toggle, { label: string; icon: any; activeColor: string }> = {
  status: { label: "Status", icon: Circle, activeColor: "var(--status-normal)" },
  alarm: { label: "Alarm", icon: Triangle, activeColor: "var(--status-critical)" },
  quality: { label: "Quality", icon: Diamond, activeColor: "var(--status-warning)" },
};

export function OverlayBar() {
  const [activeToggles, setActiveToggles] = useState<Set<Toggle>>(new Set());

  const toggle = (key: Toggle) => {
    setActiveToggles((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  return (
    <div
      className="h-10 flex items-center gap-2 px-4 border-t"
      style={{ backgroundColor: 'var(--surface-secondary)', borderColor: 'var(--border-default)' }}
    >
      {(Object.keys(toggleConfig) as Toggle[]).map((key) => {
        const cfg = toggleConfig[key];
        const isActive = activeToggles.has(key);
        const Icon = cfg.icon;
        return (
          <button
            key={key}
            onClick={() => toggle(key)}
            className="flex items-center gap-1.5 px-3 py-1 rounded text-xs transition-colors"
            style={{
              backgroundColor: isActive ? 'var(--surface-hover)' : 'transparent',
              border: '1px solid',
              borderColor: isActive ? cfg.activeColor : 'var(--border-default)',
              color: isActive ? cfg.activeColor : 'var(--text-muted)',
            }}
          >
            <Icon className="w-3 h-3 fill-current" />
            {cfg.label}
          </button>
        );
      })}
    </div>
  );
}
