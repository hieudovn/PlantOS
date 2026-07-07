import { useState } from "react";
import { useParams } from "react-router-dom";
import { HierarchyPanel } from "./components/HierarchyPanel";
import { BreadcrumbNav } from "./components/BreadcrumbNav";
import { ContextPanel } from "./components/ContextPanel";
import { OverlayBar } from "./components/OverlayBar";
import { PlantOverviewView } from "./PlantOverviewView";
import { AreaMonitoringView } from "./AreaMonitoringView";
import { AssetConditionView } from "./AssetConditionView";

export function ProcessViewWorkspace() {
  const { areaId, assetId } = useParams();
  const [selectedObject, setSelectedObject] = useState<{ type: string; id: string } | null>(() => {
    if (assetId) return { type: "asset", id: assetId };
    if (areaId) return { type: "area", id: areaId };
    return null;
  });
  const [contextVisible, setContextVisible] = useState(true);

  return (
    <div className="flex flex-col h-full">
      <BreadcrumbNav areaId={areaId} assetId={assetId} />
      <div className="flex flex-1 overflow-hidden">
        <HierarchyPanel onSelect={setSelectedObject} selectedId={selectedObject?.id} />
        <main className="flex-1 overflow-auto" style={{ backgroundColor: 'var(--surface-primary)' }}>
          {!areaId && !assetId ? (
            <PlantOverviewView />
          ) : areaId ? (
            <AreaMonitoringView areaId={areaId} />
          ) : (
            <AssetConditionView assetId={assetId!} />
          )}
        </main>
        {contextVisible && (
          <ContextPanel object={selectedObject} onClose={() => setContextVisible(false)} />
        )}
      </div>
      <OverlayBar />
    </div>
  );
}
