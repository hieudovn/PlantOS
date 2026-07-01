import subprocess, os

# Deploy backup scripts to VPS
scripts = [
    "D:/Project/Github/PlantOS/scripts/backup/pg-backup.sh",
    "D:/Project/Github/PlantOS/scripts/backup/tdengine-backup.sh", 
    "D:/Project/Github/PlantOS/scripts/backup/backup-all.sh"
]

key_path = os.path.expanduser("~/.ssh/plantos_vps")
remote_path = "/opt/plantos/scripts/backup/"

# SCP all files
for script in scripts:
    cmd = f'scp -i "{key_path}" "{script}" plantos@103.97.132.249:"{remote_path}"'
    print(f"Uploading {os.path.basename(script)}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  OK")
    else:
        print(f"  FAIL: {result.stderr}")

# SSH to chmod
ssh_cmd = f'ssh -i "{key_path}" plantos@103.97.132.249 "chmod +x /opt/plantos/scripts/backup/*.sh && echo CHMOD_DONE"'
print("Setting executable permissions...")
result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=10)
if result.returncode == 0:
    print(f"  {result.stdout.strip()}")
else:
    print(f"  FAIL: {result.stderr}")

print("\nDeployment complete!")
