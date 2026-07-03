import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, LineChart, Workflow, MapPin,
  Bell, Boxes, Activity, Server, Monitor, BarChart3, Users,
} from "lucide-react";

type NavItemDef = { path: string; icon: any; label: string; roles?: string[] };

const navGroups: { label: string; items: NavItemDef[]; roles?: string[] }[] = [
  {
    label: "Monitor",
    items: [
      { path: "/", icon: LayoutDashboard, label: "Overview" },
      { path: "/historian", icon: LineChart, label: "Historian" },
      { path: "/diagrams", icon: Workflow, label: "Diagrams" },
      { path: "/gis", icon: MapPin, label: "GIS Map" },
      { path: "/alarms", icon: Bell, label: "Alarms" },
    ],
  },
  {
    label: "Management",
    roles: ["admin", "engineer"],
    items: [
      { path: "/reports", icon: BarChart3, label: "Reports" },
    ],
  },
  {
    label: "Platform",
    roles: ["admin"],
    items: [
      { path: "/assets", icon: Boxes, label: "Assets" },
      { path: "/signals", icon: Activity, label: "Signals" },
      { path: "/edge", icon: Server, label: "Edge Fleet" },
      { path: "/system", icon: Monitor, label: "System" },
      { path: "/users", icon: Users, label: "Users" },
    ],
  },
];

function getUserRole(): string {
  try {
    const token = localStorage.getItem("plantos_token");
    if (!token) return "operator";
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload?.role || "operator";
  } catch {
    return "operator";
  }
}

function NavItem({ path, icon: Icon, label }: { path: string; icon: any; label: string }) {
  return (
    <NavLink
      to={path}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
          isActive ? "text-white" : "hover:text-white"
        }`
      }
      style={({ isActive }) => ({
        backgroundColor: isActive ? 'var(--surface-hover)' : 'transparent',
        color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
      })}
    >
      <Icon className="w-4 h-4" />
      {label}
    </NavLink>
  );
}

export function Sidebar() {
  const role = getUserRole();

  return (
    <aside style={{ backgroundColor: 'var(--surface-primary)', borderColor: 'var(--border-default)' }} className="w-60 border-r flex flex-col">
      <div style={{ borderColor: 'var(--border-default)' }} className="h-14 flex items-center px-4 border-b">
        <span className="inline-flex items-center gap-2 text-lg font-bold tracking-tight">
          <LayoutDashboard className="w-5 h-5" style={{ color: 'var(--accent-primary)' }} />
          PlantOS
        </span>
      </div>
      <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
        {navGroups.map((group) => {
          if (group.roles && !group.roles.includes(role)) return null;
          const visibleItems = group.items.filter(
            (item) => !item.roles || item.roles.includes(role)
          );
          if (visibleItems.length === 0) return null;

          return (
            <div key={group.label}>
              <div
                className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-widest"
                style={{ color: 'var(--text-muted)' }}
              >
                {group.label}
              </div>
              {visibleItems.map((item) => (
                <NavItem key={item.path} {...item} />
              ))}
            </div>
          );
        })}
      </nav>
      <div style={{ borderColor: 'var(--border-default)', color: 'var(--text-muted)' }} className="p-3 border-t text-xs flex items-center justify-between">
        <span>PlantOS v0.1.0</span>
        <span className="capitalize opacity-60">{role}</span>
      </div>
    </aside>
  );
}
