import json
import os
import ast
from datasets import load_dataset

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

            recipe = {
                "id": i + 1,
                "title": row.get('title', f"Recipe {i}").title(),
                "ingredients": ingredients,
                "steps": steps,
                "cuisine": row.get('category', 'Global').title(),
                "difficulty": "Medium",
                "time_minutes": 30,
                "tags": [row.get('category', '').lower(), "homemade"]
            }
            real_recipes.append(recipe)

        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(data_dir, exist_ok=True)
        
        out_path = os.path.join(data_dir, "real_recipes.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(real_recipes, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Successfully downloaded {len(real_recipes)} recipes to {out_path}!")
        
    except Exception as e:
        print(f"Error downloading dataset: {e}")

if __name__ == "__main__":
    main()
