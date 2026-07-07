import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { useWorkspace } from "@/lib/WorkspaceContext";
import { fetchAPI } from "@/lib/api";

interface Props {
  areaId?: string;
  assetId?: string;
}

export function BreadcrumbNav({ areaId, assetId }: Props) {
  const { plantId } = useWorkspace();

  const { data: area } = useQuery({
    queryKey: ["area", areaId],
    queryFn: () => fetchAPI<any>(`/api/v1/areas/${areaId}`),
    enabled: !!areaId,
  });

  const { data: asset } = useQuery({
    queryKey: ["asset", assetId],
    queryFn: () => fetchAPI<any>(`/api/v1/assets/${assetId}`),
    enabled: !!assetId,
  });

  return (
    <div
      className="h-10 flex items-center px-4 text-xs gap-1"
      style={{ backgroundColor: 'var(--surface-secondary)', borderBottom: '1px solid var(--border-default)', color: 'var(--text-muted)' }}
    >
      <Link to="/operations" className="hover:underline" style={{ color: 'var(--accent-primary)' }}>
        {plantId}
      </Link>
      {area && (
        <>
          <ChevronRight className="w-3 h-3" />
          <Link to={`/operations/area/${area.area_id}`} className="hover:underline" style={{ color: 'var(--accent-primary)' }}>
            {area.name || area.area_id}
          </Link>
        </>
      )}
      {asset && (
        <>
          <ChevronRight className="w-3 h-3" />
          <span style={{ color: 'var(--text-primary)' }}>{asset.name || asset.asset_id}</span>
        </>
      )}
    </div>
  );
}
