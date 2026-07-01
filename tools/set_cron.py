import subprocess
cron_line = "0 2 * * * /opt/plantos/scripts/backup/backup-all.sh\n"
subprocess.run(['crontab'], input=cron_line, text=True)
print("Cron set OK")
