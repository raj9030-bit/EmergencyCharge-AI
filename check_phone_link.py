import glob
import os
import sqlite3

db_pattern = os.path.expanduser('~\\AppData\\Local\\Packages\\Microsoft.YourPhone*\\**\\*.db')
files = glob.glob(db_pattern, recursive=True)
print('Phone Link DB files found:', len(files))
for f in files:
    try:
        conn = sqlite3.connect(f)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        print(os.path.basename(f), '->', tables)
        for t in tables:
            if any(k in t.lower() for k in ['device', 'battery', 'phone', 'status', 'power']):
                cur.execute(f"SELECT * FROM {t} LIMIT 5;")
                print(f"Table {t} sample:", cur.fetchall())
    except Exception as e:
        pass
