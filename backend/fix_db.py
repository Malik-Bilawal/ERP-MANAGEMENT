import MySQLdb

try:
    # Connect to the SERVER (not the database, since it doesn't exist yet)
    conn = MySQLdb.connect(
        host="127.0.0.1",
        user="root",
        passwd="", 
        port=3307
    )
    cursor = conn.cursor()
    # Create the missing database
    cursor.execute("CREATE DATABASE IF NOT EXISTS srf_ims_db")
    print("Successfully created srf_ims_db on Port 3307!")
    conn.close()
except Exception as e:
    print(f"Error: {e}")