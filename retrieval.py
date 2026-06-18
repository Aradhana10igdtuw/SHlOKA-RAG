import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from ingest import get_embeddings

# Load configurations
load_dotenv()

CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "chroma_db")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def load_vectorstore():
    """
    Loads the persistent Chroma vector store.
    """
    if not os.path.exists(CHROMA_DB_DIR):
        raise FileNotFoundError(f"Chroma vector store not found at '{CHROMA_DB_DIR}'. Please run ingest first.")
    
    embeddings = get_embeddings()
    return Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embeddings
    )

def retrieve_context(shloka: str, top_k: int = 5):
    """
    Embeds the shloka query and returns top matching passages from ChromaDB.
    Returns a list of dicts with page_content and metadata.
    """
    try:
        db = load_vectorstore()
    except FileNotFoundError as e:
        print(f"Error loading database: {e}")
        return []
    
    results = db.similarity_search(shloka, k=top_k)
    return [
        {
            "page_content": doc.page_content,
            "metadata": doc.metadata
        }
        for doc in results
    ]

def search_documents(query: str, k: int = 4):
    """
    Searches Chroma database for relevant document chunks.
    Returns list of dicts with content, metadata, and score.
    """
    try:
        db = load_vectorstore()
    except FileNotFoundError as e:
        return {"error": str(e), "results": []}

    # similarity_search_with_relevance_scores returns (doc, score)
    # Note: distance/relevance calculation depends on the distance metric used by Chroma (default: l2/cosine)
    results = db.similarity_search_with_score(query, k=k)
    
    formatted_results = []
    for doc, score in results:
        formatted_results.append({
            "content": doc.page_content,
            "metadata": doc.metadata,
            "score": float(score)  # Lower is typically closer/better for L2 distance
        })
    
    return {"results": formatted_results}

def generate_rag_answer(query: str, k: int = 4):
    """
    Performs retrieval and sends context + query to OpenAI for a generated response.
    Falls back to simple search if OpenAI API key is not configured.
    """
    search_res = search_documents(query, k=k)
    if "error" in search_res:
        return {"answer": f"Error loading database: {search_res['error']}", "sources": []}
    
    results = search_res["results"]
    if not results:
        return {"answer": "No relevant documents found. Please ingest documents first.", "sources": []}

    sources = list(set([res["metadata"].get("source", "Unknown") for res in results]))
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key or "your_openai_api_key_here" in openai_key:
        # No API Key, return raw results only
        summary = "No OpenAI API key found in .env. Showing top matching text chunks below:\n\n"
        for i, res in enumerate(results):
            summary += f"--- Chunk {i+1} (Source: {res['metadata'].get('source')}, Score: {res['score']:.4f}) ---\n"
            summary += f"{res['content']}\n\n"
        return {"answer": summary, "sources": sources, "raw_results": results}

    # API key is configured, use OpenAI to generate answer
    from openai import OpenAI
    client = OpenAI(api_key=openai_key)
    
    # Format context
    context_str = "\n\n".join([f"Source: {res['metadata'].get('source')}\nContent: {res['content']}" for res in results])
    
    system_prompt = (
        "You are an expert assistant specialized in Ayurvedic texts and Shlokas. "
        "Use the provided context to answer the query as accurately and fully as possible. "
        "If the answer cannot be found in the context, state that you do not know based on the provided documents. "
        "Cite the sources of your information."
    )
    
    user_prompt = f"Context:\n{context_str}\n\nQuery: {query}"
    
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        answer = response.choices[0].message.content
        return {
            "answer": answer,
            "sources": sources,
            "raw_results": results
        }
    except Exception as e:
        return {
            "answer": f"Failed to generate answer from OpenAI: {e}",
            "sources": sources,
            "raw_results": results
        }

if __name__ == "__main__":
    import sys
    test_query = sys.argv[1] if len(sys.argv) > 1 else "health"
    print(f"Testing retrieval for query: '{test_query}'...")
    res = generate_rag_answer(test_query)
    print("\nAnswer:")
    print(res["answer"])
    print("\nSources:", res["sources"])
