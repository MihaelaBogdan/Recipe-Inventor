# AI Recipe Inventor — RAG Engine

Motor RAG (Retrieval-Augmented Generation) care inventează rețete noi pe baza ingredientelor disponibile. **Fără LLM** — folosește TF-IDF + cosine similarity.

## Structură

```
Proiect_RAG/
├── backend/
│   ├── main.py            # FastAPI app + servire frontend
│   ├── rag_engine.py      # TF-IDF RAG cu cosine similarity
│   ├── recipe_generator.py# Inventare rețete (template-based)
│   ├── data_loader.py     # Încărcarea și normalizarea datelor
│   ├── recipes_data.py    # 60 rețete de bază → 300+ cu variații
│   └── requirements.txt
├── frontend/
│   ├── index.html         # UI glassmorphism dark
│   ├── style.css          # CSS premium animat
│   └── app.js             # Logica interactivă
└── README.md
```

## Cum funcționează RAG-ul

1. **Indexare** — La pornire, cele 300+ rețete sunt vectorizate cu **TF-IDF bigramic** (scikit-learn)
2. **Retrieval** — Ingredientele utilizatorului sunt transformate în același spațiu vectorial; se calculează **cosine similarity** + bonus pentru match exact
3. **Generation** — Rețetele cele mai similare devin "template-uri"; ingredientele utilizatorului sunt combinate cu cele complementare din template, titluri și explicații sunt generate din reguli

## Instalare și rulare

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Deschide `http://localhost:8000` în browser.

## Funcționalități

- 🔍 **RAG TF-IDF** — bigramic, sublinear TF, cosine similarity
- 🎯 **Bonus scoring** — match exact/parțial de ingrediente
- 🍳 **300+ rețete** — 60 baze × 4 variații (spicy, quick, vegan, light)
- 🌍 **8 bucătării** — Italian, Thai, Indian, Chinese, Japanese, Korean, Mediterranean, Mexican, American, French, Middle Eastern
- 🎨 **UI glassmorphism** — dark mode, animații, responsive
- 🏷️ **Tag input** — Enter/virgulă pentru adăugare, ✕ pentru eliminare
- 🔬 **Explicații** — de ce funcționează combinațiile de ingrediente
- 💡 **Sfaturi pro** — specifice fiecărei bucătării

## RAG Research & Comparison Objectives

Pentru proiectele curente, ne axăm pe comparația practică și analiza metodelor RAG local/on-prem:
- **Comparația dintre diferite metode de retrieval**: Evaluarea Sparse Retrieval (BM25) vs. Dense Semantic Retrieval (ChromaDB).
- **Reranking**: Utilizarea Maximal Marginal Relevance (MMR) pentru diversitatea recomandărilor.
- **Setarea unui threshold dinamic pentru relevanță**: Implementarea unui prag de relevanță hibrid folosit de agentul determinist pentru query expansion / ingredient dropping.
- **Testarea acurateții retrieval-ului**: Analiza automată a recall-ului ingredientelor față de rețetele returnate.
- **Baze de date vectoriale on-prem**: Integrarea și testarea ChromaDB rulat local fără dependențe cloud externe.
- **Comparația între modele de embeddings**: Evaluarea performanței modelului `all-MiniLM-L6-v2` față de indexarea TF-IDF tradițională.

Scopul este de a rămâne într-o zonă practică și relevantă, fără a depinde prea mult de contextul și complexitatea unui proiect comercial în această etapă.
