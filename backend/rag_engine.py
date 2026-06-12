"""
rag_engine.py — Agentic RAG Engine v3 (ChromaDB + BM25)
=======================================================
"""
import math
import numpy as np
import os
from sklearn.feature_extraction.text import TfidfVectorizer
import chromadb
from sentence_transformers import SentenceTransformer

# Keep Synonyms and Normalizations simplified for brevity but functional
SYNONYMS = {
    "chicken": ["poultry", "breast", "thighs"],
    "beef": ["meat", "steak", "ground beef"],
    "tomato": ["tomatoes", "cherry tomatoes", "passata", "sauce"],
    "pasta": ["spaghetti", "penne", "noodles", "linguine", "macaroni", "bucatini"],
    "cheese": ["parmesan", "feta", "mozzarella", "cheddar", "pecorino"],
    "egg": ["eggs", "yolk"],
}

NORMALIZATIONS = {
    "tomatoes": "tomato", "potatoes": "potato", "onions": "onion",
    "mushrooms": "mushroom", "eggs": "egg", "lemons": "lemon",
}

class BM25:
    def __init__(self, corpus: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.tokenized = [doc.lower().split() for doc in corpus]
        self.n_docs = len(self.tokenized)
        self.avgdl = sum(len(d) for d in self.tokenized) / max(self.n_docs, 1)
        self.dl = np.array([len(d) for d in self.tokenized], dtype=float)
        self.df = {}
        for doc in self.tokenized:
            for term in set(doc):
                self.df[term] = self.df.get(term, 0) + 1

    def get_scores(self, query: str) -> np.ndarray:
        query_terms = list(set(query.lower().split()))
        scores = np.zeros(self.n_docs)
        for term in query_terms:
            if term not in self.df: continue
            idf = math.log((self.n_docs - self.df[term] + 0.5) / (self.df[term] + 0.5) + 1)
            for i, doc in enumerate(self.tokenized):
                tf = doc.count(term)
                if tf == 0: continue
                tf_norm = tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * self.dl[i] / self.avgdl))
                scores[i] += idf * tf_norm
        if np.max(scores) > 0:
            scores = scores / np.max(scores)
        return scores

class RecipeRAGEngine:
    def __init__(self, recipes: list[dict]):
        self.recipes = recipes
        self.recipe_by_id = {str(r["id"]): r for r in self.recipes}
        self.recipe_index_by_id = {str(r["id"]): i for i, r in enumerate(self.recipes)}
        
        print("Loading SentenceTransformer model...")
        import torch
        device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
        self.encoder = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', device=device)
        
        # Init ChromaDB
        db_path = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        
        # Recreate collection to ensure fresh start
        try:
            self.chroma_client.delete_collection("recipes")
        except:
            pass
            
        self.collection = self.chroma_client.create_collection("recipes")
        
        # Smart dynamic vocabulary mapping
        self.english_vocab = []
        self.vocab_embeddings = None
        self._build_vocab_index()
        
        self._build_index()

    def _build_vocab_index(self):
        import string
        stop_words = {"with", "and", "the", "for", "in", "of", "a", "an", "to", "or", "at", "by", "from", "on", "fresh", "ground", "chopped", "sliced", "diced", "powder", "taste", "salt", "pepper"}
        
        vocab = set()
        for r in self.recipes:
            text = (r.get("title", "") + " " + " ".join(r.get("ingredients", []))).lower()
            text = text.translate(str.maketrans("", "", string.punctuation + string.digits))
            for word in text.split():
                if len(word) > 2 and word.isalpha() and word not in stop_words:
                    vocab.add(word)
                    
        self.english_vocab = sorted(list(vocab))
        if self.english_vocab:
            print(f"Embedding {len(self.english_vocab)} English vocabulary terms for dynamic semantic translation...")
            self.vocab_embeddings = self.encoder.encode(self.english_vocab)

    def _build_index(self):
        print(f"Indexing {len(self.recipes)} recipes into ChromaDB & BM25...")
        ing_corpus = []
        texts_to_embed = []
        ids = []
        metadatas = []
        
        for r in self.recipes:
            ings = " ".join(r.get("ingredients", [])).lower()
            title = r.get("title", "")
            steps = " ".join(r.get("steps", []))
            
            ing_corpus.append(ings)
            
            # Text for semantic search
            doc_text = f"Title: {title}. Ingredients: {ings}. Instructions: {steps}"
            texts_to_embed.append(doc_text)
            ids.append(str(r["id"]))
            
            # Metadata requires simple types
            metadatas.append({
                "title": title,
                "cuisine": r.get("cuisine", ""),
                "ingredients": ings
            })

        self.bm25 = BM25(ing_corpus)
        
        # Embed and add to Chroma
        batch_size = 200
        for i in range(0, len(texts_to_embed), batch_size):
            batch_texts = texts_to_embed[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size]
            
            embeddings = self.encoder.encode(batch_texts).tolist()
            
            self.collection.add(
                documents=batch_texts,
                embeddings=embeddings,
                ids=batch_ids,
                metadatas=batch_metadatas
            )
            
        print(" ChromaDB + BM25 indexing complete!")

    def _expand_query(self, query: str) -> str:
        words = query.lower().split()
        expanded = set(words)
        
        if self.vocab_embeddings is not None and len(self.english_vocab) > 0:
            for w in words:
                w_norm = NORMALIZATIONS.get(w, w)
                expanded.add(w_norm)
                
                if w_norm in SYNONYMS:
                    expanded.update(SYNONYMS[w_norm])
                    
                # Dynamically translate any non-English/alternative query term using embedding similarity
                if w_norm not in self.english_vocab:
                    w_emb = self.encoder.encode([w_norm])
                    dots = np.dot(self.vocab_embeddings, w_emb[0])
                    norms_vocab = np.linalg.norm(self.vocab_embeddings, axis=1)
                    norm_w = np.linalg.norm(w_emb[0])
                    
                    if norm_w > 0:
                        similarities = dots / (norms_vocab * norm_w)
                        matches = []
                        for idx in np.where(similarities > 0.55)[0]:
                            matches.append((self.english_vocab[idx], similarities[idx]))
                        
                        # Sort and pick top 2 closest English terms
                        matches.sort(key=lambda x: x[1], reverse=True)
                        for m_word, score in matches[:2]:
                            expanded.add(m_word)
        else:
            for w in words:
                w = NORMALIZATIONS.get(w, w)
                expanded.add(w)
                if w in SYNONYMS:
                    expanded.update(SYNONYMS[w])
                    
        return " ".join(expanded)

    def retrieve(self, query: str, filters: dict = None, top_k: int = 5) -> list[dict]:
        expanded_q = self._expand_query(query)
        
        # BM25 scores
        bm25_scores = self.bm25.get_scores(expanded_q)
        
        # ChromaDB Dense Search
        q_emb = self.encoder.encode([query]).tolist()
        chroma_res = self.collection.query(
            query_embeddings=q_emb,
            n_results=len(self.recipes), # Get all to combine with BM25
            include=["distances", "metadatas"]
        )
        
        hybrid_results = []
        
        if chroma_res and chroma_res["ids"] and len(chroma_res["ids"][0]) > 0:
            ids = chroma_res["ids"][0]
            distances = chroma_res["distances"][0]
            
            max_dist = max(distances) if distances and max(distances) > 0 else 1.0
            
            for rank, (doc_id, dist) in enumerate(zip(ids, distances)):
                recipe = self.recipe_by_id.get(str(doc_id))
                idx = self.recipe_index_by_id.get(str(doc_id))

                if recipe is None or idx is None:
                    continue
                
                # Normalize semantic score (lower distance = higher score)
                semantic_score = 1.0 - (dist / max_dist)
                
                # Hybrid fusion
                sparse_score = bm25_scores[idx]
                hybrid_score = (0.7 * semantic_score) + (0.3 * sparse_score)
                
                # Apply filters
                if filters:
                    if filters.get("cuisine") and filters["cuisine"] != "Any":
                        if recipe.get("cuisine") != filters["cuisine"]:
                            continue
                
                recipe_copy = dict(recipe)
                recipe_copy["hybrid_score"] = float(hybrid_score)
                recipe_copy["semantic_score"] = float(semantic_score)
                recipe_copy["bm25_score"] = float(sparse_score)
                
                hybrid_results.append(recipe_copy)
                
        # Sort by hybrid score
        hybrid_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return hybrid_results[:top_k]

    def retrieve_custom(
        self,
        query: str,
        method: str = "hybrid",
        alpha: float = 0.7,
        threshold: float = 0.0,
        use_mmr: bool = False,
        mmr_lambda: float = 0.5,
        filters: dict = None,
        top_k: int = 5
    ) -> dict:
        import time
        start_time = time.time()
        
        expanded_q = self._expand_query(query)
        
        # 1. BM25 scores
        bm25_scores = self.bm25.get_scores(expanded_q)
        
        # 2. ChromaDB Dense Search
        q_emb = self.encoder.encode([query]).tolist()[0]
        chroma_res = self.collection.query(
            query_embeddings=[q_emb],
            n_results=len(self.recipes),
            include=["distances", "metadatas", "embeddings"]
        )
        
        results = []
        discarded_by_threshold = 0
        
        if chroma_res and chroma_res["ids"] and len(chroma_res["ids"][0]) > 0:
            ids = chroma_res["ids"][0]
            distances = chroma_res["distances"][0]
            embeddings = chroma_res["embeddings"][0] if ("embeddings" in chroma_res and chroma_res["embeddings"] is not None) else None
            
            max_dist = max(distances) if distances and max(distances) > 0 else 1.0
            
            embs_list = embeddings if embeddings is not None else [None] * len(ids)
            for doc_id, dist, emb in zip(ids, distances, embs_list):
                recipe = self.recipe_by_id.get(str(doc_id))
                idx = self.recipe_index_by_id.get(str(doc_id))

                if recipe is None or idx is None:
                    continue
                
                # Apply filter checks (cuisine/difficulty/max_time)
                if filters:
                    if filters.get("cuisine") and filters["cuisine"] != "Any":
                        if recipe.get("cuisine") != filters["cuisine"]:
                            continue
                    if filters.get("difficulty") and filters["difficulty"] != "Any":
                        if recipe.get("difficulty") != filters["difficulty"]:
                            continue
                    if filters.get("max_time"):
                        time_min = recipe.get("time_minutes")
                        if time_min and time_min > int(filters["max_time"]):
                            continue
                
                # Normalize scores (BM25 is already normalized to 0-1, semantic score is distance-normalized)
                semantic_score = float(1.0 - (dist / max_dist)) if max_dist > 0 else 1.0
                sparse_score = float(bm25_scores[idx])
                
                # Hybrid fusion
                hybrid_score = float((alpha * semantic_score) + ((1.0 - alpha) * sparse_score))
                
                if method == "dense":
                    final_score = semantic_score
                elif method == "sparse":
                    final_score = sparse_score
                else:
                    final_score = hybrid_score
                
                # Check threshold
                if final_score < threshold:
                    discarded_by_threshold += 1
                    continue
                
                recipe_copy = dict(recipe)
                recipe_copy["retrieval_score"] = final_score
                recipe_copy["semantic_score"] = semantic_score
                recipe_copy["bm25_score"] = sparse_score
                recipe_copy["hybrid_score"] = hybrid_score
                recipe_copy["embedding"] = emb
                
                results.append(recipe_copy)
        
        # Sort by final score initially
        results.sort(key=lambda x: x["retrieval_score"], reverse=True)
        
        # MMR Reranking
        if use_mmr and len(results) > 1:
            reranked = []
            # Take top candidates to rerank
            candidates = results[:min(15, len(results))]
            candidate_embs = [c["embedding"] for c in candidates]
            
            selected_indices = []
            
            # Helper for similarity
            def cos_sim(a, b):
                if a is None or b is None: return 0.0
                dot = np.dot(a, b)
                norm_a = np.linalg.norm(a)
                norm_b = np.linalg.norm(b)
                if norm_a == 0 or norm_b == 0: return 0.0
                return float(dot / (norm_a * norm_b))
            
            # MMR selection loop
            while len(selected_indices) < top_k and len(selected_indices) < len(candidates):
                best_mmr_score = -999999.0
                best_candidate_idx = -1
                
                for i in range(len(candidates)):
                    if i in selected_indices:
                        continue
                    
                    sim_q = candidates[i]["retrieval_score"]
                    
                    if len(selected_indices) == 0:
                        sim_d = 0.0
                    else:
                        sim_d = max(cos_sim(candidate_embs[i], candidate_embs[j]) for j in selected_indices)
                    
                    mmr_score = (mmr_lambda * sim_q) - ((1.0 - mmr_lambda) * sim_d)
                    
                    if mmr_score > best_mmr_score:
                        best_mmr_score = mmr_score
                        best_candidate_idx = i
                
                if best_candidate_idx != -1:
                    selected_indices.append(best_candidate_idx)
                else:
                    break
                    
            reranked = [candidates[i] for i in selected_indices]
            # Fill up from remaining sorted if MMR failed to return top_k
            if len(reranked) < min(top_k, len(results)):
                for r in results:
                    if r not in reranked:
                        reranked.append(r)
                    if len(reranked) >= min(top_k, len(results)):
                        break
            results = reranked
            
        # Clean up temporary embedding fields
        for r in results:
            if "embedding" in r:
                del r["embedding"]
                
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            "recipes": results[:top_k],
            "query_expanded": expanded_q,
            "discarded_count": discarded_by_threshold,
            "total_matches": len(results) + discarded_by_threshold,
            "latency_ms": latency_ms
        }

    def register_recipe(self, r: dict):
        """Register a dynamically created recipe into RAG, ChromaDB, and HNSW if available"""
        if "id" not in r:
            r["id"] = f"invented_{len(self.recipes) + 1}"
        
        rid = str(r["id"])
        
        # Check duplicate
        if any(str(x.get("id")) == rid for x in self.recipes):
            return
            
        # 1. Add to local list
        self.recipes.append(r)

        rid = str(r["id"])
        self.recipe_by_id[rid] = r
        self.recipe_index_by_id[rid] = len(self.recipes) - 1
        
        # 2. Embed and add to ChromaDB
        ings = " ".join(r.get("ingredients", [])).lower()
        title = r.get("title", "")
        steps = " ".join(r.get("steps", []))
        doc_text = f"Title: {title}. Ingredients: {ings}. Instructions: {steps}"
        
        emb = self.encoder.encode([doc_text])
        emb_list = emb.tolist()
        
        metadata = {
            "title": title,
            "cuisine": r.get("cuisine", ""),
            "ingredients": ings
        }
        
        try:
            self.collection.add(
                documents=[doc_text],
                embeddings=emb_list,
                ids=[rid],
                metadatas=[metadata]
            )
        except Exception as e:
            print(f"Error adding dynamic recipe to ChromaDB: {e}")
            
        # 3. Rebuild BM25
        try:
            ing_corpus = [" ".join(x.get("ingredients", [])).lower() for x in self.recipes]
            self.bm25 = BM25(ing_corpus)
        except Exception as e:
            print(f"Error rebuilding BM25: {e}")
            
        # 4. Add to HNSW simulator if registered
        hnsw = getattr(self, "hnsw_simulator", None)
        if hnsw is not None:
            try:
                hnsw.add_recipe(r, emb[0])
            except Exception as e:
                print(f"Error adding dynamic recipe to HNSW simulator: {e}")

