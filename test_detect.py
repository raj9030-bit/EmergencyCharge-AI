import subprocess
import json
import time

t0 = time.time()
script = """
Get-PnpDevice -Class WPD -PresentOnly | Select-Object FriendlyName, InstanceId, Status | ConvertTo-Json -Compress
"""
res = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script], capture_output=True, text=True, timeout=5.0)
print(f"Time: {time.time()-t0:.2f}s")
print("WPD devices:", res.stdout.strip())
