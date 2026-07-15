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

keywords = ["member", "dataset", "device", "wristband", "company"]
key_tables = [t for t in tables if any(k in t.lower() for k in keywords)]

for t in key_tables:
    cur.execute("SHOW CREATE TABLE `%s`" % t)
    row = cur.fetchone()
    print("--- %s ---" % t)
    print(row[1])
    print()
    cur.execute("SELECT COUNT(*) FROM `%s`" % t)
    print("  Rows: %d" % cur.fetchone()[0])
    print()

cur.close()
conn.close()
