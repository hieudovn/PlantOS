import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { getSignals } from "@/lib/api";
import { X, Search } from "lucide-react";

type Props = { selected: string[]; onChange: (ids: string[]) => void };

export function SignalMultiSelect({ selected, onChange }: Props) {
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);
  const { data: signals } = useQuery({
    queryKey: ["signals-all-hist"],
    queryFn: () => getSignals(),
    staleTime: 30000,
  });

  const filtered = useMemo(() => {
    if (!signals) return [];
    const q = search.toLowerCase();
    return signals.filter((s: any) =>
      s.signal_id.toLowerCase().includes(q) ||
      (s.display_name || s.signal_name).toLowerCase().includes(q) ||
      s.asset_id.toLowerCase().includes(q)
    );
  }, [signals, search]);

  const toggle = (id: string) => {
    if (selected.includes(id)) {
      onChange(selected.filter(x => x !== id));
    } else {
      onChange([...selected, id]);
    }
  };

  const remove = (id: string) => onChange(selected.filter(x => x !== id));

  return (
    <div className="relative">
      <div className="flex flex-wrap gap-1 mb-2">
        {selected.map(id => (
          <span key={id} className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-500/20 text-blue-300 rounded text-xs">
            {id}
            <button onClick={() => remove(id)}><X className="w-3 h-3" /></button>
          </span>
        ))}
      </div>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
        <input
          type="text"
          placeholder="Search signals by name, asset..."
          value={search}
          onChange={e => { setSearch(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
          className="w-full bg-gray-900 border border-gray-700 rounded pl-10 pr-3 py-2 text-sm"
        />
      </div>
      {open && (
        <div className="absolute z-50 mt-1 w-full bg-gray-900 border border-gray-700 rounded-lg shadow-xl max-h-64 overflow-auto">
          {filtered.length === 0 ? (
            <div className="px-3 py-4 text-sm text-gray-500 text-center">No signals found</div>
          ) : (
            filtered.map((s: any) => (
              <label key={s.signal_id} className="flex items-center gap-3 px-3 py-2 hover:bg-gray-800 cursor-pointer text-sm">
                <input
                  type="checkbox"
                  checked={selected.includes(s.signal_id)}
                  onChange={() => toggle(s.signal_id)}
                  className="rounded"
                />
                <span className="font-mono text-xs text-gray-400">{s.asset_id}</span>
                <span>{s.display_name || s.signal_name}</span>
                <span className="text-gray-600 text-xs ml-auto">{s.engineering_unit || "—"}</span>
              </label>
            ))
          )}
        </div>
      )}
      {open && <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />}
    </div>
  );
}
