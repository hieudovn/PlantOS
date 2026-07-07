import { useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { useWorkspace } from "@/lib/WorkspaceContext";
import { WTP_WORKFLOW } from "./config/wtp-workflow";
import { ProcessBlock } from "./components/ProcessBlock";
import { PlaceholderView } from "./components/PlaceholderView";

export function PlantOverviewView() {
  const { plantId } = useWorkspace();
  const navigate = useNavigate();

  if (plantId !== "WTP-DEMO-01") {
    return (
      <PlaceholderView
        title="Process View"
        message={`No workflow configured for ${plantId}. Select WTP-DEMO-01 to view the treatment process.`}
      />
    );
  }

  return (
    <div className="flex items-center justify-center gap-2 p-8 h-full overflow-x-auto">
      {WTP_WORKFLOW.map((block, i) => (
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