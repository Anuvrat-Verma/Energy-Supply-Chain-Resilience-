import os
import json
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

# ---------------------------------------------------------------------
# DYNAMIC PATH RESOLUTION
# ---------------------------------------------------------------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOC_DIR = os.path.join(ROOT_DIR, "docs")
DB_DIR = os.path.join(ROOT_DIR, "chroma_db")

# Define target collections mapped directly to subdirectories
COLLECTIONS = {
    "macro_economics_live": os.path.join(DOC_DIR, "macro_economics_live"),
    "macro_economics_sandbox": os.path.join(DOC_DIR, "macro_economics_sandbox"),
    "maritime_logistics": os.path.join(DOC_DIR, "maritime_logistics")
}

# Initialize the local embedding model
embeddings = OllamaEmbeddings(model="nomic-embed-text")

def ingest_documents():
    """Scans isolated domain subfolders under /docs and indexes them into separate collections."""
    # 🎯 OPTIMIZED CHUNKING: Prevents cutting critical financial figures and tables in half
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)

    for collection_name, folder_path in COLLECTIONS.items():
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"📁 Created folder: '{folder_path}'. Place your [{collection_name}] .txt files here!")
            continue

        print(f"\n🔄 Scanning data store for collection: [{collection_name}]")
        docs = []
        
        for file in os.listdir(folder_path):
            if file.endswith(".txt"):
                file_path = os.path.join(folder_path, file)
                print(f"📄 Loading: {file} into collection '{collection_name}'")
                try:
                    loader = TextLoader(file_path, encoding="utf-8")
                    docs.extend(loader.load())
                except Exception as e:
                    print(f"❌ Error loading file {file}: {e}")

        if not docs:
            print(f"⚠️ No new documents found to ingest in {folder_path}")
            continue

        splits = text_splitter.split_documents(docs)
        print(f"📦 Generated {len(splits)} chunks for '{collection_name}'. Prepare index...")
        
        # 🛡️ ANTI-DUPLICATION GUARD: Clear existing collection data before rebuilding it
        try:
            existing_db = Chroma(
                persist_directory=DB_DIR, 
                embedding_function=embeddings, 
                collection_name=collection_name
            )
            # This wipes out the stale version of this specific collection
            existing_db.delete_collection()
            print(f"🗑️ Stale vector cache for '{collection_name}' wiped cleanly.")
        except Exception:
            # Catches conditions where the collection doesn't exist yet on first boot
            pass

        # Write fresh, clean embeddings without stacking duplicates
        Chroma.from_documents(
            documents=splits, 
            embedding=embeddings, 
            persist_directory=DB_DIR,
            collection_name=collection_name
        )
        print(f"✅ Collection '{collection_name}' successfully synchronized inside '{DB_DIR}'!")

def retrieve_context(query: str, collection_name: str = "macro_economics", mode: str = "live") -> str:
    """
    Searches a specific vector collection with dynamic environment routing.
    Maintains 'collection_name' keyword to prevent breaking existing agent calls.
    """
    if not os.path.exists(DB_DIR):
        print(f"⚠️ No database directory found at '{DB_DIR}'. Run ingest_documents() first.")
        return ""

    # 🎯 FIX: Safely route the collection target while keeping the original parameter name
    if collection_name == "macro_economics":
        active_collection = f"{collection_name}_{mode}"
    else:
        active_collection = collection_name  # maritime_logistics stays identical

    print(f"🔀 Environment Router: Directing semantic query to [{active_collection}]")

    db = Chroma(
        persist_directory=DB_DIR, 
        embedding_function=embeddings,
        collection_name=active_collection
    )

    docs = db.similarity_search(query, k=3)
    context = "\n".join([doc.page_content for doc in docs])
    return context
# Make sure this is at the very bottom of rag.py
if __name__ == "__main__":
    ingest_documents()