import { useQuery } from "@tanstack/react-query";
import { fetchAPI } from "@/lib/api";

export interface AssetSignalConfig {
  signalId: string;
  label: string;
  unit: string;
}

/** Fetch signals for an asset from API — NO hardcoded config. */
export function useAssetSignals(assetId: string) {
  return useQuery({
    queryKey: ["asset-signals", assetId],
    queryFn: async (): Promise<AssetSignalConfig[]> => {
      const data = await fetchAPI<any[]>(`/api/v1/signals?asset_id=${assetId}`);
      const list = Array.isArray(data) ? data : data?.data || [];
      return list.map((s: any) => ({
        signalId: s.signal_id,
        label: s.display_name || s.signal_name || s.signal_id?.split(".").pop() || s.signal_id,
        unit: s.engineering_unit || s.unit || "",
      }));
    },
    staleTime: 30000,
    enabled: !!assetId,
  });
}
