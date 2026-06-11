# AI Recipe Inventor PRO — Advanced RAG Engine & Playground

O platformă interactivă și vizuală pentru testarea, compararea și implementarea tehnologiilor **RAG (Retrieval-Augmented Generation) on-premises/local-first**. Aplicația include un generator inteligent de rețete ghidat de un agent autonom și o suită completă de benchmark-uri.

---

## 📂 Structură Proiect

```
Proiect_RAG/
├── backend/
│   ├── main.py               # API FastAPI cu endpoint-uri de Benchmark, DB Query și Chat
│   ├── rag_engine.py         # Motor Hibrid (ChromaDB + BM25) cu MMR Reranking & Thresholding
│   ├── deterministic_agent.py# Agent autonom cu buclă de auto-corecție & query expansion
│   ├── recipe_generator.py   # Generator de rețete pe baza contextului extras (rule-based)
│   ├── data_loader.py        # Încărcare, curățare și normalizare rețete
│   ├── recipes_data.py       # Date predefinite pentru rețete cu variații locale
│   └── requirements.txt      # Dependențe Python (ChromaDB, SentenceTransformers, FastAPI, etc.)
├── frontend/
│   ├── index.html            # UI-ul principal premium în stil Glassmorphism Dark
│   ├── style.css             # Design vizual premium, culori HSL, carduri de sticlă și animații
│   ├── app.js                # Controleri JS, bindings pentru benchmark-uri, simulator DB și API-uri
│   └── chatbot.html          # Interfață separată pentru modul chatbot dedicat
└── README.md                 # Specificații tehnice și documentație
```

---

## 🧬 Specificații Tehnice & Arhitectură RAG

### 1. Vectorizare & Embeddings (Local)
- Modelul utilizat: `all-MiniLM-L6-v2` (Rulează complet local prin biblioteca `sentence-transformers`).
- Dimensiunea vectorilor: **384 dimensiuni**.
- Performanță: Latență de codificare extrem de redusă (~3-10 ms pe CPU standard).

### 2. Retrieval Hibrid (Sparse + Dense)
Formula de scor îmbină metodele lexicale cu cele semantice:
$$\text{Scor Hibrid} = \alpha \times \text{Scor Dense} + (1 - \alpha) \times \text{Scor Sparse}$$
- **Sparse Retrieval**: Algoritmul **BM25** optimizat pentru detectarea cuvintelor cheie (ingrediente specifice).
- **Dense Retrieval**: Distanța Cosinus calculată peste colecția vectorială indexată în **ChromaDB**.
- **Alpha ($\alpha$)**: Parametru ajustabil live între `0.0` (doar BM25) și `1.0` (doar căutare semantică).

### 3. Diversificare prin MMR (Maximal Marginal Relevance)
Pentru a evita rețetele similare redundant, algoritmul re-ordonează rezultatele prioritizând diversitatea:
$$\text{Scor MMR} = \lambda \times \text{Relevanță}(d) - (1 - \lambda) \times \max_{s \in S} \text{Similitudine}(d, s)$$
- **$\lambda$ (Lambda)**: Controlează echilibrul (valori mici aduc o diversitate maximă a ingredientelor în listă).

### 4. Agent Autonom cu Auto-Corecție și Query Expansion
Când utilizatorul cere o rețetă, **Agentul Determinist** execută următorii pași:
1. **Analiză & Extindere**: Extinde ingredientele prin grupuri de sinonime și normalizări lexicale.
2. **Evaluare Prag**: Rulează căutarea hibridă. Dacă cel mai mare scor de relevanță este sub **Pragul Dinamic (Threshold)** setat de utilizator, pornește bucla de corecție.
3. **Ingredient Dropping**: Elimină pe rând ingredientele restrictive (de tip condimente/rare) și re-interoghează baza de date până când găsește rețete care depășesc pragul de încredere sau se atinge numărul maxim de iterații.

---

## 🔬 RAG Playground & Benchmarking Arena (Modul Interactiv)

Aplicația oferă o interfață dedicată testelor de performanță:
- **🔍 Simulator Retrieval Parametrizat**: Permite rularea de căutări ajustând din mers parametrii `Alpha`, `Threshold` și `MMR Lambda` și afișează scorurile individuale pentru fiecare metodă.
- **📊 Test Bench de Acuratețe**: Evaluează automat 5 interogări etalon și calculează metrici standard de RAG:
  - **Precision@3 & Precision@5** (Procentul de rezultate corecte returnate).
  - **Recall@5** (Procentul de rețete relevante găsite din setul total).
  - **MRR (Mean Reciprocal Rank)** (Cât de sus în listă este prima rețetă relevantă).
  - **Latența medie** de execuție în ms.
- **🧬 Model Embedding Benchmarker**: Rulează o codificare în timp real folosind CPU-ul local pentru a stabili latența reală a hardware-ului și o compară cu specificațiile estimate ale modelelor `multilingual-e5-small`, `bge-small-en-v1.5` și `multilingual-e5-base`.
- **🔒 Simulator Vector DB**: Permite interogarea simbolică a magazinelor vectoriale (**ChromaDB**, **Qdrant**, **pgvector**, **Milvus**) generând automat codul Python SDK / interogările SQL native specifice fiecărei tehnologii, alături de rezultatul brut (Raw JSON) din DB.

---

## ⚡ Instalare și Rulare Rapidă

### Cerințe
- Python 3.9+
- Pip (manager de pachete)

### Procedură
1. Clonează repository-ul.
2. Creează și activează un mediu virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Pe macOS/Linux
   # sau
   venv\Scripts\activate     # Pe Windows
   ```
3. Instalează pachetele necesare:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. Rulează serverul FastAPI:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```
5. Accesează în browser adresa: `http://127.0.0.1:8000/`.

---

## 🛠️ Stack Tehnologic
- **Backend**: FastAPI (Python), SentenceTransformers, ChromaDB, BM25, NumPy.
- **Frontend**: HTML5 Semantic, JavaScript (ES6+ Vanilla Client), CSS Custom (Glassmorphism & Flexbox/Grid).
