import subprocess, os

# Build frontend
os.chdir("D:/Project/Github/PlantOS/frontend")
result = subprocess.run(["npm", "run", "build"], capture_output=True, text=True, timeout=120)
print("STDOUT:", result.stdout[-500:] if result.stdout else "")
print("STDERR:", result.stderr[-500:] if result.stderr else "")
print("Return code:", result.returncode)

# Check output
import glob
js_files = glob.glob("D:/Project/Github/PlantOS/frontend/dist/assets/index-*.js")
print("\nJS bundles:")
for f in js_files:
    with open(f, "rb") as fh:
        c = fh.read()
    print(f"  {f.split(chr(92))[-1]}: {len(c)} bytes, auth-login={b'auth-login' in c}")
