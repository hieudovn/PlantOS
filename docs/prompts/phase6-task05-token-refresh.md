# Phase 6 — Task 6-05: JWT Token Refresh & Sliding Expiration

> **Designer:** V4 Pro | **Date:** 2026-07-01 | **Priority:** P1

## Context

JWT token hiện có expiry cố định 24h. Sau khi hết hạn, user bị redirect về `/login` và mất toàn bộ state (đang xem Historian, đang filter signals...). Cần **refresh token** hoặc **sliding expiration** để user không bị logout khi đang hoạt động.

## Current Flow (vấn đề)

```
User login → JWT (expiry=24h) → localStorage
                                           │
24h sau ──────────────────────────────────►│
                                           ▼
                          API returns 401
                                           │
                                           ▼
                          fetchAPI: clear token → redirect /login
                                           │
                                           ▼
                          User mất toàn bộ state, phải login lại
```

## Target Flow (sliding expiration)

```
User login → JWT (expiry=1h) + refresh_token (expiry=7d)
                                           │
Mỗi API call ────────────────────────────►│
                                           ▼
                          Backend: check exp < 30min?
                                           │
                          YES → return new token in X-New-Token header
                                           │
                          Frontend: update localStorage
                                           │
                          User luôn được gia hạn khi active
```

## Design Decision

Dùng **sliding expiration** (đơn giản hơn refresh token, phù hợp MVP):

- JWT expiry: **1 giờ** (giảm từ 24h)
- Nếu token còn < 30 phút → backend trả kèm token mới trong response header
- Frontend tự động cập nhật token từ header
- Không cần refresh token endpoint riêng

## Implementation Checklist

- [ ] MODIFY `backend/app/core/config.py` — JWT_EXPIRE_HOURS=1, thêm JWT_REFRESH_THRESHOLD_MINUTES=30
- [ ] MODIFY `backend/app/core/security.py` — thêm `should_refresh_token()` helper
- [ ] MODIFY `backend/app/middleware/auth.py` — set `X-New-Token` header khi token sắp hết hạn
- [ ] MODIFY `frontend/src/lib/api.ts` — đọc `X-New-Token` header và cập nhật localStorage
- [ ] VERIFY: login, đợi > 30 phút, API call vẫn work và token được refresh
- [ ] UPDATE `docs/prompts/phase6-task01-authentication.md` — ghi nhận thay đổi

## Detailed Instructions

### 1. Backend: Config

File: `backend/app/core/config.py`

```python
# Thay đổi:
JWT_EXPIRE_HOURS: int = 1       # 1 giờ (was 24)
# Thêm:
JWT_REFRESH_THRESHOLD_MINUTES: int = 30  # Refresh khi còn < 30 phút
```

### 2. Backend: Security helper

File: `backend/app/core/security.py`

Thêm function:

```python
from datetime import datetime, timezone

def should_refresh_token(payload: dict) -> bool:
    """Return True if token should be refreshed (expiring soon)."""
    exp = payload.get("exp")
    if not exp:
        return False
    expire_time = datetime.fromtimestamp(exp, tz=timezone.utc)
    remaining = expire_time - datetime.now(timezone.utc)
    threshold = timedelta(minutes=settings.JWT_REFRESH_THRESHOLD_MINUTES)
    return remaining < threshold
```

### 3. Backend: Middleware

File: `backend/app/middleware/auth.py`

Sau khi decode token thành công, kiểm tra refresh:

```python
# Trong AuthMiddleware.dispatch(), sau dòng:
# request.state.user = payload

# Thêm:
from app.core.security import should_refresh_token, create_access_token

# ... sau khi decode thành công ...
if should_refresh_token(payload):
    new_token = create_access_token(payload["sub"], payload["username"])
    # Store for later use in response
    request.state.new_token = new_token

response = await call_next(request)

# Add refresh header if new token was generated
if hasattr(request.state, 'new_token'):
    response.headers["X-New-Token"] = request.state.new_token

return response
```

> **Quan trọng:** Coder cần đọc file `auth.py` thực tế và adapt logic — hiện tại middleware trả về response trực tiếp hoặc gọi `call_next`. Cần đảm bảo header được gắn vào response từ `call_next`.

### 4. Frontend: API client

File: `frontend/src/lib/api.ts`

Trong `fetchAPI`, sau `const res = await fetch(...)`:

```typescript
// Check for refreshed token
const newToken = res.headers.get("X-New-Token");
if (newToken) {
  localStorage.setItem("plantos_token", newToken);
}

// ... existing status handling ...
```

### 5. Validation

| Check | Expected |
|---|---|
| Login | Nhận token, JWT expiry = 1h |
| API call ngay sau login | Không có X-New-Token header |
| API call sau > 30 phút | Response có X-New-Token header |
| Frontend cập nhật token | localStorage có token mới |
| API call với token cũ (đã refresh) | Vẫn hoạt động (token cũ còn valid đến khi hết 1h) |
| Token hết hạn hoàn toàn (>1h không dùng) | 401 → redirect /login (đúng behavior) |

## Notes

- Không thay đổi LoginPage — flow login giữ nguyên
- Không cần database migration — JWT là stateless
- API Key auth không bị ảnh hưởng (không có expiry)
- Token refresh hoạt động với MỌI API call (không chỉ những endpoint cụ thể)
