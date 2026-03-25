# reset_django_db.py
import os
import subprocess
import shutil
import mysql.connector

# === CONFIG ===
DB_NAME = "srf_ims_db"
DB_USER = "root"        # replace with your MySQL user
DB_PASSWORD = "admin123"        # replace with your MySQL password
DB_HOST = "localhost"
APPS = ["clients", "services", "projects", "payments", "assignments", "salary",  "services", "staff",]  # all your apps

# === Step 1: Delete migration files ===
print("Deleting migration files...")
for app in APPS:
    migrations_path = os.path.join(os.getcwd(), app, "migrations")
    if os.path.exists(migrations_path):
        for filename in os.listdir(migrations_path):
            if filename != "__init__.py" and filename.endswith(".py"):
                os.remove(os.path.join(migrations_path, filename))
        print(f"Deleted migrations for app: {app}")

# === Step 2: Drop and recreate database ===
print(f"Dropping and recreating database '{DB_NAME}'...")
conn = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    port=3307  # default MySQL port

)
conn.autocommit = True
cursor = conn.cursor()
cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
cursor.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
cursor.close()
conn.close()
print("Database reset complete.")

# === Step 3: Run makemigrations ===
print("Making migrations...")
subprocess.run(["python", "manage.py", "makemigrations"], check=True)

# === Step 4: Apply migrations ===
print("Applying migrations...")
subprocess.run(["python", "manage.py", "migrate"], check=True)

print("✅ Reset complete! Your DB and migrations are clean.")