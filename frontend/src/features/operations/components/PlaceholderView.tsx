import { Factory } from "lucide-react";

export function PlaceholderView({
  title,
  message,
}: {
  title: string;
  message: string;
}) {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center" style={{ color: 'var(--text-muted)' }}>
        <Factory className="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p className="text-lg mb-1" style={{ color: 'var(--text-secondary)' }}>{title}</p>
        <p className="text-sm">{message}</p>
      </div>
    </div>
  );
}
