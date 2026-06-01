"""
main.py — FastAPI backend v2
============================
Endpoint-uri noi față de v1:
  GET  /api/random           → rețetă aleatorie (opțional filtrat pe bucătărie)
  POST /api/search           → retrieval RAG pur (fără invenție)
  GET  /api/similar          → rețete similare cu un titlu dat
  GET  /api/idf              → greutăți IDF + distinctivitate per ingredient
  GET  /api/cuisine-detect   → detectează bucătăria din ingrediente

Endpoint-uri existente (îmbunătățite):
  GET  /api/stats            → include metadata engine v2
  GET  /api/cuisines         → lista bucătăriilor
  GET  /api/difficulties     → lista dificultăților
  GET  /api/recipes          → browse DB paginat
  POST /api/invent           → inventează rețete (cu debug RAG în răspuns)
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
from recipe_generator import invent_recipes

# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Recipe Inventor API v2",
    description=(
        "RAG-powered recipe engine — BM25 + Multi-field TF-IDF + MMR + "
        "Query Expansion + Cuisine Detection. Fără LLM."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup: load data & build all indices ────────────────────────────────────
print("🍳 Loading recipe database...")
ALL_RECIPES = load_recipes()
ENGINE      = RecipeRAGEngine(ALL_RECIPES)
print(f"✅ API v2 ready — {len(ALL_RECIPES)} recipes indexed.")


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────────────────────────────────────
class InventRequest(BaseModel):
    ingredients: list[str]     = Field(..., example=["chicken", "garlic", "lemon"])
    cuisine:     Optional[str] = Field("Any")
    difficulty:  Optional[str] = Field("Any")
    max_time:    Optional[int] = Field(None)
    num_recipes: Optional[int] = Field(5, ge=1, le=10)
    use_mmr:     Optional[bool]= Field(True,  description="Activează MMR diversity re-ranking")
    mmr_lambda:  Optional[float]= Field(0.65, description="λ MMR: 1=relevanță pură, 0=diversitate pură")


class SearchRequest(BaseModel):
    ingredients: list[str]     = Field(..., example=["salmon", "soy sauce"])
    cuisine:     Optional[str] = Field(None)
    difficulty:  Optional[str] = Field(None)
    max_time:    Optional[int] = Field(None)
    k:           Optional[int] = Field(10, ge=1, le=30)
    use_mmr:     Optional[bool]= Field(True)


# ─────────────────────────────────────────────────────────────────────────────
# API — Stats & meta
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/stats", summary="Statistici engine RAG")
def get_stats():
    return ENGINE.get_stats()


@app.get("/api/cuisines", summary="Lista bucătăriilor disponibile")
def get_cuisines():
    return get_unique_cuisines(ALL_RECIPES)


@app.get("/api/difficulties", summary="Lista niveluri dificultate")
def get_difficulties():
    return get_unique_difficulties(ALL_RECIPES)


# ─────────────────────────────────────────────────────────────────────────────
# API — Browse
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/recipes", summary="Browse baza de date paginat")
def list_recipes(
    cuisine:    Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    limit:      int           = Query(24, ge=1, le=100),
    offset:     int           = Query(0, ge=0),
):
    filtered = ALL_RECIPES
    if cuisine and cuisine not in ("Any", "Orice"):
        filtered = [r for r in filtered if r.get("cuisine") == cuisine]
    if difficulty and difficulty not in ("Any", "Orice"):
        filtered = [r for r in filtered if r.get("difficulty") == difficulty]

    # Return only base recipes (no variants) for browsing
    seen, base_only = set(), []
    for r in filtered:
        title = r.get("title", "")
        for p in ("Fiery ", "Quick ", "Plant-Based ", "Light & Healthy "):
            if title.startswith(p):
                title = title[len(p):]
                break
        if title not in seen:
            seen.add(title)
            base_only.append(r)

    page = base_only[offset: offset + limit]
    return {
        "recipes": page,
        "total":   len(base_only),
        "offset":  offset,
        "limit":   limit,
    }


@app.get("/api/random", summary="Rețetă aleatorie din baza de date")
def get_random(cuisine: Optional[str] = Query(None)):
    pool = ALL_RECIPES
    if cuisine and cuisine not in ("Any", "Orice"):
        pool = [r for r in pool if r.get("cuisine") == cuisine]
    if not pool:
        raise HTTPException(status_code=404, detail="Nicio rețetă găsită cu acești parametri.")
    return random.choice(pool)


# ─────────────────────────────────────────────────────────────────────────────
# API — RAG Search (retrieval pur, fără invenție)
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/search", summary="Retrieval RAG pur — returnează rețete existente din DB")
def search_recipes(req: SearchRequest):
    """
    Retrieval RAG fără etapa de generare.
    Returnează rețete REALE din baza de date, sortate după scorul hibrid.
    Util pentru a vedea ce găsește motorul RAG înaintea invenției.
    """
    cleaned = [i.strip().lower() for i in req.ingredients if i.strip()]
    if not cleaned:
        raise HTTPException(status_code=400, detail="Adaugă cel puțin un ingredient.")

    results = ENGINE.retrieve(
        user_ingredients  = cleaned,
        k                 = req.k or 10,
        cuisine_filter    = req.cuisine,
        difficulty_filter = req.difficulty,
        max_time          = req.max_time,
        use_mmr           = req.use_mmr if req.use_mmr is not None else True,
    )
    if not results:
        raise HTTPException(status_code=404, detail="Nicio rețetă găsită. Încearcă alte ingrediente.")

    return {
        "results":   results,
        "count":     len(results),
        "query":     cleaned,
        "total_db":  len(ALL_RECIPES),
    }


# ─────────────────────────────────────────────────────────────────────────────
# API — Similar recipes
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/similar", summary="Rețete similare cu un titlu dat")
def get_similar(
    title: str = Query(..., description="Titlul rețetei de referință"),
    k:     int = Query(5, ge=1, le=10),
):
    results = ENGINE.find_similar(title, k=k)
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"Rețeta '{title}' nu a fost găsită sau nu există similare.",
        )
    return {"similar": results, "query_title": title, "count": len(results)}


# ─────────────────────────────────────────────────────────────────────────────
# API — IDF analysis
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/idf", summary="Analiza IDF (distinctivitate) per ingredient")
def get_idf(
    ingredients: str = Query(..., description="Ingrediente separate prin virgulă"),
):
    """
    Returnează greutatea IDF pentru fiecare ingredient.
    IDF mare → ingredient rar în corpus (distinctiv).
    IDF mic  → ingredient comun (apare în multe rețete).
    Include sinonimele folosite în query expansion.
    """
    ing_list = [i.strip() for i in ingredients.split(",") if i.strip()]
    if not ing_list:
        raise HTTPException(status_code=400, detail="Adaugă cel puțin un ingredient.")
    if len(ing_list) > 20:
        raise HTTPException(status_code=400, detail="Maxim 20 ingrediente.")
    return ENGINE.explain_idf(ing_list)


# ─────────────────────────────────────────────────────────────────────────────
# API — Cuisine detection
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/cuisine-detect", summary="Detectează bucătăria din ingrediente")
def detect_cuisine(
    ingredients: str = Query(..., description="Ingrediente separate prin virgulă"),
):
    """
    Analizează ingredientele și returnează bucătăriile probabile cu scoruri.
    Folosit intern de motorul RAG pentru cuisine boosting.
    """
    ing_list = [i.strip() for i in ingredients.split(",") if i.strip()]
    if not ing_list:
        raise HTTPException(status_code=400, detail="Adaugă cel puțin un ingredient.")

    scores = ENGINE._detect_cuisine(ing_list)
    if not scores:
        return {"detected": None, "scores": {}, "ingredients": ing_list}

    best = max(scores, key=scores.get)
    total = sum(scores.values())
    confidence = {k: round(v / total, 2) for k, v in scores.items()}

    return {
        "detected":   best,
        "confidence": confidence,
        "scores":     scores,
        "ingredients": ing_list,
    }


# ─────────────────────────────────────────────────────────────────────────────
# API — Invent (main endpoint, enhanced)
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/api/invent", summary="Inventează rețete noi din ingrediente")
def invent(req: InventRequest):
    """
    Pipeline complet RAG + Generare:
      1. Normalizare + Query Expansion
      2. Retrieval hibrid (BM25 + TF-IDF multi-field)
      3. Cuisine boosting
      4. MMR diversity re-ranking
      5. Template-based recipe invention
    """
    cleaned = [i.strip().lower() for i in req.ingredients if i.strip()]
    if not cleaned:
        raise HTTPException(status_code=400, detail="Adaugă cel puțin un ingredient.")
    if len(cleaned) > 20:
        raise HTTPException(status_code=400, detail="Maxim 20 ingrediente.")

    retrieve_k = max((req.num_recipes or 5) + 8, 20)
    retrieved  = ENGINE.retrieve(
        user_ingredients  = cleaned,
        k                 = retrieve_k,
        cuisine_filter    = req.cuisine,
        difficulty_filter = req.difficulty,
        max_time          = req.max_time,
        use_mmr           = req.use_mmr if req.use_mmr is not None else True,
        mmr_lambda        = req.mmr_lambda or 0.65,
    )

    if not retrieved:
        raise HTTPException(
            status_code=404,
            detail="Nicio rețetă găsită. Încearcă alte ingrediente sau elimină filtrele.",
        )

    invented = invent_recipes(
        user_ingredients  = cleaned,
        retrieved_recipes = retrieved,
        num_recipes       = req.num_recipes or 5,
    )

    # Attach RAG debug to each invented recipe
    for i, recipe in enumerate(invented):
        if i < len(retrieved):
            src = retrieved[i]
            recipe["rag_debug"] = {
                "hybrid_score":     src.get("hybrid_score", 0),
                "bm25_score":       src.get("bm25_score", 0),
                "tfidf_ing_score":  src.get("tfidf_ing_score", 0),
                "tfidf_full_score": src.get("tfidf_full_score", 0),
                "tag_score":        src.get("tag_score", 0),
                "flavor_score":     src.get("flavor_score", 0),
                "exact_bonus":      src.get("exact_bonus", 0),
                "cuisine_boost":    src.get("cuisine_boost", 0),
                "matched_user_ingredients":    src.get("matched_user_ingredients", []),
                "user_ingredient_recall":      src.get("user_ingredient_recall", 0),
                "recipe_ingredient_precision": src.get("recipe_ingredient_precision", 0),
                "expanded_terms":   src.get("expanded_terms", []),
                "detected_cuisine": src.get("detected_cuisine"),
                "cuisine_hints":    src.get("cuisine_hints_found", {}),
            }

    # Detected cuisine from first result
    detected = retrieved[0].get("detected_cuisine") if retrieved else None
    cuisine_hints = retrieved[0].get("cuisine_hints_found", {}) if retrieved else {}

    return {
        "recipes":          invented,
        "retrieved_count":  len(retrieved),
        "total_db":         len(ALL_RECIPES),
        "query":            cleaned,
        "detected_cuisine": detected,
        "cuisine_hints":    cuisine_hints,
        "mmr_used":         req.use_mmr,
        "mmr_lambda":       req.mmr_lambda,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Serve main app (root)
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
def serve_app():
    app_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index-new.html")
    return FileResponse(app_path, media_type="text/html")

# ─────────────────────────────────────────────────────────────────────────────
# Serve frontend static files (MUST be last)
# ─────────────────────────────────────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="frontend")
