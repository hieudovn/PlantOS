import { BarChart3 } from "lucide-react";

export function ReportsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Reports</h1>
      <div style={{ backgroundColor: 'var(--surface-card)', borderColor: 'var(--border-default)' }} className="rounded-lg border p-8 text-center">
        <BarChart3 className="w-12 h-12 mx-auto mb-3" style={{ color: 'var(--text-muted)' }} />
        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Reporting dashboard coming soon.</p>
        <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
          Scheduled reports, KPI summaries, cost/quality trends, and exportable PDFs will appear here.
        </p>
      </div>
    </div>
  );
}
