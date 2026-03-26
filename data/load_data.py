"""
Script to manually load data into SQLite database.
Run this if you want to pre-process the data before starting the server.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import init_database

if __name__ == "__main__":
    data_path = os.path.join(os.path.dirname(__file__), 'dataset.xlsx')
    if not os.path.exists(data_path):
        print(f"Dataset not found at {data_path}")
        print("Please download from: https://drive.google.com/file/d/1UqaLbFaveV-3MEuiUrzKydhKmkeC1iAL/view")
        sys.exit(1)

    print(f"Loading data from {data_path}...")
    success = init_database(data_path)
    if success:
        print("Data loaded successfully!")
    else:
        print("Failed to load data.")