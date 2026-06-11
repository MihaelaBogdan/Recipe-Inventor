"""
langchain_demo.py - Using LangChain for RAG on Recipes
===========================================================
This script demonstrates the use of components from the technical specification
to perform Chroma vector indexing, hybrid search (BM25 + Dense),
and semantic querying on the local recipe dataset.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from recipes_data import BASE_RECIPES, generate_variations
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

def main():
    print("1. Loading base recipes...")
    # Extend recipes using the internal variation generator from the application
    recipes = BASE_RECIPES + generate_variations()
    print(f"   Loaded {len(recipes)} recipes for indexing.")

    print("\n2. Converting recipes into LangChain documents...")
    docs = []
    for r in recipes:
        # Form the base text for embeddings and retrieval
        content = f"Title: {r['title']}. Category/Cuisine: {r['cuisine']}. Ingredients: {', '.join(r['ingredients'])}. Preparation: {', '.join(r['steps'])}"
        
        # Save metadata for later filtering
        metadata = {
            "id": r["id"],
            "title": r["title"],
            "cuisine": r["cuisine"],
            "difficulty": r["difficulty"],
            "time_minutes": r["time_minutes"]
        }
        docs.append(Document(page_content=content, metadata=metadata))
    print(f"   Created {len(docs)} LangChain Document objects.")

    print("\n3. Initializing the on-premise Embeddings model (HuggingFace)...")
    # Uses the local model used in the rest of the application (all-MiniLM-L6-v2)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    print("   Local embeddings model loaded successfully.")

    print("\n4. Indexing culinary documents in the Chroma vector database (In-Memory)...")
    # Create the in-memory vector store for demo
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings
    )
    print("   Documents have been vector-indexed in Chroma.")

    print("\n5. Configuring hybrid search (EnsembleRetriever)...")
    # Configure sparse retriever (BM25 - keyword search)
    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = 3

    # Configure dense retriever (Chroma - semantic/meaning search)
    dense_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # Combine both methods: 70% vector (semantic) weight, 30% keyword weight
    hybrid_retriever = EnsembleRetriever(
        retrievers=[dense_retriever, bm25_retriever],
        weights=[0.7, 0.3]
    )
    print("   Hybrid Retriever (Dense + Sparse) has been configured.")

    # Run a test search with relevant ingredients
    query = "chicken and garlic"
    print(f"\n6. Executing a hybrid search for query: '{query}'...")
    results = hybrid_retriever.invoke(query)

    print("\n================ RETRIEVED RESULTS (Top 3) ================")
    for idx, doc in enumerate(results[:3]):
        meta = doc.metadata
        print(f"\n[{idx + 1}] Recipe: {meta['title']} ({meta['cuisine']})")
        print(f"    Difficulty: {meta['difficulty']} | Cooking time: {meta['time_minutes']} min")
        print(f"    Ingredients snippet: {doc.page_content[:150]}...")
    print("=============================================================")

if __name__ == "__main__":
    main()
