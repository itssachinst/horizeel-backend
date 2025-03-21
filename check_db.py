import sqlite3
import os

def main():
    # List all databases in the current directory
    print("Available databases:")
    db_files = [f for f in os.listdir('.') if f.endswith('.db')]
    for db in db_files:
        print(f"- {db}")
    
    # Connect to the database
    db_file = 'videos.db'
    if not os.path.exists(db_file):
        print(f"Database file {db_file} not found!")
        return
        
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    
    # Check tables
    print("\nTables in database:")
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    for table in tables:
        print(f"- {table[0]}")
    
    # Check user table if it exists
    if ('user',) in tables or ('users',) in tables:
        user_table = 'user' if ('user',) in tables else 'users'
        print(f"\nUsers in {user_table} table:")
        try:
            cur.execute(f"PRAGMA table_info({user_table})")
            columns = [col[1] for col in cur.fetchall()]
            print(f"Columns: {columns}")
            
            # Get sample users
            cur.execute(f"SELECT * FROM {user_table} LIMIT 5")
            users = cur.fetchall()
            for user in users:
                print(user)
        except sqlite3.OperationalError as e:
            print(f"Error: {e}")
    
    conn.close()

if __name__ == "__main__":
    main() 