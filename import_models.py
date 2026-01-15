import pandas as pd
import sqlite3
import os

# Configuration
csv_file_path = 'd:\\MNT Shipment data server\\models.csv'
db_file_path = 'd:\\MNT Shipment data server\\mnt_data.db'
table_name = 'os_models'

def fix_encoding_and_import():
    print(f"Reading {csv_file_path}...")
    
    # Try reading with cp949 (common for Korean CSVs)
    try:
        df = pd.read_csv(csv_file_path, encoding='cp949')
        print("Successfully read file with cp949 encoding.")
    except Exception as e:
        print(f"Failed to read with cp949: {e}")
        # Fallback to euc-kr if needed, or just fail
        try:
            df = pd.read_csv(csv_file_path, encoding='euc-kr')
            print("Successfully read file with euc-kr encoding.")
        except Exception as e2:
            print(f"Failed to read with euc-kr: {e2}")
            return

    # Save back as UTF-8 for future use (optional, but good for the user)
    # We will overwrite the file with utf-8-sig to make it readable in Excel and editors
    print(f"Saving {csv_file_path} as UTF-8...")
    df.to_csv(csv_file_path, index=False, encoding='utf-8-sig')
    
    # Import to Database
    print(f"Connecting to database {db_file_path}...")
    conn = sqlite3.connect(db_file_path)
    
    print(f"Importing data into table '{table_name}'...")
    # if_exists='replace' will drop the table if it exists and create a new one
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    
    # Verify
    cursor = conn.cursor()
    cursor.execute(f"SELECT count(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"Successfully imported {count} rows into '{table_name}'.")
    
    # Show sample
    print("Sample data from DB:")
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
        
    conn.close()
    print("Done.")

if __name__ == "__main__":
    fix_encoding_and_import()
