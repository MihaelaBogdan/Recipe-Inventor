import json
import os
import ast
from datasets import load_dataset
 
 
# ─────────────────────────────────────────────────────────────────────────────
# CUISINE INFERENCE
# ─────────────────────────────────────────────────────────────────────────────
CUISINE_KEYWORDS: dict[str, list[str]] = {
    "Italian": ["pasta", "pizza", "risotto", "parmesan", "mozzarella", "basil", "marinara",
                "lasagna", "carbonara", "tiramisu", "prosciutto", "pecorino", "gnocchi",
                "pesto", "focaccia", "ravioli", "fettuccine", "ricotta", "pancetta"],
    "Mexican": ["taco", "burrito", "salsa", "tortilla", "jalapeño", "guacamole", "enchilada",
                "chorizo", "cumin", "cilantro", "chipotle", "quesadilla", "avocado",
                "lime", "poblano", "cotija", "tomatillo"],
    "Indian": ["curry", "masala", "turmeric", "garam", "tikka", "dal", "naan", "ghee",
               "cardamom", "coriander", "paneer", "biryani", "chutney", "samosa",
               "tandoori", "saffron", "fenugreek", "mustard seed"],
    "Chinese": ["soy sauce", "ginger", "sesame", "wok", "fried rice", "hoisin",
                "five spice", "dumpling", "tofu", "bok choy", "oyster sauce",
                "szechuan", "scallion", "rice vinegar", "star anise"],
    "Japanese": ["sushi", "miso", "ramen", "teriyaki", "sake", "dashi", "wasabi",
                 "edamame", "tempura", "udon", "mirin", "kombu", "nori", "tofu",
                 "panko", "matcha", "tonkatsu"],
    "Thai": ["coconut milk", "lemongrass", "fish sauce", "pad thai", "galangal",
             "kaffir", "sriracha", "tamarind", "thai basil", "nam pla", "curry paste"],
    "French": ["dijon", "crème", "ratatouille", "gruyere", "thyme", "bay leaf",
               "beurre blanc", "béarnaise", "coq au vin", "bouillabaisse", "brioche",
               "herbes de provence", "shallot", "cognac"],
    "Mediterranean": ["feta", "hummus", "tahini", "chickpea", "eggplant", "couscous",
                      "harissa", "preserved lemon", "za'atar", "sumac", "pita"],
    "Korean": ["kimchi", "gochujang", "sesame oil", "bulgogi", "doenjang", "bibimbap",
               "gochugaru", "perilla", "doenjang", "japchae", "tteok"],
    "American": ["bbq", "burger", "mac and cheese", "cornbread", "biscuit", "bacon",
                 "ranch", "buffalo", "pulled pork", "coleslaw", "brisket", "chili",
                 "macaroni", "cheddar", "hot dog"],
    "Greek": ["feta", "tzatziki", "gyro", "spanakopita", "kalamata", "oregano",
              "pita", "moussaka", "souvlaki", "dolma"],
    "Spanish": ["paella", "chorizo", "saffron", "paprika", "manchego", "gazpacho",
                "albondigas", "patatas bravas", "jamón", "sofrito"],
    "Middle Eastern": ["tahini", "za'atar", "sumac", "shawarma", "falafel", "hummus",
                       "pomegranate", "rose water", "baharat", "harissa", "couscous"],
    "Vietnamese": ["pho", "banh mi", "fish sauce", "rice noodle", "lemongrass",
                   "vietnamese", "nuoc cham", "spring roll", "hoisin"],
}
 
 
def infer_cuisine(title: str, ingredients: list[str]) -> str:
    text = (title + " " + " ".join(ingredients)).lower()
    scores: dict[str, int] = {}
    for cuisine, keywords in CUISINE_KEYWORDS.items():
        scores[cuisine] = sum(1 for kw in keywords if kw in text)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Global"
 
 
# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("Downloading recipe dataset from HuggingFace (Shengtao/recipe)...")
    try:
        dataset = load_dataset("Shengtao/recipe", split="train")
        recipes_to_take = 500
        real_recipes = []
 
        for i, row in enumerate(dataset):
            if i >= recipes_to_take:
                break
 
            # Parse ingredients
            raw_ing = row.get('ingredients', '')
            ingredients = [x.strip() for x in raw_ing.split(';')] if raw_ing else []
 
            # Parse instructions
            raw_inst = row.get('instructions_list', '[]')
            try:
                steps = ast.literal_eval(raw_inst)
            except:
                steps = [row.get('directions', '')]
 
            if not ingredients or not steps:
                continue
 
            cuisine = infer_cuisine(row.get('title', ''), ingredients)
 
            recipe = {
                "id": i + 1,
                "title": row.get('title', f"Recipe {i}").title(),
                "ingredients": ingredients,
                "steps": steps,
                "cuisine": cuisine,
                "difficulty": "Medium",
                "time_minutes": 30,
                "tags": [cuisine.lower(), row.get('category', '').lower(), "homemade"],
            }
            real_recipes.append(recipe)
 
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(data_dir, exist_ok=True)
 
        out_path = os.path.join(data_dir, "real_recipes.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(real_recipes, f, indent=2, ensure_ascii=False)
 
        # Print cuisine distribution for verification
        from collections import Counter
        cuisines = Counter(r["cuisine"] for r in real_recipes)
        print(f"\n✅ Successfully downloaded {len(real_recipes)} recipes to {out_path}!")
        print("\nCuisine distribution:")
        for cuisine, count in cuisines.most_common():
            print(f"  {cuisine}: {count}")
 
    except Exception as e:
        print(f"Error downloading dataset: {e}")
 
 
if __name__ == "__main__":
    main()