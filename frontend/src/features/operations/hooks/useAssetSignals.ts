import { useQuery } from "@tanstack/react-query";
import { fetchAPI } from "@/lib/api";
import type { AssetSignalConfig } from "../types";

interface SignalApiRow {
  signal_id: string;
  display_name?: string | null;
  signal_name?: string | null;
  engineering_unit?: string | null;
  unit?: string | null;
}

function isSignalApiRow(value: unknown): value is SignalApiRow {
  if (!value || typeof value !== "object") return false;
  const row = value as Record<string, unknown>;
  return typeof row.signal_id === "string";
}

/** Fetch signals for an asset from API — NO hardcoded config. */
export function useAssetSignals(assetId: string) {
  return useQuery({
    queryKey: ["asset-signals", assetId],
    queryFn: async (): Promise<AssetSignalConfig[]> => {
      const data: unknown = await fetchAPI(`/api/v1/signals?asset_id=${assetId}`);
      const list = Array.isArray(data) ? data : (data as Record<string, unknown>)?.data;
      if (!Array.isArray(list)) return [];
      return list
        .filter(isSignalApiRow)
        .map((s: SignalApiRow) => ({
          signalId: s.signal_id,
          label: s.display_name || s.signal_name || s.signal_id.split(".").pop() || s.signal_id,
          unit: s.engineering_unit || s.unit || "",
        }));
    },
    staleTime: 30000,
    enabled: !!assetId,
  });
}
