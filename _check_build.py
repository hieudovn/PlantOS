import glob, os

# Check dist files
js_files = glob.glob("D:/Project/Github/PlantOS/frontend/dist/assets/index-*.js")
print("JS files:", len(js_files))
for f in js_files:
    with open(f, "rb") as fh:
        content = fh.read()
    has_auth_login = b"auth-login" in content
    has_token_version = b"tokenVersion" in content
    has_get_plants = b"getPlants" in content
    name = os.path.basename(f)
    print(f"  {name}: auth-login={has_auth_login}, tokenVersion={has_token_version}, getPlants={has_get_plants}")
