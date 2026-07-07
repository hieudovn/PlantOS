import { useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { useWorkspace } from "@/lib/WorkspaceContext";
import { getWorkflowConfig } from "./config";
import { ProcessBlock } from "./components/ProcessBlock";
import { PlaceholderView } from "./components/PlaceholderView";

export function PlantOverviewView() {
  const { plantId } = useWorkspace();
  const navigate = useNavigate();

  const workflow = getWorkflowConfig(plantId);

  if (!workflow || workflow.length === 0) {
    return (
      <PlaceholderView
        title="Process View"
        message={`No workflow configured for ${plantId}.`}
      />
    );
  }

  return (
    <div className="flex items-center justify-center gap-2 p-8 h-full overflow-x-auto">
      {workflow.map((block, i) => (
        <div key={block.id} className="flex items-center gap-2 shrink-0">
          {i > 0 && (
            <ArrowRight className="w-5 h-5 shrink-0" style={{ color: 'var(--text-muted)' }} />
          )}
          <ProcessBlock
            config={block}
            onClick={() => navigate(`/operations/area/${block.areaId}`)}
          />
        </div>
      ))}
    </div>
  );
}