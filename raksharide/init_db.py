import mysql.connector

try:
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password=''
    )
    cursor = connection.cursor()

    print("Re-creating Database from scratch to ensure a clean slate...")
    cursor.execute("DROP DATABASE IF EXISTS raksharide;")
    cursor.execute("CREATE DATABASE raksharide;")
    cursor.execute("USE raksharide;")

    # Read schema
    with open('database/schema.sql', 'r') as f:
        sql_script = f.read()
    
    # Execute multi-statement SQL
    for statement in sql_script.split(';'):
        if statement.strip():
            cursor.execute(statement)

    connection.commit()
    print("Database `raksharide` successfully recreated and tables instantiated!")
    
    cursor.close()
    connection.close()

except Exception as e:
    print(f"Error initializing DB: {e}")
