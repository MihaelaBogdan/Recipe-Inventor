"""
rag_engine.py — Enhanced RAG Engine v2
=======================================
Tehnici RAG implementate:
  1. BM25 (Okapi BM25)        — ranking probabilistic clasic
  2. Multi-field TF-IDF       — index separat pt ingrediente / taguri / flavor / full
  3. Query expansion          — sinonime ingrediente (ex: "pui" → "poultry, breast, thigh")
  4. Ingredient normalisation — plural/singular, aliasuri (ex: "roșii" = "tomato")
  5. Hybrid scoring           — BM25 * 0.30 + TF-IDF_ing * 0.35 + TF-IDF_full * 0.15 + tag * 0.10
  6. Cuisine detection        — detectează bucătăria din ingrediente → boost scoruri
  7. Exact & partial match bonus — bonus per ingredient găsit exact sau parțial
  8. MMR re-ranking           — Maximal Marginal Relevance pentru diversitate rezultate
  9. Retrieval debug info     — scor detaliat per rețetă pentru transparență
"""

import math
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ─────────────────────────────────────────────────────────────────────────────
# 1. INGREDIENT SYNONYMS  (query expansion)
# ─────────────────────────────────────────────────────────────────────────────
SYNONYMS: dict[str, list[str]] = {
    "chicken":      ["poultry", "fowl", "breast", "thighs", "drumstick"],
    "beef":         ["meat", "steak", "sirloin", "chuck", "ground beef", "veal"],
    "pork":         ["bacon", "ham", "pancetta", "lard", "belly", "ribs"],
    "lamb":         ["mutton", "sheep", "leg of lamb", "kofta"],
    "fish":         ["seafood", "cod", "tilapia", "sea bass", "halibut"],
    "salmon":       ["fish", "seafood", "pink fish", "trout"],
    "shrimp":       ["prawn", "seafood", "langoustine", "scampi"],
    "tomato":       ["tomatoes", "cherry tomatoes", "canned tomatoes", "passata", "san marzano"],
    "garlic":       ["allium", "clove", "ail"],
    "onion":        ["shallot", "leek", "scallion", "green onion", "allium"],
    "lemon":        ["citrus", "lime", "zest", "citron"],
    "lime":         ["citrus", "lemon", "kaffir lime"],
    "pasta":        ["spaghetti", "penne", "fettuccine", "noodles", "linguine", "rigatoni"],
    "mushroom":     ["porcini", "shiitake", "portobello", "cremini", "chanterelle"],
    "cheese":       ["parmesan", "feta", "mozzarella", "cheddar", "gruyere", "ricotta"],
    "chili":        ["chilli", "cayenne", "jalapeño", "serrano", "pepper flakes", "dried chili"],
    "herbs":        ["basil", "thyme", "oregano", "parsley", "cilantro", "mint", "tarragon"],
    "beans":        ["legumes", "chickpeas", "lentils", "black beans", "cannellini"],
    "lentils":      ["legumes", "dal", "red lentils", "green lentils", "masoor"],
    "rice":         ["arborio", "jasmine", "basmati", "grain", "risotto"],
    "coconut":      ["coconut milk", "coconut cream", "desiccated coconut"],
    "cream":        ["heavy cream", "crème fraîche", "double cream", "whipping cream"],
    "egg":          ["eggs", "yolk", "egg yolk", "albumin"],
    "butter":       ["ghee", "margarine", "clarified butter"],
    "soy sauce":    ["tamari", "soya", "shoyu", "kecap manis"],
    "ginger":       ["galangal", "fresh ginger", "ground ginger"],
    "pepper":       ["black pepper", "white pepper", "peppercorn"],
    "spinach":      ["kale", "chard", "greens", "leafy greens", "baby spinach"],
    "eggplant":     ["aubergine", "melanzane", "brinjal"],
    "zucchini":     ["courgette", "summer squash"],
    "chickpeas":    ["garbanzo", "legumes", "ceci", "hummus"],
    "tahini":       ["sesame paste", "sesame", "sesame butter"],
    "yogurt":       ["yoghurt", "greek yogurt", "labneh", "curd"],
    "tofu":         ["bean curd", "silken tofu", "firm tofu", "tempeh"],
    "avocado":      ["guacamole"],
    "quinoa":       ["grain", "protein grain", "superfood"],
    "sweet potato": ["yam", "batata", "kumara"],
}

# ─────────────────────────────────────────────────────────────────────────────
# 2. INGREDIENT NORMALISATIONS  (many forms → canonical)
# ─────────────────────────────────────────────────────────────────────────────
NORMALIZATIONS: dict[str, str] = {
    "tomatoes": "tomato", "potatoes": "potato", "onions": "onion",
    "mushrooms": "mushroom", "eggs": "egg", "lemons": "lemon",
    "limes": "lime", "carrots": "carrot", "peppers": "pepper",
    "cloves": "garlic", "breast": "chicken", "thighs": "chicken",
    "sirloin": "beef", "chuck": "beef", "prawns": "shrimp",
    "canned tomatoes": "tomato", "cherry tomatoes": "tomato",
    "ground beef": "beef", "ground lamb": "lamb", "ground pork": "pork",
    "heavy cream": "cream", "double cream": "cream",
    "green onion": "onion", "scallion": "onion", "shallot": "onion",
    "aubergine": "eggplant", "courgette": "zucchini",
    "garbanzo": "chickpeas", "ceci": "chickpeas",
    "galangal": "ginger", "tamari": "soy sauce",
    "kale": "spinach", "chard": "spinach",
    "porcini mushrooms": "mushroom", "shiitake": "mushroom",
    "parmesan cheese": "parmesan", "feta cheese": "feta",
    "canned tomatoes": "tomato", "chicken breast": "chicken",
    "chicken thighs": "chicken", "salmon fillets": "salmon",
    "beef sirloin": "beef", "pork shoulder": "pork",
    "ground lamb": "lamb", "veal shanks": "veal",
    "olive oil": "olive oil",  # keep as-is
    "jasmine rice": "rice", "arborio rice": "rice", "basmati rice": "rice",
    "ramen noodles": "noodles", "rice noodles": "noodles",
    "spaghetti": "pasta", "penne pasta": "pasta", "fettuccine": "pasta",
    "macaroni": "pasta",
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. CUISINE HINTS  (ingredient → cuisine boost)
# ─────────────────────────────────────────────────────────────────────────────
CUISINE_HINTS: dict[str, list[str]] = {
    "Italian":        ["pasta", "spaghetti", "penne", "arborio", "mozzarella",
                       "parmesan", "basil", "prosciutto", "ricotta", "pancetta"],
    "Thai":           ["lemongrass", "fish sauce", "galangal", "thai basil",
                       "kaffir lime", "palm sugar", "tamarind paste", "pad"],
    "Indian":         ["garam masala", "turmeric", "cumin", "coriander",
                       "cardamom", "paneer", "dal", "naan", "ghee", "curry"],
    "Chinese":        ["soy sauce", "sesame oil", "wok", "shaoxing wine",
                       "five spice", "doubanjiang", "hoisin", "bok choy"],
    "Japanese":       ["miso", "dashi", "mirin", "sake", "nori", "wasabi",
                       "ramen", "bonito", "sushi", "ponzu", "matcha"],
    "Korean":         ["gochujang", "doenjang", "kimchi", "sesame oil",
                       "korean", "bulgogi", "gochugaru", "soju"],
    "Mediterranean":  ["olive oil", "feta", "sumac", "tahini", "za'atar",
                       "halloumi", "capers", "kalamata", "phyllo"],
    "Mexican":        ["jalapeño", "cilantro", "lime", "achiote", "tortilla",
                       "avocado", "tomatillo", "chipotle", "epazote"],
    "French":         ["butter", "cognac", "gruyere", "dijon", "herbes de provence",
                       "baguette", "crème", "tarragon", "mirepoix"],
    "Middle Eastern": ["tahini", "sumac", "za'atar", "harissa", "ras el hanout",
                       "flatbread", "pita", "pomegranate", "baharat"],
    "American":       ["bbq sauce", "cheddar", "cornmeal", "cajun", "clam",
                       "pulled pork", "bourbon", "ranch"],
    "Vietnamese":     ["fish sauce", "rice noodles", "bean sprouts", "star anise",
                       "lemongrass", "pho", "nuoc cham"],
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. SEMANTIC FLAVOR EXPANSION  (flavor words → ingredient hints)
# ─────────────────────────────────────────────────────────────────────────────
FLAVOR_TO_INGREDIENTS: dict[str, list[str]] = {
    "spicy":    ["chili", "cayenne", "jalapeño", "gochujang", "sriracha"],
    "sour":     ["lemon", "lime", "vinegar", "tamarind", "yogurt"],
    "sweet":    ["honey", "sugar", "mirin", "palm sugar", "maple syrup"],
    "smoky":    ["smoked paprika", "chipotle", "liquid smoke", "BBQ"],
    "umami":    ["soy sauce", "miso", "parmesan", "anchovies", "mushroom"],
    "creamy":   ["cream", "coconut milk", "yogurt", "butter", "tahini"],
    "fresh":    ["lemon", "lime", "herbs", "cilantro", "mint", "parsley"],
    "earthy":   ["mushroom", "lentils", "cumin", "truffle", "beet"],
    "nutty":    ["sesame", "tahini", "peanuts", "almonds", "pine nuts"],
    "herby":    ["basil", "oregano", "thyme", "rosemary", "tarragon"],
}


# ─────────────────────────────────────────────────────────────────────────────
# 5. BM25 (Okapi BM25)  — pure-Python, no external dependency
# ─────────────────────────────────────────────────────────────────────────────
class BM25:
    """
    Okapi BM25 probabilistic ranking.
    k1=1.5, b=0.75 — standard IR defaults.
    """
    def __init__(self, corpus: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b  = b
        self.tokenized = [doc.lower().split() for doc in corpus]
        self.n_docs    = len(self.tokenized)
        self.avgdl     = sum(len(d) for d in self.tokenized) / max(self.n_docs, 1)
        self.dl        = np.array([len(d) for d in self.tokenized], dtype=float)
        # Document frequency per term
        self.df: dict[str, int] = {}
        for doc in self.tokenized:
            for term in set(doc):
                self.df[term] = self.df.get(term, 0) + 1

    def get_scores(self, query: str) -> np.ndarray:
        query_terms = list(set(query.lower().split()))  # unique query terms
        scores = np.zeros(self.n_docs)
        for term in query_terms:
            if term not in self.df:
                continue
            idf = math.log(
                (self.n_docs - self.df[term] + 0.5) / (self.df[term] + 0.5) + 1
            )
            for i, doc in enumerate(self.tokenized):
                tf = doc.count(term)
                if tf == 0:
                    continue
                tf_norm = tf * (self.k1 + 1) / (
                    tf + self.k1 * (1 - self.b + self.b * self.dl[i] / self.avgdl)
                )
                scores[i] += idf * tf_norm
        return scores


# ─────────────────────────────────────────────────────────────────────────────
# 6. MAIN RAG ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class RecipeRAGEngine:
    """
    Hybrid RAG retrieval engine combining:
      - BM25 probabilistic ranking
      - Multi-field TF-IDF (ingredients / tags / flavor / full)
      - Query expansion (synonyms + flavor words)
      - Ingredient normalisation
      - Cuisine detection & score boosting
      - Exact + partial ingredient match bonus
      - MMR re-ranking for diversity
    """

    def __init__(self, recipes: list[dict]):
        self.recipes = recipes
        self._build_index()

    # ── Index building ────────────────────────────────────────────────────────
    def _build_index(self):
        ing_corpus    = []
        tag_corpus    = []
        flavor_corpus = []
        full_corpus   = []

        for r in self.recipes:
            ings    = " ".join(r.get("ingredients", [])).lower()
            tags    = " ".join(r.get("tags", [])).lower()
            flavor  = " ".join(r.get("flavor_profile", [])).lower()
            cuisine = r.get("cuisine", "").lower()
            tech    = r.get("key_technique", "").lower()
            desc    = r.get("description", "").lower()

            ing_corpus.append(ings)
            tag_corpus.append(f"{tags} {cuisine}")
            flavor_corpus.append(f"{flavor} {tech}")
            full_corpus.append(f"{ings} {cuisine} {tags} {flavor} {tech} {desc}")

        vec_kw = dict(ngram_range=(1, 2), sublinear_tf=True, min_df=1)

        self.ing_vec  = TfidfVectorizer(**vec_kw, max_features=10_000)
        self.tag_vec  = TfidfVectorizer(**vec_kw, max_features=5_000)
        self.flv_vec  = TfidfVectorizer(**vec_kw, max_features=3_000)
        self.full_vec = TfidfVectorizer(**vec_kw, max_features=15_000)

        self.ing_mat  = self.ing_vec.fit_transform(ing_corpus)
        self.tag_mat  = self.tag_vec.fit_transform(tag_corpus)
        self.flv_mat  = self.flv_vec.fit_transform(flavor_corpus)
        self.full_mat = self.full_vec.fit_transform(full_corpus)

        # BM25 on ingredient corpus
        self.bm25 = BM25(ing_corpus)

        # Keep ing_corpus for MMR
        self._ing_corpus = ing_corpus

        n = len(self.recipes)
        v = len(self.full_vec.vocabulary_)
        print(
            f"✅ RAG Engine v2 ready — {n} recipes | vocab {v} | "
            f"BM25 + multi-field TF-IDF + MMR | "
            f"{len(SYNONYMS)} synonym groups | "
            f"{len(CUISINE_HINTS)} cuisine detectors"
        )

    # ── Query helpers ─────────────────────────────────────────────────────────
    def _normalise(self, ingredient: str) -> str:
        s = ingredient.lower().strip()
        return NORMALIZATIONS.get(s, s)

    def _expand_query(self, ingredients: list[str]) -> str:
        """
        Expand query with:
          - Normalised forms
          - Synonym expansions
          - Flavor word → ingredient mappings
        """
        expanded: set[str] = set()
        for ing in ingredients:
            raw  = ing.lower().strip()
            norm = self._normalise(raw)
            expanded.add(raw)
            expanded.add(norm)
            # Synonyms
            for syn in SYNONYMS.get(norm, []) + SYNONYMS.get(raw, []):
                expanded.add(syn)
            # Flavor words
            for flavor_word, ing_hints in FLAVOR_TO_INGREDIENTS.items():
                if flavor_word in raw:
                    expanded.update(ing_hints)
        return " ".join(expanded)

    def _detect_cuisine(self, ingredients: list[str]) -> dict[str, int]:
        """Return a score dict mapping cuisine → number of hint matches."""
        ing_set = {i.lower() for i in ingredients}
        scores: dict[str, int] = {}
        for cuisine, hints in CUISINE_HINTS.items():
            hit = sum(
                1 for h in hints
                if any(h in i or i in h for i in ing_set)
            )
            if hit > 0:
                scores[cuisine] = hit
        return scores

    # ── MMR re-ranking ────────────────────────────────────────────────────────
    def _mmr_rerank(
        self,
        candidates: list[dict],
        lambda_param: float = 0.65,
        k: int = 20,
    ) -> list[dict]:
        """
        Maximal Marginal Relevance.
        score_MMR(d) = λ * relevance(d) − (1−λ) * max_sim(d, already_selected)
        λ=1 → pure relevance; λ=0 → pure diversity.
        Default λ=0.65 balances both.
        """
        if len(candidates) <= 1:
            return candidates[:k]

        # Build a small TF-IDF matrix from candidate ingredient strings
        texts = [" ".join(c.get("ingredients", [])).lower() for c in candidates]
        try:
            tmp_vec = TfidfVectorizer(ngram_range=(1, 1), min_df=1)
            mat = tmp_vec.fit_transform(texts)
        except Exception:
            return candidates[:k]

        selected: list[int] = []
        remaining = list(range(len(candidates)))

        while remaining and len(selected) < k:
            if not selected:
                best = max(remaining, key=lambda i: candidates[i].get("hybrid_score", 0))
            else:
                sel_mat = mat[selected]
                best, best_mmr = None, -1e9
                for i in remaining:
                    rel = candidates[i].get("hybrid_score", 0)
                    div = float(cosine_similarity(mat[i], sel_mat).max())
                    mmr = lambda_param * rel - (1 - lambda_param) * div
                    if mmr > best_mmr:
                        best_mmr, best = mmr, i

            selected.append(best)
            remaining.remove(best)

        return [candidates[i] for i in selected]

    # ── Coverage metrics ──────────────────────────────────────────────────────
    def _coverage(self, user_ings: list[str], recipe: dict) -> dict:
        """
        Compute ingredient coverage metrics for retrieval explanation.
        Returns: {matched, total_user, total_recipe, precision, recall}
        """
        u_set = {self._normalise(i) for i in user_ings}
        r_set = {self._normalise(i) for i in recipe.get("ingredients", [])}

        matched_u = {u for u in u_set if any(u in r or r in u for r in r_set)}
        matched_r = {r for r in r_set if any(u in r or r in u for u in u_set)}

        recall    = len(matched_u) / max(len(u_set), 1)
        precision = len(matched_r) / max(len(r_set), 1)
        return {
            "matched_user_ingredients":   sorted(matched_u),
            "matched_recipe_ingredients": sorted(matched_r),
            "user_ingredient_recall":     round(recall, 3),
            "recipe_ingredient_precision": round(precision, 3),
        }

    # ── Main retrieval ────────────────────────────────────────────────────────
    def retrieve(
        self,
        user_ingredients: list[str],
        k: int = 10,
        cuisine_filter: str | None = None,
        difficulty_filter: str | None = None,
        max_time: int | None = None,
        use_mmr: bool = True,
        mmr_lambda: float = 0.65,
    ) -> list[dict]:
        """
        Full hybrid retrieval pipeline:
          query → normalise → expand → multi-field scoring →
          BM25 → exact bonus → cuisine boost → hybrid merge → MMR
        """
        # ── Pre-process query ────────────────────────────────────────────────
        normalised       = [self._normalise(i) for i in user_ingredients]
        expanded_query   = self._expand_query(user_ingredients)
        cuisine_scores   = self._detect_cuisine(user_ingredients)
        detected_cuisine = max(cuisine_scores, key=cuisine_scores.get) if cuisine_scores else None

        # ── TF-IDF similarity across fields ──────────────────────────────────
        q_ing  = self.ing_vec.transform([expanded_query])
        q_full = self.full_vec.transform([expanded_query])
        q_tag  = self.tag_vec.transform([" ".join(normalised)])
        q_flv  = self.flv_vec.transform([" ".join(normalised)])

        ing_sim  = cosine_similarity(q_ing,  self.ing_mat)[0]
        full_sim = cosine_similarity(q_full, self.full_mat)[0]
        tag_sim  = cosine_similarity(q_tag,  self.tag_mat)[0]
        flv_sim  = cosine_similarity(q_flv,  self.flv_mat)[0]

        # ── BM25 (normalised to [0, 1]) ───────────────────────────────────────
        bm25_raw  = self.bm25.get_scores(expanded_query)
        bm25_max  = bm25_raw.max() if bm25_raw.max() > 0 else 1.0
        bm25_norm = bm25_raw / bm25_max

        # ── Exact & partial match bonus ───────────────────────────────────────
        user_set    = set(normalised)
        exact_bonus = np.zeros(len(self.recipes))
        for idx, recipe in enumerate(self.recipes):
            rec_norm  = {self._normalise(i) for i in recipe.get("ingredients", [])}
            exact_cnt = len(user_set & rec_norm)
            partial_cnt = sum(
                1 for u in user_set for r in rec_norm
                if (u in r or r in u) and u != r and len(u) > 2
            )
            exact_bonus[idx] = exact_cnt * 0.06 + partial_cnt * 0.02

        # ── Cuisine boost ─────────────────────────────────────────────────────
        cuisine_boost = np.zeros(len(self.recipes))
        if cuisine_scores:
            max_hint = max(cuisine_scores.values())
            for idx, recipe in enumerate(self.recipes):
                c = recipe.get("cuisine", "")
                if c in cuisine_scores:
                    cuisine_boost[idx] = 0.06 * (cuisine_scores[c] / max_hint)

        # ── Hybrid score ──────────────────────────────────────────────────────
        # Weights:  ing_tfidf(0.35) + bm25(0.30) + full_tfidf(0.15) +
        #           tag_sim(0.10) + flavor_sim(0.05) + exact_bonus + cuisine_boost
        hybrid = (
            0.35 * ing_sim  +
            0.30 * bm25_norm +
            0.15 * full_sim  +
            0.10 * tag_sim   +
            0.05 * flv_sim   +
            exact_bonus      +
            cuisine_boost
        )

        # ── Collect candidate pool (3× k for MMR) ────────────────────────────
        STRIP = ("Fiery ", "Quick ", "Plant-Based ", "Light & Healthy ")
        seen_base, candidates = set(), []

        for idx in np.argsort(hybrid)[::-1]:
            recipe = self.recipes[idx]

            # Deduplicate recipe variants
            base = recipe["title"]
            for p in STRIP:
                if base.startswith(p):
                    base = base[len(p):]
                    break
            if base in seen_base:
                continue
            seen_base.add(base)

            # Apply filters
            if cuisine_filter and cuisine_filter not in ("Any", "Orice"):
                if recipe.get("cuisine") != cuisine_filter:
                    continue
            if difficulty_filter and difficulty_filter not in ("Any", "Orice"):
                if recipe.get("difficulty") != difficulty_filter:
                    continue
            if max_time and recipe.get("time_minutes", 9999) > max_time:
                continue

            # Coverage metrics
            cov = self._coverage(user_ingredients, recipe)

            candidates.append({
                **recipe,
                # ── RAG debug scores ──
                "hybrid_score":    round(float(hybrid[idx]), 4),
                "bm25_score":      round(float(bm25_norm[idx]), 4),
                "tfidf_ing_score": round(float(ing_sim[idx]), 4),
                "tfidf_full_score": round(float(full_sim[idx]), 4),
                "tag_score":       round(float(tag_sim[idx]), 4),
                "flavor_score":    round(float(flv_sim[idx]), 4),
                "exact_bonus":     round(float(exact_bonus[idx]), 4),
                "cuisine_boost":   round(float(cuisine_boost[idx]), 4),
                # ── Query context ──
                "detected_cuisine":    detected_cuisine,
                "cuisine_hints_found": cuisine_scores,
                "expanded_terms":      expanded_query.split()[:15],
                "normalised_query":    normalised,
                # ── Coverage ──
                **cov,
            })

            if len(candidates) >= k * 3:
                break

        if not candidates:
            return []

        # ── MMR diversity re-ranking ──────────────────────────────────────────
        if use_mmr and len(candidates) > 1:
            candidates = self._mmr_rerank(candidates, lambda_param=mmr_lambda, k=k)
        else:
            candidates = candidates[:k]

        return candidates

    # ── Utility endpoints ─────────────────────────────────────────────────────
    def find_similar(self, recipe_title: str, k: int = 5) -> list[dict]:
        """Find recipes similar to a given one (by ingredient overlap)."""
        target = next(
            (r for r in self.recipes
             if r.get("title", "").lower() == recipe_title.lower()),
            None,
        )
        if not target:
            # Try partial match
            target = next(
                (r for r in self.recipes
                 if recipe_title.lower() in r.get("title", "").lower()),
                None,
            )
        if not target:
            return []
        results = self.retrieve(target.get("ingredients", []), k=k + 1)
        return [r for r in results if r.get("title") != target.get("title")][:k]

    def explain_idf(self, ingredients: list[str]) -> list[dict]:
        """
        Return the IDF weight of each ingredient term in the TF-IDF vocabulary.
        High IDF → rare / distinctive ingredient.
        Low IDF  → common ingredient (appears in many recipes).
        """
        explanations = []
        vocab = self.ing_vec.vocabulary_
        idf   = self.ing_vec.idf_

        for ing in ingredients:
            norm = self._normalise(ing)
            term_idf = None
            for term in [norm, ing.lower()]:
                if term in vocab:
                    term_idf = round(float(idf[vocab[term]]), 3)
                    break
            explanations.append({
                "ingredient":    ing,
                "normalised":    norm,
                "idf_weight":    term_idf,
                "distinctiveness": (
                    "very distinctive" if term_idf and term_idf > 4
                    else "distinctive" if term_idf and term_idf > 3
                    else "common" if term_idf and term_idf > 2
                    else "very common" if term_idf
                    else "not in vocabulary"
                ),
                "synonyms_used": SYNONYMS.get(norm, [])[:4],
            })
        return explanations

    def get_stats(self) -> dict:
        cuisines = set(r.get("cuisine", "") for r in self.recipes)
        avg_ing  = round(
            sum(len(r.get("ingredients", [])) for r in self.recipes) / max(len(self.recipes), 1),
            1,
        )
        return {
            "total_recipes":     len(self.recipes),
            "cuisines":          len(cuisines),
            "avg_ingredients":   avg_ing,
            "index_type":        "Hybrid BM25 + Multi-field TF-IDF + MMR",
            "vocabulary_size":   len(self.full_vec.vocabulary_),
            "synonym_groups":    len(SYNONYMS),
            "cuisine_detectors": len(CUISINE_HINTS),
            "bm25_k1":           self.bm25.k1,
            "bm25_b":            self.bm25.b,
            "mmr_lambda":        0.65,
        }
