import os
import sys

try:
    import pymysql
except ImportError:
    print("pymysql not installed, run: uv add pymysql")
    sys.exit(1)

from dotenv import load_dotenv

load_dotenv()

host = os.getenv("DB_HOST", "localhost")
port = int(os.getenv("DB_PORT", "3306"))
user = os.getenv("DB_USER", "root")
password = os.getenv("DB_PASSWORD", "")
database = os.getenv("DB_NAME", "")

if not database:
    print("DB_NAME not set in .env")
    sys.exit(1)

conn = pymysql.connect(host=host, port=port, user=user, password=password, database=database, charset="utf8mb4")
cur = conn.cursor()

# List all tables
cur.execute("SHOW TABLES")
tables = [row[0] for row in cur.fetchall()]

print(f"=== Database: {database} ===")
print(f"=== Tables: {len(tables)} ===\n")

for table in tables:
    cur.execute(f"SHOW CREATE TABLE `{table}`")
    create_sql = cur.fetchone()[1]
    print(f"--- Table: {table} ---")
    print(create_sql)
    print()

    # Row count
    cur.execute(f"SELECT COUNT(*) FROM `{table}`")
    count = cur.fetchone()[0]
    print(f"  Rows: {count}\n")

cur.close()
conn.close()
