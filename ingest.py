import os
import glob
from dotenv import load_dotenv
from langchain_text_splitters import TokenTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

# Load configurations
load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", "data")
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "chroma_db")
EMBEDDING_MODE = os.getenv("EMBEDDING_MODE", "local").lower()
LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

def get_embeddings():
    """
    Returns the appropriate LangChain embedding object based on environment settings.
    """
    if EMBEDDING_MODE == "openai" and os.getenv("OPENAI_API_KEY"):
        print("Using OpenAIEmbeddings...")
        return OpenAIEmbeddings()
    else:
        print(f"Using local HuggingFaceEmbeddings with model '{LOCAL_EMBEDDING_MODEL}'...")
        return HuggingFaceEmbeddings(model_name=LOCAL_EMBEDDING_MODEL)

def ingest_documents():
    """
    Loads text files from the data directory, splits them into chunks, and saves to Chroma DB.
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Created data directory: {DATA_DIR}")

    # Gather files
    search_pattern = os.path.join(DATA_DIR, "*")
    files = glob.glob(search_pattern)
    files = [f for f in files if os.path.isfile(f) and not f.endswith(".gitkeep")]

    if not files:
        print(f"No documents found in '{DATA_DIR}' to ingest.")
        return 0

    documents = []
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Create LangChain document
            doc = Document(
                page_content=content,
                metadata={"source": os.path.basename(file_path)}
            )
            documents.append(doc)
            print(f"Loaded: {file_path}")
        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    if not documents:
        print("No valid documents loaded.")
        return 0

    # Split documents into overlapping chunks
    text_splitter = TokenTextSplitter(
        chunk_size=512,
        chunk_overlap=64
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    # Generate embeddings and store in Chroma
    embeddings = get_embeddings()
    print(f"Initializing Chroma DB at '{CHROMA_DB_DIR}'...")
    
    # Chroma persists auto-magically on init or insert in newer versions.
    db = Chroma.from_documents(
        chunks,
        embeddings,
        persist_directory=CHROMA_DB_DIR
    )
    
    if hasattr(db, "persist"):
        db.persist()

    print("Ingestion completed successfully!")
    return len(chunks)

if __name__ == "__main__":
    ingest_documents()
