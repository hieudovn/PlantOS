# Task: Users Page — Add Edge Access Column

> **Role:** Coder-Executioner (V4 Flash)
> **Scope:** Frontend-only — add Edge Access column to Center Users page
> **File:** `frontend/src/features/users/UserManagementPage.tsx`

---

## What to do

Add an **"Edge Access"** column to the Users table showing which edge nodes each user can access, with a simple inline toggle.

### API endpoints (already exist)

```
GET  /api/v1/edges/{edge_node_id}/users       → list assigned users
POST /api/v1/edges/{edge_node_id}/users       → assign user {user_id}
DELETE /api/v1/edges/{edge_node_id}/users/{user_id} → remove assignment
```

### Implementation

#### 1. Add imports

```tsx
import { Server } from "lucide-react";  // add to existing lucide imports
```

#### 2. Add edge nodes query

```tsx
// Inside UserManagementPage, add:
const { data: edgeNodes } = useQuery({
  queryKey: ["edge-nodes"],
  queryFn: () => fetchAPI<any[]>("/api/v1/edge-nodes"),
  refetchInterval: 30000,
});
```

#### 3. Add edge assignments query per user

Add a helper component `EdgeAccessCell` that fetches and displays assignments for a single user:

```tsx
function EdgeAccessCell({ userId }: { userId: string }) {
  const { data: edges = [] } = useQuery({
    queryKey: ["edge-nodes"],
    queryFn: () => fetchAPI<any[]>("/api/v1/edge-nodes"),
  });

  const { data: assignedEdges = [], isLoading } = useQuery({
    queryKey: ["edge-users", userId],
    queryFn: async () => {
      const results = await Promise.all(
        edges.map(async (edge: any) => {
          const users = await fetchAPI<any[]>(`/api/v1/edges/${edge.edge_node_id}/users`);
          const assigned = users.some((u: any) => u.user_id === userId);
          return { edgeId: edge.edge_node_id, assigned };
        })
      );
      return results;
    },
    enabled: edges.length > 0,
  });

  const queryClient = useQueryClient();

  const toggleMutation = useMutation({
    mutationFn: async ({ edgeId, assign }: { edgeId: string; assign: boolean }) => {
      if (assign) {
        return fetchAPI(`/api/v1/edges/${edgeId}/users`, {
          method: "POST",
          body: JSON.stringify({ user_id: userId }),
        });
      } else {
        return fetchAPI(`/api/v1/edges/${edgeId}/users/${userId}`, { method: "DELETE" });
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["edge-users", userId] });
    },
  });

  if (isLoading) return <span className="text-xs" style={{ color: 'var(--text-muted)' }}>...</span>;

  const activeCount = assignedEdges.filter(e => e.assigned).length;

  return (
    <div className="flex items-center gap-1 flex-wrap">
      {assignedEdges.map(({ edgeId, assigned }) => (
        <button
          key={edgeId}
          onClick={() => toggleMutation.mutate({ edgeId, assign: !assigned })}
          className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium transition-colors ${
            assigned
              ? 'border border-green-500/30'
              : 'border border-gray-500/20'
          }`}
          style={{
            color: assigned ? 'var(--status-normal)' : 'var(--text-muted)',
            backgroundColor: assigned ? 'var(--status-normal)' + '15' : 'transparent',
            borderColor: assigned ? 'var(--status-normal)' + '40' : 'var(--border-subtle)',
          }}
          title={assigned ? `Click to remove from ${edgeId}` : `Click to assign to ${edgeId}`}
        >
          <Server className="w-3 h-3" />
          {edgeId.replace('EDGEV2-', 'v2:').replace('edge-agent-', 'v1:')}
        </button>
      ))}
      {activeCount === 0 && (
        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>None</span>
      )}
    </div>
  );
}
```

#### 4. Add column header

After `<th ...>Status</th>`, add:

```tsx
<th className="text-left px-4 py-3 font-medium">Edge Access</th>
```

#### 5. Add column cell

After the Status `<td>`, before Actions `<td>`, add:

```tsx
<td className="px-4 py-3">
  <EdgeAccessCell userId={u.id} />
</td>
```

---

## Deploy

```bash
cd frontend
npm run build
scp -r dist/* plantos@103.97.132.249:/opt/plantos/frontend/dist/
ssh plantos@103.97.132.249 'docker cp /opt/plantos/frontend/dist/. plantos-frontend:/usr/share/nginx/html/'
```

---

## Expected Result

Each user row shows clickable edge node badges:
- Green badge = assigned (click to remove)
- Gray badge = not assigned (click to add)
- Shows edge node IDs as short labels (v2:PC-01, v1:01)
