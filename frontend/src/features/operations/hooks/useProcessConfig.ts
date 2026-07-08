import { useQuery } from "@tanstack/react-query";
import { fetchAPI } from "@/lib/api";
import { getPlantConfig } from "../config";

export function useProcessConfig(plantId: string) {
  return useQuery({
    queryKey: ["process-config", plantId],
    queryFn: async () => {
      const res = await fetchAPI<any>(`/api/v1/plants/${plantId}/process-view`);
      if (res?.source === "backend") return res;
      throw new Error("Backend returned fallback, using local config");
    },
    staleTime: 60000,
    placeholderData: () => {
      const local = getPlantConfig(plantId);
      return local
        ? { plant_id: plantId, workflow: local.workflow || [], thresholds: local.thresholds || {}, source: "fallback" as const }
        : undefined;
    },
    retry: 1,
  });
}

export function useConditionConfig(assetId: string) {
  return useQuery({
    queryKey: ["condition-config", assetId],
    queryFn: () => fetchAPI<any>(`/api/v1/assets/${assetId}/condition-config`),
    staleTime: 60000,
    retry: 1,
  });
}
