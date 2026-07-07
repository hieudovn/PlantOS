import { useState } from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, LineChart, Factory, MapPin,
  Bell, Boxes, Activity, Server, Monitor, BarChart3, Users,
} from "lucide-react";

type NavItemDef = { path: string; icon: any; label: string; roles?: string[] };

const navGroups: { label: string; items: NavItemDef[]; roles?: string[] }[] = [
  {
    label: "Monitor",
    items: [
      { path: "/", icon: LayoutDashboard, label: "Overview" },
      { path: "/historian", icon: LineChart, label: "Historian" },
      { path: "/operations", icon: Factory, label: "Operations" },
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

function NavItem({ path, icon: Icon, label, collapsed }: { path: string; icon: any; label: string; collapsed?: boolean }) {
  return (
    <NavLink
      to={path}
      title={collapsed ? label : undefined}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
          collapsed ? "justify-center" : ""
        } ${isActive ? "text-white" : "hover:text-white"}`
      }
      style={({ isActive }) => ({
        backgroundColor: isActive ? 'var(--surface-hover)' : 'transparent',
        color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
      })}
    >
      <Icon className="w-4 h-4 shrink-0" />
      {!collapsed && label}
    </NavLink>
  );
}

export function Sidebar() {
  const role = getUserRole();
  const [expanded, setExpanded] = useState(false);

  return (
    <aside
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
      style={{ backgroundColor: 'var(--surface-primary)', borderColor: 'var(--border-default)' }}
      className={`${expanded ? "w-40" : "w-14"} border-r flex flex-col transition-all duration-200 overflow-hidden`}
    >
      {/* Brand */}
      <div style={{ borderColor: 'var(--border-default)' }} className="h-14 flex items-center px-3 border-b shrink-0">
        {expanded ? (
          <span className="inline-flex items-center gap-2 text-base font-bold tracking-tight">
            <LayoutDashboard className="w-5 h-5 shrink-0" style={{ color: 'var(--accent-primary)' }} />
            PlantOS
          </span>
        ) : (
          <LayoutDashboard className="w-5 h-5 mx-auto" style={{ color: 'var(--accent-primary)' }} />
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 p-1.5 space-y-1 overflow-y-auto">
        {navGroups.map((group) => {
          if (group.roles && !group.roles.includes(role)) return null;
          const visibleItems = group.items.filter(
            (item) => !item.roles || item.roles.includes(role)
          );
          if (visibleItems.length === 0) return null;

          return (
            <div key={group.label}>
              {expanded && (
                <div
                  className="px-3 py-1 text-[10px] font-semibold uppercase tracking-widest"
                  style={{ color: 'var(--text-muted)' }}
                >
                  {group.label}
                </div>
              )}
              {visibleItems.map((item) => (
                <NavItem key={item.path} {...item} collapsed={!expanded} />
              ))}
            </div>
          );
        })}
      </nav>

      {/* Footer */}
      <div style={{ borderColor: 'var(--border-default)', color: 'var(--text-muted)' }} className="p-3 border-t text-xs shrink-0">
        {expanded ? (
          <div className="flex items-center justify-between">
            <span>v0.1.0</span>
            <span className="capitalize opacity-60">{role}</span>
          </div>
        ) : (
          <div className="text-center">v0.1.0</div>
        )}
      </div>
    </aside>
  );
}
