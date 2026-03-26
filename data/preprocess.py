"""
Data preprocessing script.
Analyzes the dataset and prints schema information.
"""
import pandas as pd
import sys
import os

def analyze_dataset(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    xls = pd.ExcelFile(file_path)
    print(f"Excel file: {file_path}")
    print(f"Sheets: {xls.sheet_names}")
    print("=" * 60)

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        print(f"\n--- Sheet: {sheet_name} ---")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Types:")
        for col in df.columns:
            non_null = df[col].notna().sum()
            print(f"    {col}: {df[col].dtype} ({non_null} non-null)")
        print(f"  Sample (first 2 rows):")
        print(df.head(2).to_string(index=False))
        print()

if __name__ == "__main__":
    data_path = os.path.join(os.path.dirname(__file__), 'dataset.xlsx')
    analyze_dataset(data_path)