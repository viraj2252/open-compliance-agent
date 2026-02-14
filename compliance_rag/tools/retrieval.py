import duckdb
from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool
from compliance_rag.config import llm_config, VECTOR_STORE_PATH, METADATA_DB_PATH

# 1. Vector Search Tool
# Use the FAISS index we created for sematic search
vector_store = FAISS.load_local(
    VECTOR_STORE_PATH, 
    llm_config["embedding_model"],
    allow_dangerous_deserialization=True # Required for local loading
)

@tool
def policy_search_tool(query: str, k: int = 3):
    """
    Search for internal company policy content and clauses.
    Use this for questions about rules, standards, and requirements.
    """
    docs = vector_store.similarity_search(query, k=k)
    return "\n\n".join([f"Source: {d.metadata.get('source', 'Unknown')}\n{d.page_content}" for d in docs])

# 2. Metadata SQL Tool
# Query the DuckDB database for structured policy information
@tool
def policy_metadata_tool(sql_query: str):
    """
    Execute a SQL query against the policies metadata database.
    The table name is 'policies'. 
    Columns: policy_id, title, owner, version, last_updated, department, status, retention_years.
    Use this for questions about owners, dates, versions, and lists of policies.
    """
    try:
        con = duckdb.connect(METADATA_DB_PATH)
        result = con.execute(sql_query).df().to_string()
        con.close()
        return result
    except Exception as e:
        return f"Error executing SQL: {str(e)}"
