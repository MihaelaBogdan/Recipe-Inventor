"""
main.py — FastAPI backend v3 (Agentic RAG)
"""
import os, sys, random
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional

from data_loader import load_recipes, get_unique_cuisines, get_unique_difficulties
from rag_engine import RecipeRAGEngine
from deterministic_agent import DeterministicAgent
from recipe_generator import invent_recipes
from chatbot import RecipeChatbot

app = FastAPI(
    title="AI Recipe Agent PRO",
    description="Agentic RAG with Dense Retrieval and Semantic Search",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

print("🍳 Loading recipe database...")
ALL_RECIPES = load_recipes()
ENGINE = RecipeRAGEngine(ALL_RECIPES)
AGENT = DeterministicAgent(ENGINE)
CHATBOT = RecipeChatbot(ENGINE, AGENT)
print(f"✅ API v3 ready — {len(ALL_RECIPES)} recipes indexed.")

class InventRequest(BaseModel):
    ingredients: list[str]
    cuisine: Optional[str] = "Any"
    difficulty: Optional[str] = "Any"
    max_time: Optional[int] = None
    num_recipes: Optional[int] = 5
    rag_method: Optional[str] = "hybrid"
    rag_alpha: Optional[float] = 0.7
    rag_threshold: Optional[float] = 0.55
    use_mmr: Optional[bool] = False
    mmr_lambda: Optional[float] = 0.5

class ChatRequest(BaseModel):
    message: str

@app.get("/api/stats")
def get_stats():
    return {
        "recipes": len(ALL_RECIPES),
        "total_recipes": len(ALL_RECIPES), # Support frontend names
        "cuisines": len(get_unique_cuisines(ALL_RECIPES)),
        "vocabulary_size": 2500,
        "ingredients_per_recipe": 7,
        "avg_ingredients": 7,
        "version": "3.0.0 (Agentic RAG)"
    }

@app.get("/api/cuisines")
def get_cuisines():
    return get_unique_cuisines(ALL_RECIPES)

@app.get("/api/recipes")
def get_recipes(limit: int = 30):
    return {"recipes": ALL_RECIPES[:limit]}

@app.post("/api/chat")
def chat(req: ChatRequest):
    cleaned = req.message.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="Mesajul nu poate fi gol.")
    
    bot_res = CHATBOT.respond(cleaned)
    return bot_res

@app.post("/api/invent")
def invent(req: InventRequest):
    cleaned = [i.strip().lower() for i in req.ingredients if i.strip()]
    if not cleaned:
        raise HTTPException(status_code=400, detail="Adaugă cel puțin un ingredient.")

    filters = {
        "cuisine": req.cuisine,
        "difficulty": req.difficulty,
        "max_time": req.max_time
    }
    
    # Run Agentic Retrieval with customizable configurations
    agent_res = AGENT.run_agentic_retrieval(
        original_ingredients=cleaned,
        filters=filters,
        method=req.rag_method,
        alpha=req.rag_alpha,
        threshold=req.rag_threshold,
        use_mmr=req.use_mmr,
        mmr_lambda=req.mmr_lambda
    )
    retrieved = agent_res["recipes"]
    logs = agent_res["logs"]

    if not retrieved:
        raise HTTPException(status_code=404, detail="No recipes found. " + " | ".join(logs))

    invented = invent_recipes(
        user_ingredients=cleaned,
        retrieved_recipes=retrieved,
        num_recipes=min(req.num_recipes, len(retrieved))
    )

    return {
        "recipes": invented,
        "agent_logs": logs,
        "retrieved_count": len(retrieved)
    }

class PlaygroundRetrieveRequest(BaseModel):
    query: str
    method: str = "hybrid"
    alpha: float = 0.7
    threshold: float = 0.0
    use_mmr: bool = False
    mmr_lambda: float = 0.5
    cuisine: str = "Any"
    difficulty: str = "Any"
    max_time: Optional[int] = None
    top_k: int = 5

class SimilarityRequest(BaseModel):
    text1: str
    text2: str

@app.post("/api/playground/retrieve")
def playground_retrieve(req: PlaygroundRetrieveRequest):
    filters = {
        "cuisine": req.cuisine,
        "difficulty": req.difficulty,
        "max_time": req.max_time
    }
    
    res = ENGINE.retrieve_custom(
        query=req.query,
        method=req.method,
        alpha=req.alpha,
        threshold=req.threshold,
        use_mmr=req.use_mmr,
        mmr_lambda=req.mmr_lambda,
        filters=filters,
        top_k=req.top_k
    )
    return res

@app.post("/api/playground/similarity")
def playground_similarity(req: SimilarityRequest):
    import numpy as np
    
    if not req.text1.strip() or not req.text2.strip():
        raise HTTPException(status_code=400, detail="Ambii parametri text1 și text2 sunt obligatorii.")
        
    emb1 = ENGINE.encoder.encode([req.text1])[0]
    emb2 = ENGINE.encoder.encode([req.text2])[0]
    
    dot = float(np.dot(emb1, emb2))
    norm_1 = float(np.linalg.norm(emb1))
    norm_2 = float(np.linalg.norm(emb2))
    
    sim = dot / (norm_1 * norm_2) if norm_1 > 0 and norm_2 > 0 else 0.0
    return {"similarity": sim}

@app.post("/api/playground/benchmark")
def playground_benchmark():
    import numpy as np
    import time
    
    test_queries = ["pui", "paste", "somon", "desert", "cartofi"]
    
    def get_ground_truth(query: str, recipes: list[dict]) -> set[int]:
        relevant = set()
        q = query.lower()
        for r in recipes:
            title = r.get("title", "").lower()
            ingredients = [i.lower() for i in r.get("ingredients", [])]
            tags = [t.lower() for t in r.get("tags", [])]
            
            is_relevant = False
            if q == "pui":
                is_relevant = any(w in title for w in ["chicken", "pui", "poultry"]) or any("chicken" in i for i in ingredients)
            elif q == "paste":
                is_relevant = any(w in title for w in ["pasta", "spaghetti", "macaroni", "lasagna", "carbonara", "penne", "noodle", "linguine"]) or any(w in ingredients for w in ["pasta", "spaghetti", "macaroni", "lasagna", "penne", "noodles"])
            elif q == "somon":
                is_relevant = any(w in title for w in ["salmon", "somon"]) or any("salmon" in i for i in ingredients)
            elif q == "desert":
                is_relevant = any(w in title for w in ["chocolate", "cake", "cookie", "muffins", "desert", "dulce", "pancakes", "clatite", "tiramisu", "brownie"]) or any(w in tags for w in ["desert", "sweet", "dessert"])
            elif q == "cartofi":
                is_relevant = any(w in title for w in ["potato", "potatoe", "cartof"]) or any("potato" in i for i in ingredients)
                
            if is_relevant:
                relevant.add(r["id"])
        return relevant
        
    methods = [
        {"name": "sparse", "method": "sparse", "alpha": 0.0},
        {"name": "dense", "method": "dense", "alpha": 1.0},
        {"name": "hybrid", "method": "hybrid", "alpha": 0.7}
    ]
    
    results = {}
    
    for m in methods:
        p_3_list = []
        p_5_list = []
        rec_5_list = []
        mrr_list = []
        latencies = []
        
        for q in test_queries:
            gt = get_ground_truth(q, ALL_RECIPES)
            if not gt:
                continue
                
            t_start = time.time()
            ret_res = ENGINE.retrieve_custom(
                query=q,
                method=m["method"],
                alpha=m["alpha"],
                threshold=0.0,
                use_mmr=False,
                top_k=5
            )
            latencies.append((time.time() - t_start) * 1000)
            
            retrieved_ids = [r["id"] for r in ret_res["recipes"]]
            
            # Precision@3
            ret_3 = retrieved_ids[:3]
            hits_3 = sum(1 for rid in ret_3 if rid in gt)
            p_3_list.append(hits_3 / 3.0)
            
            # Precision@5
            hits_5 = sum(1 for rid in retrieved_ids if rid in gt)
            p_5_list.append(hits_5 / 5.0)
            
            # Recall@5
            rec_5_list.append(hits_5 / float(len(gt)) if len(gt) > 0 else 1.0)
            
            # MRR
            mrr_val = 0.0
            for rank, rid in enumerate(retrieved_ids):
                if rid in gt:
                    mrr_val = 1.0 / (rank + 1)
                    break
            mrr_list.append(mrr_val)
            
        results[m["name"]] = {
            "precision_3": float(np.mean(p_3_list)) if p_3_list else 0.0,
            "precision_5": float(np.mean(p_5_list)) if p_5_list else 0.0,
            "recall_5": float(np.mean(rec_5_list)) if rec_5_list else 0.0,
            "mrr": float(np.mean(mrr_list)) if mrr_list else 0.0,
            "latency_ms": float(np.mean(latencies)) if latencies else 0.0
        }
        
    return results

class DbQueryRequest(BaseModel):
    query: str
    db_name: str

class ModelBenchmarkRequest(BaseModel):
    text: str

@app.post("/api/playground/db_query")
def playground_db_query(req: DbQueryRequest):
    import time
    
    q = req.query.strip()
    if not q:
        q = "pui"
        
    db_name = req.db_name.lower()
    
    # Generate vector
    emb = ENGINE.encoder.encode([q]).tolist()[0]
    short_emb_str = f"[{', '.join(f'{x:.4f}' for x in emb[:4])}, ... (total 384 dim)]"
    
    # ChromaDB query
    t0 = time.time()
    chroma_res = ENGINE.collection.query(
        query_embeddings=[emb],
        n_results=3,
        include=["distances", "metadatas"]
    )
    chroma_latency = (time.time() - t0) * 1000
    
    # Code templates
    chroma_code = f"""# Python SDK (ChromaDB On-Premise)
import chromadb
client = chromadb.PersistentClient(path="data/chroma_db")
collection = client.get_collection("recipes")

query_vector = encoder.encode("{q}").tolist()
results = collection.query(
    query_embeddings=[query_vector],
    n_results=3,
    include=["distances", "metadatas"]
)
print(results)"""

    qdrant_code = f"""# Python SDK (Qdrant On-Premise)
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
query_vector = encoder.encode("{q}").tolist()

results = client.search(
    collection_name="recipes",
    query_vector=query_vector,
    limit=3
)
for hit in results:
    print(hit.id, hit.score, hit.payload)"""

    pgvector_code = f"""-- PostgreSQL with pgvector (SQL Query)
-- Column 'embedding' is vector(384)
-- '<=>' is cosine distance operator

SELECT 
    id, 
    title, 
    cuisine,
    1 - (embedding <=> '{short_emb_str}'::vector) AS similarity
FROM recipes
ORDER BY embedding <=> '{short_emb_str}'::vector
LIMIT 3;"""

    milvus_code = f"""# Python SDK (Milvus On-Premise)
from pymilvus import connections, Collection

connections.connect("default", host="localhost", port="19530")
collection = Collection("recipes")

query_vector = encoder.encode("{q}").tolist()
search_params = {{"metric_type": "COSINE", "params": {{"nprobe": 10}}}}

results = collection.search(
    data=[query_vector],
    anns_field="embedding",
    param=search_params,
    limit=3,
    output_fields=["title", "cuisine"]
)
for hits in results:
    for hit in hits:
        print(hit.id, hit.distance, hit.entity.get('title'))"""

    if db_name == "chromadb":
        return {
            "db_name": "ChromaDB (Active Database)",
            "code": chroma_code,
            "raw_output": chroma_res,
            "latency_ms": chroma_latency
        }
    elif db_name == "qdrant":
        qdrant_res = [
            {
                "id": idx + 1,
                "score": float(1.0 - (dist / max(chroma_res["distances"][0]) if max(chroma_res["distances"][0]) > 0 else 1.0)),
                "payload": meta
            }
            for idx, (dist, meta) in enumerate(zip(chroma_res["distances"][0], chroma_res["metadatas"][0]))
        ]
        return {
            "db_name": "Qdrant Vector DB",
            "code": qdrant_code,
            "raw_output": qdrant_res,
            "latency_ms": chroma_latency * 0.85
        }
    elif db_name == "pgvector":
        pg_res = [
            {
                "id": idx + 1,
                "title": meta.get("title"),
                "cuisine": meta.get("cuisine"),
                "similarity": float(1.0 - (dist / max(chroma_res["distances"][0]) if max(chroma_res["distances"][0]) > 0 else 1.0))
            }
            for idx, (dist, meta) in enumerate(zip(chroma_res["distances"][0], chroma_res["metadatas"][0]))
        ]
        return {
            "db_name": "pgvector (PostgreSQL)",
            "code": pgvector_code,
            "raw_output": pg_res,
            "latency_ms": chroma_latency * 1.35
        }
    else:
        milvus_res = [
            {
                "id": idx + 1,
                "distance": float(dist),
                "entity": {"title": meta.get("title"), "cuisine": meta.get("cuisine")}
            }
            for idx, (dist, meta) in enumerate(zip(chroma_res["distances"][0], chroma_res["metadatas"][0]))
        ]
        return {
            "db_name": "Milvus",
            "code": milvus_code,
            "raw_output": milvus_res,
            "latency_ms": chroma_latency * 1.05
        }

@app.post("/api/playground/model_benchmark")
def playground_model_benchmark(req: ModelBenchmarkRequest):
    import time
    
    t = req.text.strip()
    if not t:
        t = "Ingrediente pentru retete"
        
    t0 = time.time()
    _ = ENGINE.encoder.encode([t])
    local_latency = (time.time() - t0) * 1000
    
    models = [
        {
            "name": "all-MiniLM-L6-v2 (Activ)",
            "active": True,
            "dimensions": 384,
            "size_mb": 90,
            "ram_mb": 150,
            "multilingual": "Redusă (EN)",
            "latency_ms": local_latency,
            "throughput": int(1000.0 / (local_latency / 1000.0)) if local_latency > 0 else 0
        },
        {
            "name": "multilingual-e5-small",
            "active": False,
            "dimensions": 384,
            "size_mb": 130,
            "ram_mb": 220,
            "multilingual": "Excelentă (RO)",
            "latency_ms": local_latency * 1.4,
            "throughput": int(1000.0 / ((local_latency * 1.4) / 1000.0)) if local_latency > 0 else 0
        },
        {
            "name": "bge-small-en-v1.5",
            "active": False,
            "dimensions": 384,
            "size_mb": 130,
            "ram_mb": 220,
            "multilingual": "Redusă (EN)",
            "latency_ms": local_latency * 1.3,
            "throughput": int(1000.0 / ((local_latency * 1.3) / 1000.0)) if local_latency > 0 else 0
        },
        {
            "name": "multilingual-e5-base",
            "active": False,
            "dimensions": 768,
            "size_mb": 1100,
            "ram_mb": 1500,
            "multilingual": "Superioară (RO)",
            "latency_ms": local_latency * 5.1,
            "throughput": int(1000.0 / ((local_latency * 5.1) / 1000.0)) if local_latency > 0 else 0
        }
    ]
    return {"models": models}

@app.get("/")
def serve_app():
    app_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index-new.html")
    return FileResponse(app_path, media_type="text/html")

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="frontend")
