import duckdb
import os
from datetime import datetime
from compliance_rag.config import METADATA_DB_PATH

def setup_metadata_db():
    """
    Sets up a DuckDB database to store structured metadata for compliance policies.
    This enables the SQL Analyst agent to perform structured queries.
    """
    print(f"--- Initializing Metadata Database at {METADATA_DB_PATH} ---")
    
    # Connect to DuckDB (creates the file if it doesn't exist)
    con = duckdb.connect(METADATA_DB_PATH)
    
    # 1. Create the policies table
    con.execute("""
        CREATE OR REPLACE TABLE policies (
            policy_id VARCHAR PRIMARY KEY,
            title VARCHAR,
            owner VARCHAR,
            version VARCHAR,
            last_updated DATE,
            department VARCHAR,
            status VARCHAR,
            retention_years INTEGER
        )
    """)
    
    # 2. Insert sample metadata
    # Dates are formatted as YYYY-MM-DD
    sample_data = [
        ('POL-001', 'AI Usage Policy', 'Sarah Chen', '1.2', '2024-01-15', 'Engineering', 'Active', 5),
        ('POL-002', 'Remote Work Policy', 'Marcus Thorne', '2.0', '2023-11-20', 'HR', 'Active', 3),
        ('POL-003', 'Data Classification Standard', 'Elena Rodriguez', '1.0', '2024-02-10', 'Security', 'Active', 7)
    ]
    
    for record in sample_data:
        con.execute("INSERT INTO policies VALUES (?, ?, ?, ?, ?, ?, ?, ?)", record)
    
    # 3. Verify
    result = con.execute("SELECT COUNT(*) FROM policies").fetchone()
    print(f"Successfully created 'policies' table with {result[0]} records.")
    
    con.close()

if __name__ == "__main__":
    setup_metadata_db()
