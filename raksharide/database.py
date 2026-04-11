import mysql.connector
from mysql.connector import Error

def get_db_connection():
    """
    Establish and return a connection to the MySQL database.
    Returns the connection object if successful, or None if failed.
    """
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='raksharide'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL Database: {e}")
        return None
