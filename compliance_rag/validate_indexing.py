from compliance_rag.tools.retrieval import policy_search_tool

def validate_vector_store():
    print("--- Validating Vector Store Indexing ---")
    
    test_queries = [
        "What are the rules for AI usage?",
        "Tell me about the remote work policy.",
        "How is data classified?"
    ]
    
    for query in test_queries:
        print(f"\nTesting Query: '{query}'")
        try:
            # We use the policy_search_tool which loads the existing FAISS index
            results = policy_search_tool.invoke({"query": query, "k": 1})
            if results:
                print(f"Result Found:\n{results[:200]}...") # Print first 200 chars
            else:
                print("No results found for this query.")
        except Exception as e:
            print(f"Error during validation: {str(e)}")

if __name__ == "__main__":
    validate_vector_store()
