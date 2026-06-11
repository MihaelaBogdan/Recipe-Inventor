"""
langchain_demo.py - Utilizarea LangChain pentru RAG pe retete
===========================================================
Acest script demonstreaza utilizarea componentelor din specificatia tehnica
pentru a realiza indexarea vectoriala Chroma, cautarea hibrida (BM25 + Dense)
si interogarea semantica pe setul de date local de retete.
"""

import os
import sys

# Adaugam directorul parinte in path pentru importuri
sys.path.insert(0, os.path.dirname(__file__))

from recipes_data import BASE_RECIPES, generate_variations
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

def main():
    print("1. Se incarca retetele de baza...")
    # Extindem retetele folosind generatorul intern de variatii din aplicatie
    recipes = BASE_RECIPES + generate_variations()
    print(f"   Am incarcat {len(recipes)} retete pentru indexare.")

    print("\n2. Conversia retetelor in documente LangChain...")
    docs = []
    for r in recipes:
        # Formam textul de baza pentru embeddings si retrieval
        content = f"Titlu: {r['title']}. Categorie/Bucatarie: {r['cuisine']}. Ingrediente: {', '.join(r['ingredients'])}. Preparare: {', '.join(r['steps'])}"
        
        # Salvam metadatele pentru filtrare ulterioara
        metadata = {
            "id": r["id"],
            "title": r["title"],
            "cuisine": r["cuisine"],
            "difficulty": r["difficulty"],
            "time_minutes": r["time_minutes"]
        }
        docs.append(Document(page_content=content, metadata=metadata))
    print(f"   Am creat {len(docs)} documente de tip LangChain Document.")

    print("\n3. Initializarea modelului on-premise de Embeddings (HuggingFace)...")
    # Foloseste modelul local utilizat in restul aplicatiei (all-MiniLM-L6-v2)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    print("   Modelul local de embeddings a fost incarcat cu succes.")

    print("\n4. Indexarea documentelor culinare in baza de date vectoriala Chroma (In-Memory)...")
    # Cream magazinul vectorial in-memory pentru demo
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings
    )
    print("   Documentele au fost indexate vectorial in Chroma.")

    print("\n5. Configurarea cautarii hibride (EnsembleRetriever)...")
    # Configurare retriever rar (BM25 - cautare dupa cuvinte cheie)
    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = 3

    # Configurare retriever dens (Chroma - cautare dupa inteles/semantici)
    dense_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # Combinam cele doua metode: 70% pondere vectoriala (semantica), 30% cuvinte cheie
    hybrid_retriever = EnsembleRetriever(
        retrievers=[dense_retriever, bm25_retriever],
        weights=[0.7, 0.3]
    )
    print("   Retriever-ul Hibrid (Dense + Sparse) a fost configurat.")

    # Ruleaza o cautare de test cu ingrediente relevante
    query = "pui si usturoi"
    print(f"\n6. Executam o cautare hibrida pentru interogarea: '{query}'...")
    results = hybrid_retriever.invoke(query)

    print("\n================ REZULTATE RETRIEVED (Top 3) ================")
    for idx, doc in enumerate(results[:3]):
        meta = doc.metadata
        print(f"\n[{idx + 1}] Reteta: {meta['title']} ({meta['cuisine']})")
        print(f"    Dificultate: {meta['difficulty']} | Timp de gatire: {meta['time_minutes']} min")
        print(f"    Ingrediente snippet: {doc.page_content[:150]}...")
    print("=============================================================")

if __name__ == "__main__":
    main()
