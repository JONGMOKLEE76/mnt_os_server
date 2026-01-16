import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mnt_data.db")

def check_users():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, userid, email, status, is_admin FROM users")
        users = cursor.fetchall()
        print("Users in database:")
        for user in users:
            print(user)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_users()
