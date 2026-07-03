import urllib.request, json
data = json.dumps({"username": "admin", "password": "PlantOS@2026!"}).encode()
req = urllib.request.Request("http://localhost:8000/api/v1/auth/login", data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
print(resp.read().decode())
