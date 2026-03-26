"""
Run this on Render to download the dataset.
Or upload the business_data.db directly.
"""
import os
import subprocess

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'sap-o2c-data')

if not os.path.exists(DATA_DIR):
    print("Data directory not found. Please upload business_data.db manually.")
    print("Or place sap-o2c-data folder in data/")