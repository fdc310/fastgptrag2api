import pymysql, os
from dotenv import load_dotenv

load_dotenv()

conn = pymysql.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", ""),
    charset="utf8mb4",
)
cur = conn.cursor()

cur.execute("SHOW TABLES")
tables = [r[0] for r in cur.fetchall()]

print("=== ALL TABLES ===")
for t in tables:
    print(t)

print()
keywords = ["robot", "setting"]
matched = [t for t in tables if any(k in t.lower() for k in keywords)]
print("=== MATCHED (robot/setting) ===")
for t in matched:
    print(t)
    cur.execute("SHOW CREATE TABLE `%s`" % t)
    print(cur.fetchone()[1])
    print()

cur.close()
conn.close()
