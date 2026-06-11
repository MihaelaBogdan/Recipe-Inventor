# Specificatie Tehnica: Migrarea Arhitecturii RAG la LangChain

Acest document descrie specificatiile tehnice pentru inlocuirea pipeline-ului manual de cautare si generare din aplicatia Recipe Inventor cu o arhitectura bazata pe framework-ul LangChain.

---

## 1. Componentele Arhitecturii Curente vs. Echivalentul LangChain

In arhitectura manuala (FastAPI + ChromaDB SDK + SentenceTransformers), codul gestioneaza direct operatiile matematice si asocierile de context. Folosind LangChain, aceste componente sunt abstractizate in module reutilizabile:

| Componenta Curenta | Modul Echivalent LangChain | Rol |
| :--- | :--- | :--- |
| `SentenceTransformer('all-MiniLM-L6-v2')` | `HuggingFaceEmbeddings` | Genereaza embedding-uri vectoriale pe baza textului |
| `chromadb.PersistentClient` | `Chroma` (VectorStore LangChain) | Salveaza, indexeaza si interogheaza vectorii pe disc |
| `BM25` (manual) | `BM25Retriever` | Efectueaza cautari rapide dupa cuvinte cheie |
| Cautare Hibrida (Alpha manual) | `EnsembleRetriever` | Combina rezultatele BM25 si Dense (RRF sau pondere) |
| Prompt & LLM manual | `create_stuff_documents_chain` | Insereaza documentele gasite in contextul prompt-ului LLM |
| `ChatbotHistory` (manual) | `RunnableWithMessageHistory` | Mentine starea conversatiei si istoricul mesajelor |

---

## 2. Specificatii de Implementare a Codului in Python

Mai jos sunt detaliate etapele de configurare a unui modul de cautare si generare prin LangChain, compatibil cu baza noastra de date culinara.

### A. Incarcarea Datelor si Indexarea Vectoriala (Ingestie)
Retetele incarcate din scriptul `data_loader.py` sunt convertite in obiecte de tip `Document` din LangChain, pastrand metadatele necesare pentru filtrare (cuisine, difficulty, time_minutes).

```python
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# 1. Pregatirea documentelor LangChain
docs = []
for recipe in recipes:
    content = f"Titlu: {recipe['title']}. Ingrediente: {', '.join(recipe['ingredients'])}. Instructiuni: {', '.join(recipe['steps'])}"
    metadata = {
        "id": recipe["id"],
        "title": recipe["title"],
        "cuisine": recipe.get("cuisine", ""),
        "difficulty": recipe.get("difficulty", ""),
        "time_minutes": recipe.get("time_minutes", 0)
    }
    docs.append(Document(page_content=content, metadata=metadata))

# 2. Configurare Model de Embeddings
embeddings_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 3. Initializare si Populare Vector Store Chroma
vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=embeddings_model,
    persist_directory="data/chroma_db_langchain"
)
```

### B. Cautarea Hibrida cu Filtrare (Retrieval)
Pentru a replica functionalitatea de cautare hibrida din `rag_engine.py` (Dense + Sparse), utilizam `EnsembleRetriever`. Acesta combina un `BM25Retriever` local cu retrieverul oferit de `Chroma`.

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

# 1. Configurare Retriever Sparse (BM25)
bm25_retriever = BM25Retriever.from_documents(docs)
bm25_retriever.k = 3

# 2. Configurare Retriever Dense (Chroma) cu suport pentru metadate
dense_retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={
        "k": 3,
        "filter": {"cuisine": "Italian"} # Exemplu de filtru aplicat pe metadate
    }
)

# 3. Creare Ensemble Retriever (Ponderat: 70% dense, 30% sparse)
hybrid_retriever = EnsembleRetriever(
    retrievers=[dense_retriever, bm25_retriever],
    weights=[0.7, 0.3]
)
```

### C. Generarea Retetelor (Synthesis Chain)
Odata ce documentele relevante au fost gasite, ele sunt combinate intr-un prompt destinat modelului lingvistic (LLM).

```python
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI # Sau alt provider de LLM (Ollama, Anthropic)

# 1. Initializare Model de Limbaj (pe baza de API on-premise sau cloud)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

# 2. Definirea Prompt-ului de Sistem
system_prompt = (
    "Esti un bucatar sef experimentat. Foloseste urmatoarele retete recuperate "
    "ca si context pentru a raspunde sau a inventa o reteta noua bazata pe dorintele utilizatorului.\n\n"
    "CONTEXT:\n{context}\n\n"
    "INTREBARE UTILIZATOR: {input}"
)
prompt_template = ChatPromptTemplate.from_template(system_prompt)

# 3. Construirea Lantului de RAG
combine_docs_chain = create_stuff_documents_chain(llm, prompt_template)
rag_chain = create_retrieval_chain(hybrid_retriever, combine_docs_chain)

# 4. Executare Lant
response = rag_chain.invoke({"input": "vreau o reteta cu pui si ciuperci"})
print(response["answer"])
```

---

## 3. Avantaje Practice ale tranzitiei la LangChain

1. **Modularitate**: Daca dorim sa schimbam baza de date ChromaDB cu Qdrant sau Milvus, codul de retrieval ramane identic, inlocuindu-se doar clasa de instantiere a Vector Store-ului.
2. **Filtrare Avansata pe Metadate**: Filtrarea complexa dupa timp de gatire, cuisine sau dificultate este gestionata automat de LangChain, eliminand codul manual de curatare a array-urilor.
3. **Chains de Memorie incorporate**: Adaugarea memoriei intr-un chatbot conversational RAG se face simplu prin legarea unui `RunnableWithMessageHistory`, fara a mai gestiona manual append-urile in array-ul de istoric.
