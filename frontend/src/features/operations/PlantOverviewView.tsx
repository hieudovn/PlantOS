import { useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { useWorkspace } from "@/lib/WorkspaceContext";
import { useProcessConfig } from "./hooks/useProcessConfig";
import { ProcessBlock } from "./components/ProcessBlock";
import { PlaceholderView } from "./components/PlaceholderView";

export function PlantOverviewView() {
  const { plantId } = useWorkspace();
  const navigate = useNavigate();

  const { data: config } = useProcessConfig(plantId);
  const workflow = config?.workflow;

  if (!workflow || workflow.length === 0) {
    return (
      <PlaceholderView
        title="Process View"
        message={`No workflow configured for ${plantId}.`}
      />
    );
  }

  return (
    <div className="flex flex-col gap-2 h-full">
      {/* Source badge */}
      <div className="flex items-center justify-end px-8 pt-2">
        <span
          className="text-xs px-2 py-0.5 rounded"
          style={{
            backgroundColor: config?.source === "backend" ? "rgba(59,130,246,0.15)" : "rgba(234,179,8,0.15)",
            color: config?.source === "backend" ? "#3b82f6" : "#eab308",
          }}
        >
          {config?.source === "backend" ? "API" : "Fallback"}
        </span>
      </div>

      {/* Workflow blocks */}
      <div className="flex items-center justify-center gap-2 p-8 h-full overflow-x-auto">
        {workflow.map((block: any, i: number) => (
          <div key={block.id} className="flex items-center gap-2 shrink-0">
            {i > 0 && (
              <ArrowRight className="w-5 h-5 shrink-0" style={{ color: 'var(--text-muted)' }} />
            )}
            <ProcessBlock
              config={{
                id: block.id,
                label: block.label,
                areaId: block.area_id,
                signalId: block.kpi_signal_id,
                unit: block.kpi_unit,
              }}
              onClick={() => navigate(`/operations/area/${block.area_id}`)}
            />
          </div>
        ))}
      </div>
    </div>
  );
}