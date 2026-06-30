import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, Wrench, Radio, ChartLine, MapPin,
  GitBranch, Bell, Plug,
} from "lucide-react";

const navItems = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/assets", label: "Assets", icon: Wrench },
  { to: "/signals", label: "Signals", icon: Radio },
  { to: "/historian", label: "Historian", icon: ChartLine },
  { to: "/diagrams", label: "Diagrams", icon: GitBranch },
  { to: "/gis", label: "GIS Map", icon: MapPin },
  { to: "/alarms", label: "Alarms", icon: Bell },
  { to: "/edge", label: "Edge Fleet", icon: Plug },
];

export function Sidebar() {
  return (
    <aside className="w-60 bg-gray-900 border-r border-gray-800 flex flex-col">
      <div className="h-14 flex items-center px-4 border-b border-gray-800">
        <span className="text-lg font-bold tracking-tight">🏭 PlantOS</span>
      </div>
      <nav className="flex-1 p-2 space-y-0.5">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? "bg-gray-800 text-white"
                  : "text-gray-400 hover:text-white hover:bg-gray-800/50"
              }`
            }
          >
            <Icon className="w-4 h-4" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="p-3 border-t border-gray-800 text-xs text-gray-600">
        PlantOS v0.1.0
      </div>
    </aside>
  );
}
