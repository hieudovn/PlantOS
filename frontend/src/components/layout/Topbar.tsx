export function Topbar() {
  return (
    <header className="h-14 border-b border-gray-800 flex items-center justify-between px-6 bg-gray-900/50">
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-400">Workspace:</span>
        <span className="text-sm font-medium">DEMO-PLANT</span>
      </div>
      <div className="text-xs text-gray-600">MVP Preview</div>
    </header>
  );
}
