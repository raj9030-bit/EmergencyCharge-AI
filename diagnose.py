import subprocess
import psutil
import json

# 1. Real Laptop Model and Manufacturer
res_mfr = subprocess.run(['powershell', '-NoProfile', '-Command', '(Get-CimInstance Win32_ComputerSystem).Manufacturer'], capture_output=True, text=True)
res_mdl = subprocess.run(['powershell', '-NoProfile', '-Command', '(Get-CimInstance Win32_ComputerSystem).Model'], capture_output=True, text=True)
laptop_model = f"{res_mfr.stdout.strip()} {res_mdl.stdout.strip()}".strip()

# 2. Real Laptop Battery
bat = psutil.sensors_battery()
laptop_pct = bat.percent if bat else None
plugged = bat.power_plugged if bat else None

print('=== REAL LAPTOP HARDWARE ===')
print('Model:', laptop_model)
print('Battery %:', laptop_pct)
print('Power Plugged:', plugged)

# 3. Check ADB
adb = r'C:\Users\lenovo\AppData\Local\Android\Sdk\platform-tools\adb.exe'
res_adb = subprocess.run([adb, 'devices', '-l'], capture_output=True, text=True)
print('\n=== ADB OUTPUT ===')
print(res_adb.stdout.strip())

# 4. Check all PnP USB devices
ps_pnp = 'Get-PnpDevice -PresentOnly | Select-Object FriendlyName, InstanceId, Class | ConvertTo-Json -Compress'
res_pnp = subprocess.run(['powershell', '-NoProfile', '-Command', ps_pnp], capture_output=True, text=True)

print('\n=== CONNECTED USB / PORTABLE / PHONE DEVICES ===')
try:
    data = json.loads(res_pnp.stdout)
    if isinstance(data, dict):
        data = [data]
    found = False
    for d in data:
        fn = d.get('FriendlyName') or ''
        iid = d.get('InstanceId') or ''
        cls = d.get('Class') or ''
        if cls in ('WPD', 'PortableDevice', 'USB', 'Bluetooth') or any(k in fn.lower() or k in iid.lower() for k in ['phone', 'mobile', 'samsung', 'apple', 'pixel', 'xiaomi', 'oneplus', 'vivo', 'oppo', 'realme', 'huawei', 'motorola', 'mtp', 'android']):
            print(f"[{cls}] {fn} | ID: {iid}")
            found = True
    if not found:
        print("No phone/portable device detected in PnP.")
except Exception as e:
    print("Error parsing PnP:", e)
