import { Circle, ArrowRight } from "lucide-react";

type StageKpi = {
  label: string;
  value: string | number;
  unit?: string;
};

type StageProps = {
  id: string;
  label: string;
  status: "normal" | "warning" | "critical";
  kpis: StageKpi[];
  onClick?: () => void;
};

type WorkflowDiagramProps = {
  stages: StageProps[];
  plantId: string;
};

const statusColors: Record<string, string> = {
  normal: "var(--status-normal)",
  warning: "var(--status-warning)",
  critical: "var(--status-critical)",
};

export function WorkflowDiagram({ stages, plantId }: WorkflowDiagramProps) {
  if (stages.length === 0) {
    return (
      <div
        style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }}
        className="rounded-lg border p-6"
      >
        <h3 style={{ color: 'var(--text-secondary)' }} className="text-xs font-semibold uppercase tracking-wide mb-3">
          Workflow Diagram
        </h3>
        <div style={{ color: 'var(--text-muted)' }} className="text-sm text-center py-8">
          No workflow stages configured for {plantId}
        </div>
      </div>
    );
  }

  return (
    <div
      style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }}
      className="rounded-lg border p-4"
    >
      <h3 style={{ color: 'var(--text-secondary)' }} className="text-xs font-semibold uppercase tracking-wide mb-3">
        Workflow Diagram · {plantId}
      </h3>
      <div className="flex items-start gap-0 overflow-x-auto pb-2">
        {stages.map((stage, idx) => {
          const handleClick = stage.onClick;
          return (
          <div key={stage.id} className="flex items-start">
            <div
              onClick={handleClick}
              role={handleClick ? "button" : undefined}
              tabIndex={handleClick ? 0 : undefined}
              onKeyDown={handleClick ? (e) => { if (e.key === "Enter") handleClick(); } : undefined}
              style={{
                backgroundColor: 'var(--surface-secondary)',
                borderColor: 'var(--border-default)',
                minWidth: 140,
              }}
              className={`rounded-lg border p-3 ${stage.onClick ? "cursor-pointer hover:brightness-110 transition-all" : ""}`}
            >
              <div className="flex items-center gap-1.5 mb-2">
                <Circle
                  className="w-2.5 h-2.5 fill-current"
                  style={{ color: statusColors[stage.status] || statusColors.normal }}
                />
                <span style={{ color: 'var(--text-primary)' }} className="text-sm font-medium">
                  {stage.label}
                </span>
              </div>
              {stage.kpis.map((kpi, ki) => (
                <div key={ki} className="text-xs leading-tight mb-0.5">
                  <span style={{ color: 'var(--text-secondary)' }}>{kpi.label}: </span>
                  <span style={{ color: 'var(--text-primary)' }} className="font-semibold">
                    {kpi.value}{kpi.unit ? ` ${kpi.unit}` : ""}
                  </span>
                </div>
              ))}
            </div>
            {idx < stages.length - 1 && (
              <div className="flex items-center pt-5 px-1">
                <ArrowRight className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
              </div>
            )}
          </div>
          );
        })}
      </div>
    </div>
  );
}
