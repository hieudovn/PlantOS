import { PlaceholderView } from "./components/PlaceholderView";

export function AssetConditionView({ assetId }: { assetId: string }) {
  return (
    <PlaceholderView
      title={`Asset: ${assetId}`}
      message="Asset condition view — coming in Phase 6-PV-04."
    />
  );
}