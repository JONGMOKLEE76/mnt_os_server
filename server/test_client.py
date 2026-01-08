import requests
import pandas as pd
import json
from tqdm import tqdm

# Sample data based on the image provided by the user
data = [
    {
        "Planweek": "202401",
        "Created_at": "2024-01-01",
        "Division": "MNT",
        "From Site": "EECK",
        "Region": "EU",
        "To Site": "LGECK",
        "Mapping Model.Suffix": "MODEL1.SUFFIX1",
        "Rep PMS": "PMS1",
        "Category": "CAT1",
        "Frozen": "N",
        "Week Name": "W1",
        "SP": 100
    },
    {
        "Planweek": "202401",
        "Created_at": "2024-01-01",
        "Division": "MNT",
        "From Site": "EEAK",
        "Region": "CIS",
        "To Site": "LGEAK",
        "Mapping Model.Suffix": "MODEL2.SUFFIX2",
        "Rep PMS": "PMS2",
        "Category": "CAT2",
        "Frozen": "N",
        "Week Name": "W1",
        "SP": 200
    }
]

BASE_URL = "http://127.0.0.1:5000"

def check_server_status():
    print(f"Checking server status at {BASE_URL}...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is ONLINE: {data.get('message')}")
            return True
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Server is OFFLINE or unreachable: {str(e)}")
        return False

def send_large_dataframe(df, chunk_size=5000):
    """
    Splits a large DataFrame into chunks and sends them to the server sequentially.
    """
    total_rows = len(df)
    chunks = [df[i:i + chunk_size] for i in range(0, total_rows, chunk_size)]
    total_chunks = len(chunks)
    
    print(f"\n🚀 Starting large upload: {total_rows} rows in {total_chunks} chunks.")
    endpoint = f"{BASE_URL}/upsert_shipment_plan"
    
    # Use tqdm for progress bar
    for i, chunk in enumerate(tqdm(chunks, desc="Uploading", unit="chunk")):
        data = chunk.to_dict(orient='records')
        try:
            response = requests.post(endpoint, json=data)
            if response.status_code != 200:
                print(f"\n❌ Chunk {i+1} failed ({response.status_code}): {response.text}")
                return False
        except Exception as e:
            print(f"\n❌ Error during chunk {i+1}: {str(e)}")
            return False
            
    print(f"\n✨ Successfully uploaded {total_rows} rows.\n")
    return True

def test_upsert():
    print("\nStarting upsert test...")
    endpoint = f"{BASE_URL}/upsert_shipment_plan"
    print("Sending initial data...")
    response = requests.post(endpoint, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    # Modify one record to test update
    updated_data = [
        {
            "Planweek": "202401",
            "Created_at": "2024-01-01",
            "Division": "MNT",
            "From Site": "EECK",
            "Region": "EU",
            "To Site": "LGECK",
            "Mapping Model.Suffix": "MODEL1.SUFFIX1",
            "Rep PMS": "PMS1",
            "Category": "CAT1",
            "Frozen": "N",
            "Week Name": "W1",
            "SP": 150  # Changed from 100 to 150
        }
    ]

    print("\nSending updated data (testing update)...")
    endpoint = f"{BASE_URL}/upsert_shipment_plan"
    response = requests.post(endpoint, json=updated_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    if check_server_status():
        # Example of sending small test data
        test_upsert()
        
        # Example of how to send a large DataFrame (commented out for safety)
        # large_df = pd.read_excel("your_large_file.xlsx")
        # send_large_dataframe(large_df)
    else:
        print("Aborting tests because server is not responding.")
