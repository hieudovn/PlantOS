import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { getAssets } from "@/lib/api";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix default marker icon for Vite bundling
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

const statusColor: Record<string, string> = {
  active: "#22c55e",
  running: "#3b82f6",
  warning: "#f59e0b",
  alarm: "#ef4444",
};

function createColoredIcon(color: string) {
  return L.divIcon({
    className: "",
    html: `<div style="width:14px;height:14px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 0 4px rgba(0,0,0,0.5)"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

export function GisMapPage() {
  const plantId = new URLSearchParams(window.location.search).get("plant_id") || "VF-DEMO";
  const { data: assets } = useQuery({
    queryKey: ["assets", plantId],
    queryFn: () => getAssets({ plant_id: plantId }),
  });

  useEffect(() => {
    const map = L.map("gis-map").setView([10.7626, 106.6602], 16);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap",
      maxZoom: 19,
    }).addTo(map);

    const locatedAssets = assets?.filter((a: any) => a.location?.lat && a.location?.lng) || [];

    locatedAssets.forEach((a: any) => {
      const marker = L.marker([a.location.lat, a.location.lng], {
        icon: createColoredIcon(statusColor[a.lifecycle_status] || "#6b7280"),
      }).addTo(map);

      marker.bindPopup(
        `<b>${a.name}</b><br/>${a.asset_id}<br/>Status: ${a.lifecycle_status}`
      );
      marker.on("click", () => {
        window.location.href = `/assets/${a.asset_id}`;
      });
    });

    // Fit bounds if markers exist
    if (locatedAssets.length > 0) {
      const bounds = locatedAssets.map((a: any) => [a.location.lat, a.location.lng]);
      map.fitBounds(bounds as any, { padding: [50, 50] });
    }

    return () => {
      map.remove();
    };
  }, [assets]);

  const locatedCount = assets?.filter((a: any) => a.location?.lat && a.location?.lng).length || 0;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">GIS Map</h1>
      <div className="text-sm text-gray-500">
        {locatedCount} assets with location
      </div>
      <div id="gis-map" className="h-[500px] rounded-lg border border-gray-800 z-0" />
    </div>
  );
}
