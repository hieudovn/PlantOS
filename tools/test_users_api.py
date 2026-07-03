import urllib.request, json

# Login as admin
data = json.dumps({"username": "admin", "password": "PlantOS@2026!"}).encode()
req = urllib.request.Request("http://localhost:8000/api/v1/auth/login", data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
result = json.loads(resp.read())
token = result["access_token"]
print(f"Login: {result['username']} / {result['role']}")

# List users
req2 = urllib.request.Request("http://localhost:8000/api/v1/users", headers={"Authorization": f"Bearer {token}"})
resp2 = urllib.request.urlopen(req2)
users = json.loads(resp2.read())
for u in users:
    print(f"  {u['username']:12} {u['role']:10} {'active' if u['is_active'] else 'inactive'}")

# Login as engineer
data3 = json.dumps({"username": "engineer", "password": "PlantOS@2026!"}).encode()
req3 = urllib.request.Request("http://localhost:8000/api/v1/auth/login", data=data3, headers={"Content-Type": "application/json"})
resp3 = urllib.request.urlopen(req3)
eng = json.loads(resp3.read())
print(f"Engineer login: {eng['username']} / {eng['role']}")

# Engineer tries to list users (should fail 403)
req4 = urllib.request.Request("http://localhost:8000/api/v1/users", headers={"Authorization": f"Bearer {eng['access_token']}"})
try:
    urllib.request.urlopen(req4)
    print("ENGINEER ACCESSED USERS — BUG!")
except urllib.error.HTTPError as e:
    print(f"Engineer /users: {e.code} (expected 403)")
