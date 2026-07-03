import { createBrowserRouter } from "react-router-dom";
import { Shell } from "@/components/layout/Shell";
import { OverviewPage } from "@/features/overview/OverviewPage";
import { SystemHealthPage } from "@/features/system/SystemHealthPage";
import { AssetTable } from "@/features/assets/AssetTable";
import { AssetDetail } from "@/features/assets/AssetDetail";
import { SignalTable } from "@/features/signals/SignalTable";
import { HistorianPage } from "@/features/historian/HistorianPage";
import { DiagramPage } from "@/features/visualization/DiagramPage";
import { GisMapPage } from "@/features/visualization/GisMapPage";
import { EdgeFleetPage } from "@/features/edge-fleet/EdgeFleetPage";
import { AlarmPage } from "@/features/alarms/AlarmPage";
import { LoginPage } from "@/features/auth/LoginPage";
import { ReportsPage } from "@/features/reports/ReportsPage";
import { UserManagementPage } from "@/features/users/UserManagementPage";

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="flex items-center justify-center h-64 text-gray-600">
      <div className="text-center">
        <div className="text-4xl mb-3">🚧</div>
        <div className="text-lg">{title}</div>
        <div className="text-sm mt-1">Coming in next phase</div>
      </div>
    </div>
  );
}

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/",
    element: <Shell />,
    children: [
      { index: true, element: <OverviewPage /> },
      { path: "assets", element: <AssetTable /> },
      { path: "assets/:assetId", element: <AssetDetail /> },
      { path: "signals", element: <SignalTable /> },
      { path: "historian", element: <HistorianPage /> },
      { path: "diagrams", element: <DiagramPage /> },
      { path: "gis", element: <GisMapPage /> },
      { path: "alarms", element: <AlarmPage /> },
      { path: "edge", element: <EdgeFleetPage /> },
      { path: "system", element: <SystemHealthPage /> },
      { path: "reports", element: <ReportsPage /> },
      { path: "users", element: <UserManagementPage /> },
    ],
  },
]);
