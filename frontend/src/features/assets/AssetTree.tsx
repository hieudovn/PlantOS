import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { getAssets } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { ChevronRight, ChevronDown } from "lucide-react";

// Icons by asset type
const typeIcons: Record<string, any> = {
  pump: { icon: "🔧", label: "Pump" },
  motor: { icon: "⚡", label: "Motor" },
  tank: { icon: "🛢️", label: "Tank" },
  valve: { icon: "🔩", label: "Valve" },
  transformer: { icon: "🔌", label: "Transformer" },
  feeder: { icon: "⚡", label: "Feeder" },
  breaker: { icon: "🔒", label: "Breaker" },
  line: { icon: "📦", label: "Line" },
  substation: { icon: "🏭", label: "Substation" },
};

interface TreeNode {
  id: string;
  label: string;
  type: string;
  assetId?: string;
  status?: string;
  children: TreeNode[];
}

function buildTree(assets: any[]): TreeNode[] {
  // Group by area_id (string)
  const areaMap: Record<string, TreeNode> = {};
  const assetNodes: Record<string, TreeNode> = {};

  // Create asset nodes
  for (const a of assets) {
    const node: TreeNode = {
      id: a.asset_id,
      label: a.name,
      type: a.asset_type || "unknown",
      assetId: a.asset_id,
      status: a.lifecycle_status,
      children: [],
    };
    assetNodes[a.asset_id] = node;
  }

  // Build parent-child relationships
  const roots: TreeNode[] = [];
  for (const a of assets) {
    const node = assetNodes[a.asset_id];
    if (a.parent_asset_id && assetNodes[a.parent_asset_id]) {
      assetNodes[a.parent_asset_id].children.push(node);
    } else if (a.area_id) {
      // Group by area
      if (!areaMap[a.area_id]) {
        areaMap[a.area_id] = {
          id: a.area_id,
          label: a.area_id,
          type: "area",
          children: [],
        };
      }
      areaMap[a.area_id].children.push(node);
    } else {
      roots.push(node);
    }
  }

  return [...roots, ...Object.values(areaMap)];
}

function TreeNodeRow({ node, level = 0 }: { node: TreeNode; level?: number }) {
  const [expanded, setExpanded] = useState(level < 2);
  const navigate = useNavigate();
  const hasChildren = node.children.length > 0;
  const info = typeIcons[node.type];

  const handleClick = () => {
    if (node.assetId) {
      navigate(`/assets/${node.assetId}`);
    } else {
      setExpanded(!expanded);
    }
  };

  return (
    <div>
      <div
        className="flex items-center gap-2 px-3 py-1.5 hover:bg-gray-800/50 cursor-pointer text-sm"
        style={{ paddingLeft: `${level * 20 + 12}px` }}
        onClick={handleClick}
      >
        {hasChildren ? (
          <span
            onClick={e => {
              e.stopPropagation();
              setExpanded(!expanded);
            }}
          >
            {expanded ? (
              <ChevronDown className="w-3.5 h-3.5 text-gray-500" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5 text-gray-500" />
            )}
          </span>
        ) : (
          <span className="w-3.5" />
        )}
        <span className="text-sm">{info?.icon || "📄"}</span>
        <span className="flex-1">{node.label}</span>
        {node.assetId && (
          <span className="font-mono text-xs text-gray-500">{node.assetId}</span>
        )}
        {node.status && <StatusBadge status={node.status} />}
      </div>
      {expanded && hasChildren && (
        <div>
          {node.children.map(child => (
            <TreeNodeRow key={child.id} node={child} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export function AssetTree() {
  const { data: assets, isLoading } = useQuery({
    queryKey: ["assets"],
    queryFn: () => getAssets(),
  });

  if (isLoading) return <div className="text-gray-500">Loading...</div>;
  if (!assets) return null;

  const tree = buildTree(assets);

  return (
    <div className="rounded-lg border border-gray-800 overflow-hidden">
      {tree.map(node => (
        <TreeNodeRow key={node.id} node={node} />
      ))}
    </div>
  );
}
