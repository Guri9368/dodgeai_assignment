import sqlite3
import pandas as pd
import os
import json
import glob
from .config import settings

DB_PATH = settings.DATABASE_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def clean_column_name(col):
    col = str(col).strip()
    col = col.replace(' ', '_').replace('.', '_').replace('/', '_')
    col = col.replace('-', '_').replace('(', '').replace(')', '')
    col = col.replace('#', 'num').replace('%', 'pct')
    col = ''.join(c if c.isalnum() or c == '_' else '_' for c in col)
    col = col.strip('_')
    if col and col[0].isdigit():
        col = 'col_' + col
    return col if col else 'unnamed_col'


def load_jsonl_file(file_path):
    """Load a JSONL file (one JSON object per line)."""
    records = []
    encodings = ['utf-8', 'latin-1', 'cp1252']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            break
        except UnicodeDecodeError:
            continue
    return records


def init_database(data_path: str = None):
    """Load all JSONL files from the SAP dataset into SQLite."""
    if data_path is None:
        data_path = settings.DATA_FILE_PATH

    if not os.path.exists(data_path):
        print(f"ERROR: Data path not found: {data_path}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Absolute path tried: {os.path.abspath(data_path)}")
        return False

    # Remove old database
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed old database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    table_info = {}

    try:
        print(f"\nLoading data from: {os.path.abspath(data_path)}")
        print("=" * 60)

        # Find all JSONL files recursively
        jsonl_files = []
        for root, dirs, files in os.walk(data_path):
            for file in files:
                if file.endswith('.jsonl') or file.endswith('.json'):
                    jsonl_files.append(os.path.join(root, file))

        if not jsonl_files:
            print(f"No .jsonl or .json files found in {data_path}")
            # Show what IS there
            for root, dirs, files in os.walk(data_path):
                for f in files:
                    print(f"  Found: {os.path.join(root, f)}")
            return False

        print(f"Found {len(jsonl_files)} data files\n")

        for file_path in sorted(jsonl_files):
            # Use the parent folder name as table name
            parent_folder = os.path.basename(os.path.dirname(file_path))
            table_name = parent_folder.lower().strip()
            table_name = ''.join(
                c if c.isalnum() or c == '_' else '_' for c in table_name
            )
            table_name = table_name.strip('_')

            if not table_name:
                table_name = os.path.splitext(
                    os.path.basename(file_path)
                )[0].lower()

            # Load the JSONL file
            records = load_jsonl_file(file_path)

            if not records:
                print(f"  SKIP {file_path} (empty or unreadable)")
                continue

            # Convert to DataFrame
            df = pd.DataFrame(records)

            # Clean column names
            df.columns = [clean_column_name(col) for col in df.columns]

           # Remove completely empty columns
            df = df.dropna(axis=1, how='all')

            # ✅ FIX: Serialize dict/list columns to JSON strings
            # SQLite cannot store Python dicts/lists natively
            for col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].apply(
                        lambda x: json.dumps(x, default=str)
                        if isinstance(x, (dict, list))
                        else x
                    )

            # If table already exists (multiple files per folder),

            # If table already exists (multiple files per folder),
            # append data
            if table_name in table_info:
                df.to_sql(
                    table_name, conn, if_exists='append', index=False
                )
                table_info[table_name] += len(df)
            else:
                df.to_sql(
                    table_name, conn, if_exists='replace', index=False
                )
                table_info[table_name] = len(df)

            print(
                f"  ✓ {table_name}: {len(df)} rows, "
                f"cols={list(df.columns)[:6]}..."
            )

        conn.commit()

        print(f"\n{'=' * 60}")
        print(f"DATABASE READY!")
        print(f"Tables loaded: {len(table_info)}")
        print(f"{'=' * 60}")
        for name, count in sorted(table_info.items()):
            print(f"  {name}: {count} rows")
        print(f"{'=' * 60}")

        # Save mapping
        with open("table_mapping.json", "w") as f:
            json.dump(table_info, f, indent=2)

        return True

    except Exception as e:
        print(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()


def get_schema_description():
    """Get a COMPACT schema description for LLM prompts."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
    )
    tables = [row['name'] for row in cursor.fetchall()]

    schema_parts = []
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        col_names = [col['name'] for col in columns]

        cursor.execute(f"SELECT COUNT(*) as cnt FROM {table};")
        count = cursor.fetchone()['cnt']

        # Just column names, no sample data (saves tokens)
        schema_parts.append(
            f"{table} ({count} rows): {', '.join(col_names)}"
        )

    conn.close()
    return "\n".join(schema_parts)


def execute_query(sql: str):
    """Execute a SELECT query safely."""
    conn = get_connection()
    try:
        sql_stripped = sql.strip().upper()
        if not sql_stripped.startswith("SELECT"):
            return {"error": "Only SELECT queries allowed.", "results": []}

        for kw in ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "--"]:
            if kw in sql_stripped:
                return {"error": f"Forbidden: {kw}", "results": []}

        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        return {"results": results, "count": len(results)}
    except Exception as e:
        return {"error": str(e), "results": []}
    finally:
        conn.close()


def get_all_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
    )
    tables = [row['name'] for row in cursor.fetchall()]
    conn.close()
    return tables


def get_table_data(table_name: str, limit: int = 100):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT ?;", (limit,))
        rows = [dict(row) for row in cursor.fetchall()]
        return rows
    except Exception:
        return []
    finally:
        conn.close()