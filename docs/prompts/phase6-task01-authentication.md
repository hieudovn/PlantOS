# Phase 6 — Task 6-01: API Authentication (JWT + API Key)

> **Designer:** DeepSeek V4 Pro | **Date:** 2026-07-01

## Context

PlantOS API hiện mở hoàn toàn — không có authentication. Cần thêm JWT auth cho UI users và API Key cho Edge Agent / external clients.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Nginx :80                       │
│  /api/*  →  Backend :8000                       │
│  /       →  Frontend static                     │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│              Backend :8000                       │
│                                                  │
│  Middleware: JWT Auth (all /api/v1/*)            │
│  Exceptions: /health, /api/v1/auth/login         │
│                                                  │
│  Middleware: API Key Auth (for Edge Agent)        │
│  Header: X-API-Key                               │
└─────────────────────────────────────────────────┘
                    │
          ┌────────┴────────┐
          ▼                 ▼
    UI User (JWT)    Edge Agent (API Key)
    Login → Token     Config: api_key
```

## Auth Methods

| Method | Use Case | Header | Expiry |
|---|---|---|---|
| **JWT Token** | UI login (username/password) | `Authorization: Bearer <token>` | 24h |
| **API Key** | Edge Agent, external clients | `X-API-Key: <key>` | Permanent (revocable) |

## Implementation Checklist

- [ ] CREATE `backend/app/modules/auth/` — module: models, service, router
- [ ] CREATE `backend/app/core/security.py` — JWT utils, password hashing
- [ ] CREATE `backend/app/middleware/auth.py` — JWT + API Key middleware
- [ ] MODIFY `backend/app/main.py` — register auth middleware
- [ ] MODIFY `backend/app/core/config.py` — add JWT_SECRET, API_KEYS settings
- [ ] MODIFY `frontend/src/lib/api.ts` — add Bearer token to requests
- [ ] CREATE `frontend/src/features/auth/LoginPage.tsx` — login form
- [ ] MODIFY `frontend/src/routes/index.tsx` — add /login route
- [ ] MODIFY `edge/agent/config.yaml` — add api_key field
- [ ] MODIFY `edge/agent/sync.py` — add X-API-Key header
- [ ] BUILD frontend → deploy VPS

## Detailed Instructions

### 1. Backend: JWT + API Key

#### `backend/app/core/config.py` (MODIFY)

Thêm:

```python
JWT_SECRET: str = "plantos-dev-secret-change-in-production"
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_HOURS: int = 24
API_KEYS: str = ""  # comma-separated: "key1,key2"
```

#### `backend/app/core/security.py` (CREATE)

```python
"""JWT token utilities and password hashing."""

import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id: str, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {"sub": user_id, "username": username, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
```

#### `backend/app/middleware/auth.py` (CREATE)

```python
"""Authentication middleware — JWT + API Key."""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.security import decode_access_token
from app.core.config import settings

PUBLIC_PATHS = ["/health", "/api/v1/auth/login", "/docs", "/openapi.json"]

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Skip public paths
        if any(path.startswith(p) for p in PUBLIC_PATHS):
            return await call_next(request)
        
        # API Key auth (for Edge Agent, external clients)
        api_key = request.headers.get("X-API-Key")
        if api_key and settings.API_KEYS:
            valid_keys = [k.strip() for k in settings.API_KEYS.split(",") if k.strip()]
            if api_key in valid_keys:
                return await call_next(request)
        
        # JWT auth (for UI users)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = decode_access_token(token)
            if payload:
                request.state.user = payload
                return await call_next(request)
        
        raise HTTPException(status_code=401, detail="Invalid or missing authentication")
```

#### `backend/app/main.py` (MODIFY)

```python
from app.middleware.auth import AuthMiddleware

app.add_middleware(AuthMiddleware)
```

#### `backend/app/modules/auth/router.py` (CREATE)

```python
"""Auth API — login, token refresh."""

from fastapi import APIRouter, HTTPException
from app.core.security import create_access_token, verify_password
from app.db import get_session

router = APIRouter()

# Simple in-memory user store (replace with DB in future)
_USERS = {
    "admin": {"password": "$2b$12$...placeholder...", "role": "admin"},
    "engineer": {"password": "$2b$12$...placeholder...", "role": "engineer"},
}

@router.post("/auth/login")
def login(username: str, password: str):
    user = _USERS.get(username)
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(username, username)
    return {"access_token": token, "token_type": "bearer", "username": username}
```

> **Note:** Sử dụng `passlib[bcrypt]` + bcrypt để hash password. Tạo user mặc định `admin/admin` bằng `hash_password("admin")`.

### 2. Frontend: Login Page

#### `frontend/src/features/auth/LoginPage.tsx` (CREATE)

```tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";

export function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const res = await fetch("/api/v1/auth/login?" + new URLSearchParams({ username, password }), { method: "POST" });
      if (!res.ok) throw new Error("Invalid credentials");
      const data = await res.json();
      localStorage.setItem("plantos_token", data.access_token);
      localStorage.setItem("plantos_user", data.username);
      navigate("/");
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <form onSubmit={handleLogin} className="bg-gray-900 p-8 rounded-lg border border-gray-800 w-96">
        <h1 className="text-xl font-bold mb-6">🏭 PlantOS Login</h1>
        {error && <div className="bg-red-900/50 text-red-300 p-2 rounded mb-4 text-sm">{error}</div>}
        <input type="text" placeholder="Username" value={username} onChange={e => setUsername(e.target.value)}
          className="w-full p-2 mb-3 bg-gray-800 border border-gray-700 rounded text-white" />
        <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)}
          className="w-full p-2 mb-4 bg-gray-800 border border-gray-700 rounded text-white" />
        <button type="submit" className="w-full p-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          Login
        </button>
      </form>
    </div>
  );
}
```

#### `frontend/src/lib/api.ts` (MODIFY)

Thêm Bearer token vào mọi request:

```typescript
async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem("plantos_token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  
  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    localStorage.removeItem("plantos_token");
    window.location.href = "/login";
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API ${res.status}`);
  }
  return res.json();
}
```

### 3. Edge Agent: API Key

#### `edge/agent/config.yaml` (MODIFY)

```yaml
api_key: {EDGE_API_KEY}
```

#### `edge/agent/sync.py` (MODIFY)

Thêm header:

```python
resp = await client.post(self.ingest_url, json={
    "source": self.edge_node_id,
    "measurements": unsynced,
}, headers={"X-API-Key": self.api_key})
```

#### `backend/.env` or docker-compose environment:

```yaml
API_KEYS: {EDGE_API_KEY}
```

---

## Security Notes

- JWT_SECRET phải được thay đổi trong production (dùng env var, không hardcode)
- API keys nên được lưu trong DB thay vì env var comma-separated (future)
- bcrypt rounds: mặc định 12 (passlib)
- HTTPS bắt buộc cho production (Phase 6-04)

## Validation

```bash
# 1. Test unauthenticated request (should fail)
curl http://103.97.132.249/api/v1/plants
# → 401 Unauthorized

# 2. Test API key auth (Edge Agent)
curl -H "X-API-Key: {EDGE_API_KEY}" http://103.97.132.249/api/v1/plants
# → 200 OK

# 3. Login UI
open http://103.97.132.249/login
# → Login with admin/admin

# 4. Test JWT
curl -X POST "http://103.97.132.249/api/v1/auth/login?username=admin&password=admin"
# → {"access_token":"eyJ...","token_type":"bearer"}

# 5. Use JWT token
curl -H "Authorization: Bearer eyJ..." http://103.97.132.249/api/v1/plants
# → 200 OK
```

---

## Files Summary

| # | File | Action | Description |
|---|------|--------|-------------|
| 1 | `backend/app/core/security.py` | CREATE | JWT + password hashing |
| 2 | `backend/app/core/config.py` | MODIFY | JWT_SECRET, API_KEYS |
| 3 | `backend/app/middleware/auth.py` | CREATE | Auth middleware |
| 4 | `backend/app/main.py` | MODIFY | Register middleware |
| 5 | `backend/app/modules/auth/router.py` | CREATE | Login endpoint |
| 6 | `backend/app/modules/auth/__init__.py` | CREATE | Package init |
| 7 | `frontend/src/features/auth/LoginPage.tsx` | CREATE | Login UI |
| 8 | `frontend/src/routes/index.tsx` | MODIFY | Add /login route |
| 9 | `frontend/src/lib/api.ts` | MODIFY | Bearer token |
| 10 | `edge/agent/config.yaml` | MODIFY | Add api_key |
| 11 | `edge/agent/sync.py` | MODIFY | X-API-Key header |
| 12 | `deployment/docker-compose.yml` | MODIFY | API_KEYS env var |
| 13 | `backend/requirements.txt`/`pyproject.toml` | MODIFY | Add passlib, bcrypt, pyjwt |

## Handoff to Coder

```
Đọc: docs/prompts/phase6-task01-authentication.md
13 files (6 CREATE, 7 MODIFY).
JWT auth cho UI + API Key cho Edge Agent.
Middleware pattern: check public paths → API key → JWT → 401.
Build frontend + rebuild backend Docker + deploy VPS.
Default user: admin/admin.
Validate: curl không auth → 401; curl + API key → 200; login UI → token.
```
