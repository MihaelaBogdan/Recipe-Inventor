"""
data_loader.py
--------------
Loads all recipes and prepares them for indexing.
"""

import sys, os
import json

def load_recipes():
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "real_recipes.json")
    if not os.path.exists(data_path):
        print(f"Warning: {data_path} not found. Returning empty list.")
        return []
        
    with open(data_path, "r", encoding="utf-8") as f:
        recipes = json.load(f)
        
    for r in recipes:
        # Ensure ingredient_string field exists (used by TF-IDF)
        r.setdefault("ingredient_string", " ".join(r.get("ingredients", [])).lower())
        # Ensure all fields exist with defaults
        r.setdefault("description", "A delicious recipe.")
        r.setdefault("tags", [])
        r.setdefault("flavor_profile", [])
        r.setdefault("difficulty", "Medium")
        r.setdefault("time_minutes", 30)
        r.setdefault("servings", 4)
        r.setdefault("key_technique", "")
        r.setdefault("protein_type", "")
        r.setdefault("cuisine", "Global")
    return recipes

def get_unique_cuisines(recipes):
    return sorted(set(r.get("cuisine", "") for r in recipes if r.get("cuisine")))

def get_unique_difficulties(recipes):
    order = {"Easy": 0, "Medium": 1, "Hard": 2}
    all_diffs = set(r.get("difficulty", "") for r in recipes if r.get("difficulty"))
    return sorted(all_diffs, key=lambda d: order.get(d, 99))
