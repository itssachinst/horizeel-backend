import sys
import os
import psycopg2

# Add the parent directory to sys.path for imports from app package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def check_saved_videos():
    """
    Check if the saved_videos table exists and print its structure and contents
    """
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="Sachi89",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
    
    # Check if the saved_videos table exists
    cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'saved_videos')")
    table_exists = cursor.fetchone()[0]
    
    if table_exists:
        print("The saved_videos table exists.")
        
        # Get table structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'saved_videos'
        """)
        columns = cursor.fetchall()
        print("\nTable structure:")
        for column in columns:
            print(f"  {column[0]} ({column[1]})")
        
        # Get table contents
        cursor.execute("SELECT * FROM saved_videos LIMIT 10")
        rows = cursor.fetchall()
        
        print(f"\nFound {len(rows)} saved videos:")
        for row in rows:
            print(f"  ID: {row[0]}, User ID: {row[1]}, Video ID: {row[2]}, Saved at: {row[3]}")
    else:
        print("The saved_videos table does not exist.")
    
    # Close the connection
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_saved_videos() 