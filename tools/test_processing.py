import httpx
BASE = "http://127.0.0.1:8011"
r = httpx.post(f"{BASE}/api/auth/login", json={"username":"admin","password":"Test@1234"})
c = dict(r.cookies)
csrf = c.get("plantos_csrf","")

# Create
r2 = httpx.post(f"{BASE}/api/processing/profiles", cookies=c, json={
    "profile_id": "test_scale", "name": "Test Scale",
    "steps": [{"type": "scale_offset", "params": {"scale": 0.1, "offset": 0}, "order": 1}]
}, headers={"X-CSRF-Token": csrf})
print("CREATE:", r2.status_code, r2.text[:200])

# Preview
r3 = httpx.post(f"{BASE}/api/processing/profiles/test_scale/preview", cookies=c, json={"raw_samples": [723, 721, 718, 725]}, headers={"X-CSRF-Token": csrf})
print("PREVIEW:", r3.status_code, r3.text[:300])

# List
r4 = httpx.get(f"{BASE}/api/processing/profiles", cookies=c)
print("LIST:", r4.status_code, r4.text[:200])
