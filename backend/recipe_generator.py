"""
recipe_generator.py
-------------------
Rule-based recipe invention engine.
Takes user ingredients + RAG-retrieved base recipes and generates new,
unique recipe proposals — no LLM required.

Strategy:
  1. Adapt ingredients: merge user's list with complementary ones from base
  2. Adapt steps: soft-substitute ingredient names where possible
  3. Generate a creative title using templates + adjective bank
  4. Generate a flavour explanation from ingredient category pairing rules
  5. Add cuisine-specific cooking tips
"""

import re

# ─────────────────────────────────────────────────────────────────────────────
ADJECTIVES = [
    "Golden", "Rustic", "Vibrant", "Smoky", "Crispy", "Silky", "Bold", "Zesty",
    "Aromatic", "Hearty", "Sun-Kissed", "Savory", "Fragrant", "Caramelized",
    "Charred", "Velvety", "Bright", "Robust", "Spiced", "Glazed", "Seared",
    "Braised", "Tangy", "Herb-Crusted", "Slow-Cooked", "Pan-Seared", "Roasted",
]

DISH_TYPES: dict[str, list[str]] = {
    "Italian":       ["Pasta", "Risotto", "Frittata", "Bruschetta", "Bake"],
    "Thai":          ["Stir-Fry", "Curry", "Noodle Bowl", "Larb Salad"],
    "Indian":        ["Curry", "Dal", "Masala Bowl", "Biryani"],
    "Chinese":       ["Stir-Fry", "Fried Rice", "Noodle Bowl", "Soup"],
    "Japanese":      ["Donburi", "Ramen Bowl", "Bento Bowl", "Teriyaki"],
    "Korean":        ["Bibimbap Bowl", "Stir-Fry", "Hot Pot", "Rice Bowl"],
    "Vietnamese":    ["Noodle Bowl", "Soup", "Rice Bowl"],
    "Mediterranean": ["Salad", "Bake", "Skillet", "Mezze Bowl"],
    "Mexican":       ["Tacos", "Bowl", "Quesadilla", "Enchiladas"],
    "American":      ["Casserole", "Skillet", "Chowder", "Hash"],
    "French":        ["Gratin", "Ragout", "Tart", "Bisque"],
    "Middle Eastern":["Bowl", "Platter", "Stew", "Mezze"],
    "International": ["Bowl", "Skillet", "One-Pan Dish", "Bake"],
}

# ─────────────────────────────────────────────────────────────────────────────
# Flavour pairing rules
# ─────────────────────────────────────────────────────────────────────────────
FLAVOR_CATEGORIES: dict[str, set] = {
    "proteins":   {"chicken", "beef", "pork", "lamb", "fish", "salmon", "tuna",
                   "shrimp", "eggs", "egg", "tofu", "paneer", "veal", "turkey",
                   "duck", "clams", "mussels"},
    "aromatics":  {"garlic", "onion", "shallot", "ginger", "leek", "lemongrass",
                   "galangal", "green onion", "scallion"},
    "acids":      {"lemon", "lime", "vinegar", "tomato", "tomatoes", "canned tomatoes",
                   "cherry tomatoes", "yogurt", "wine", "tamarind", "orange",
                   "orange juice", "sumac"},
    "fats":       {"olive oil", "butter", "cream", "coconut milk", "sesame oil",
                   "tahini", "lard", "heavy cream"},
    "herbs":      {"basil", "oregano", "thyme", "rosemary", "parsley", "cilantro",
                   "mint", "dill", "sage", "bay leaves", "Thai basil",
                   "kaffir lime leaves"},
    "spices":     {"cumin", "paprika", "smoked paprika", "turmeric", "cinnamon",
                   "chili", "red chili", "coriander", "garam masala",
                   "Szechuan pepper", "sumac", "allspice", "cayenne"},
    "starches":   {"pasta", "rice", "potato", "bread", "flour", "noodles", "quinoa",
                   "pita", "spaghetti", "penne", "fettuccine", "ramen noodles",
                   "rice noodles", "arborio rice", "macaroni", "couscous"},
    "vegetables": {"spinach", "kale", "zucchini", "eggplant", "bell peppers",
                   "carrot", "mushrooms", "cauliflower", "sweet potato", "chickpeas",
                   "peas", "broccoli", "celery", "cucumber"},
    "dairy":      {"cheese", "parmesan", "feta", "mozzarella", "cream cheese",
                   "gruyere", "cheddar", "halloumi", "sour cream",
                   "parmesan cheese", "feta cheese"},
    "sweet":      {"honey", "sugar", "brown sugar", "pineapple", "mirin",
                   "palm sugar", "maple syrup"},
}

PAIR_EXPLANATIONS: dict[tuple, str] = {
    ("proteins", "acids"):     "Acids like citrus or vinegar tenderise proteins through gentle denaturation while adding brightness that cuts through richness—the contrast creates a more complex, layered flavour.",
    ("proteins", "fats"):      "Fats carry fat-soluble aromatic compounds deep into protein fibres, enriching the texture and creating a satisfying mouthfeel that defines great comfort food.",
    ("aromatics", "fats"):     "Blooming aromatics in fat is culinary alchemy—heat liberates volatile aromatic compounds, creating a fragrant base that permeates every element of the dish.",
    ("herbs", "acids"):        "Fresh herbs and acid create a vibrant interplay: chlorophyll-rich greens are enhanced by acidity while herbs temper sharp edges, producing a bright, complex top note.",
    ("spices", "fats"):        "Fat-soluble spice compounds bloom in fat, amplifying their intensity and ensuring even, thorough distribution throughout the dish—this is the secret behind great curries.",
    ("dairy", "acids"):        "Dairy richness is perfectly balanced by acidity—the contrast prevents heaviness while adding a clean finish that defines cuisines from Italy to India.",
    ("starches", "fats"):      "Starches are remarkable flavour sponges that absorb surrounding fats and aromatics, providing textural contrast and acting as the cohesive backbone of any dish.",
    ("vegetables", "aromatics"): "Vegetables cooked with aromatics undergo transformation—Maillard reactions develop complex notes while aromatics infuse each piece with depth far beyond its natural flavour.",
    ("sweet", "acids"):        "Sweet-sour balance is the hallmark of sophisticated cooking from Asia to Latin America. This dynamic tension keeps every bite interesting and demands another forkful.",
    ("spices", "aromatics"):   "Layering spices with aromatics builds a complex flavoral architecture—the aromatic base amplifies spice compounds while adding moisture and pungency for extraordinary depth.",
    ("dairy", "herbs"):        "Creamy dairy mellows sharp herbs while herbs cut through richness. This balance—seen in tzatziki, raita, and sauce gribiche—appears across global cuisines for good reason.",
    ("proteins", "spices"):    "Spices penetrate proteins during cooking, creating layers of flavour that develop differently at each stage—marinade, sear, simmer—resulting in remarkable complexity.",
    ("vegetables", "acids"):   "Acid brightens vegetables, preserves their vibrant colour, and creates a contrast that highlights their natural sweetness—a splash of citrus can transform a simple dish.",
}

CUISINE_NOTES: dict[str, str] = {
    "Italian":       "Italian cuisine celebrates ingredient purity—each component shines individually while harmonising with the whole. Simplicity is sophistication.",
    "Thai":          "Thai cooking masters balance across five senses—sweet, sour, salty, bitter, and umami create dishes of remarkable complexity from humble ingredients.",
    "Indian":        "Indian cooking builds flavour through precise sequence—spices bloom in fat, aromatics soften, ground spices are fried to remove rawness. Each step is essential.",
    "Chinese":       "Chinese wok cooking harnesses extreme heat (wok hei) to create unique caramelised flavours that are impossible to achieve at lower temperatures.",
    "Japanese":      "Japanese cuisine values the inherent flavour of each ingredient (umami), using minimal seasoning and precise technique to let natural tastes shine.",
    "Korean":        "Korean cuisine excels at fermentation and bold seasoning—gochujang, doenjang, and sesame create deeply satisfying, complex flavours.",
    "Vietnamese":    "Vietnamese cooking is defined by the balance of fresh herbs, clear broths, and subtle seasoning—brightness over heaviness, always.",
    "Mediterranean": "Mediterranean cooking is built on olive oil, garlic, and fresh herbs—bright, health-conscious flavours reflecting sun-drenched coastal landscapes.",
    "Mexican":       "Mexican cuisine achieves depth through dried chilies, which develop complex smoky, fruity notes completely different from their fresh counterparts.",
    "French":        "French technique elevates simple ingredients—fond, reductions, and emulsifications create profound flavours from few components through precise method.",
    "Middle Eastern":"Middle Eastern cuisine balances warm spices with bright acids and fresh herbs, creating aromatic layers of extraordinary depth.",
    "American":      "American regional cooking celebrates bold, hearty flavours—slow cooking, smoking, and braising transform humble cuts into magnificent dishes.",
    "International": "This dish draws on global culinary wisdom—balancing flavours, textures, and cooking techniques from multiple traditions.",
}

COOKING_TIPS: dict[str, list[str]] = {
    "Italian":       ["Salt your pasta water until it tastes like the sea—under-seasoning is the most common pasta mistake.", "Reserve pasta water before draining; its starch binds sauces beautifully."],
    "Thai":          ["Prep everything before starting—stir-frying moves fast and waits for no one.", "Balance constantly: add a little fish sauce, lime, sugar, and chili to taste."],
    "Indian":        ["Fry spices until fragrant (blooming) to remove raw notes before adding liquids.", "Add yogurt or cream off heat to prevent curdling—patience pays off."],
    "Chinese":       ["A smoking-hot wok is non-negotiable—this creates the wok hei flavour.", "Cook in small batches; overcrowding drops temperature and you'll steam instead of fry."],
    "Japanese":      ["Quality ingredients matter above all—use the best you can find.", "Taste constantly and adjust with small amounts—precision is everything in Japanese cooking."],
    "Vietnamese":    ["Char your aromatics directly over a flame for deeper, more complex broth.", "Finish with a squeeze of lime and fresh herbs right before eating."],
    "Mediterranean": ["Use the best olive oil you can afford—it's often the star ingredient.", "Fresh herbs added at the end preserve aromatic oils and vibrant colour."],
    "French":        [],
    "Mexican":       [],
    "American":      [],
    "Korean":        [],
    "Middle Eastern":[],
    "International": [],
}


# ─────────────────────────────────────────────────────────────────────────────
def _categorize(ingredient: str) -> str:
    ing_lower = ingredient.lower().strip()
    for cat, items in FLAVOR_CATEGORIES.items():
        for item in items:
            if item in ing_lower or ing_lower in item:
                return cat
    return "vegetables"


def generate_explanation(user_ingredients: list[str]) -> str:
    cats = list(set(_categorize(i) for i in user_ingredients))
    explanations = []
    for i in range(len(cats)):
        for j in range(i + 1, len(cats)):
            pair = (cats[i], cats[j])
            if pair in PAIR_EXPLANATIONS:
                explanations.append(PAIR_EXPLANATIONS[pair])
            elif (pair[1], pair[0]) in PAIR_EXPLANATIONS:
                explanations.append(PAIR_EXPLANATIONS[(pair[1], pair[0])])

    if not explanations:
        explanations = [
            "These ingredients create a balanced profile through complementary textures and taste contrasts—a combination rooted in classic flavour pairing principles."
        ]

    main = [i.title() for i in user_ingredients[:3]]
    intro = f"Why {', '.join(main)} work beautifully together: "
    return intro + " ".join(explanations[:2])


def generate_title(user_ingredients: list[str], base_recipe: dict, idx: int = 0) -> str:
    adj      = ADJECTIVES[(idx * 7 + len(user_ingredients)) % len(ADJECTIVES)]
    cuisine  = base_recipe.get("cuisine", "International")
    options  = DISH_TYPES.get(cuisine, ["Dish", "Bowl", "Skillet"])
    dish     = options[idx % len(options)]
    main_ings = [i.title() for i in user_ingredients if len(i) > 2][:2]

    if len(main_ings) >= 2:
        return f"{adj} {main_ings[0]} & {main_ings[1]} {dish}"
    if len(main_ings) == 1:
        return f"{adj} {cuisine}-Style {main_ings[0]} {dish}"
    return f"{adj} {cuisine} {dish}"


def adapt_ingredients(user_ingredients: list[str], base_recipe: dict, max_total: int = 10) -> list[str]:
    """Merge user's ingredients with complementary ones from the base recipe."""
    user_set = {i.lower().strip() for i in user_ingredients}
    result   = list(user_ingredients)

    for ing in base_recipe.get("ingredients", []):
        if len(result) >= max_total:
            break
        ing_lower = ing.lower().strip()
        already   = any(u in ing_lower or ing_lower in u for u in user_set)
        if not already:
            result.append(ing)

    return result


def adapt_steps(base_steps: list[str], user_ingredients: list[str], base_recipe: dict) -> list[str]:
    """Soft-substitute base ingredient names with user's equivalents in step text."""
    base_ings   = base_recipe.get("ingredients", [])
    replacement = {}

    for i, b_ing in enumerate(base_ings[: len(user_ingredients)]):
        if i < len(user_ingredients):
            u_ing = user_ingredients[i]
            if b_ing.lower() != u_ing.lower() and len(b_ing) > 3:
                replacement[b_ing.lower()] = u_ing.lower()

    adapted = []
    for step in base_steps:
        s = step
        for base_term, user_term in replacement.items():
            s = re.sub(re.escape(base_term), user_term, s, flags=re.IGNORECASE)
        adapted.append(s)
    return adapted


def estimate_nutrition(ingredients: list[str]) -> dict:
    cal = 180
    protein = 6
    carbs = 12
    fat = 4
    
    for ing in ingredients:
        ing_l = ing.lower()
        if any(p in ing_l for p in ["chicken", "poultry", "breast", "thighs", "turkey", "duck"]):
            cal += 140
            protein += 22
            fat += 4
        elif any(b in ing_l for b in ["beef", "steak", "pork", "lamb", "veal", "meat", "bacon"]):
            cal += 220
            protein += 20
            fat += 14
        elif any(s in ing_l for s in ["salmon", "tuna", "fish", "shrimp", "prawn", "seafood", "mussels", "clams"]):
            cal += 110
            protein += 18
            fat += 4
        elif any(d in ing_l for d in ["cheese", "parmesan", "cheddar", "mozzarella", "cream", "butter", "ghee", "heavy cream"]):
            cal += 90
            protein += 4
            fat += 8
        elif any(s in ing_l for s in ["pasta", "rice", "noodle", "potato", "bread", "flour", "spaghetti", "penne", "macaroni", "couscous"]):
            cal += 150
            carbs += 30
            protein += 3
        elif any(v in ing_l for v in ["spinach", "broccoli", "carrot", "zucchini", "eggplant", "tomato", "onion", "garlic", "shallot", "pepper", "mushroom"]):
            cal += 20
            carbs += 3
            protein += 1
        elif "oil" in ing_l:
            cal += 80
            fat += 9
        elif "egg" in ing_l:
            cal += 70
            protein += 6
            fat += 5
        elif "tofu" in ing_l or "paneer" in ing_l:
            cal += 75
            protein += 8
            fat += 4
            
    return {
        "calories": cal,
        "protein": f"{protein}g",
        "carbs": f"{carbs}g",
        "fat": f"{fat}g"
    }


def calculate_flavor_profile(ingredients: list[str]) -> dict:
    sweet = 12
    sour = 10
    salty = 15
    spicy = 5
    creamy = 10
    umami = 15
    
    for ing in ingredients:
        ing_l = ing.lower()
        if any(x in ing_l for x in ["honey", "sugar", "brown sugar", "pineapple", "maple syrup", "mirin", "sweet", "apple", "carrot"]):
            sweet += 25
        if any(x in ing_l for x in ["lemon", "lime", "vinegar", "tomato", "cherry tomatoes", "yogurt", "wine", "tamarind", "orange"]):
            sour += 20
        if any(x in ing_l for x in ["soy sauce", "salt", "parmesan", "bacon", "cheese", "olives"]):
            salty += 22
        if any(x in ing_l for x in ["chili", "cayenne", "pepper", "ginger", "garlic", "spic", "szechuan"]):
            spicy += 25
        if any(x in ing_l for x in ["butter", "cream", "coconut milk", "oil", "cheese", "mozzarella", "ghee", "lard", "heavy cream"]):
            creamy += 25
        if any(x in ing_l for x in ["chicken", "beef", "pork", "fish", "salmon", "shrimp", "mushrooms", "tofu", "paneer", "msg", "soy sauce", "parmesan"]):
            umami += 30
            
    # Normalize to nice reasonable percentages
    total = sweet + sour + salty + spicy + creamy + umami
    if total > 0:
        return {
            "sweet": min(95, int((sweet / total) * 200) + 5),
            "sour": min(95, int((sour / total) * 200) + 5),
            "salty": min(95, int((salty / total) * 200) + 5),
            "spicy": min(95, int((spicy / total) * 250) + 2),
            "creamy": min(95, int((creamy / total) * 200) + 5),
            "umami": min(95, int((umami / total) * 200) + 8)
        }
    return {"sweet": 10, "sour": 10, "salty": 15, "spicy": 5, "creamy": 10, "umami": 15}


def get_plating_guide(cuisine: str) -> str:
    if cuisine == "Italian":
        return "Plated in a shallow rimmed bowl, topped with a cascade of freshly shaved Parmigiano-Reggiano, finished with a precise thread of cold-pressed olive oil and a sprig of fresh basil."
    elif cuisine in ["Thai", "Chinese", "Vietnamese", "Japanese", "Korean"]:
        return "Served in a deep stoneware bowl, ingredients arranged in clean sections over the base, garnished with toasted sesame seeds, finely sliced scallions, and a drizzle of toasted chili oil."
    elif cuisine == "Indian":
        return "Presented in a warm copper handi or deep bowl, finished with a spiral of fresh cream, fresh coriander leaves, and served with charred naan placed diagonally on the side."
    elif cuisine == "Mexican":
        return "Arranged neatly on a rustic wooden board, garnished with fresh cilantro leaves, crumbled cotija cheese, and served with charred lime halves for squeezing."
    elif cuisine == "French":
        return "Artfully centered on a wide white plate, finished with a glossy reduction sauce spooned in a crescent shape, and garnished with delicate fresh chervil or microgreens."
    else:
        return "Presented in a hot cast-iron skillet or shallow ceramic dish, garnished with fresh chopped herbs and a splash of citrus to brighten the presentation."


def get_beverage_pairing(cuisine: str, ingredients: list[str]) -> str:
    ings_flat = " ".join(ingredients).lower()
    is_beef = any(b in ings_flat for b in ["beef", "steak", "lamb", "pork", "meat", "bacon"])
    is_seafood = any(s in ings_flat for s in ["salmon", "fish", "tuna", "shrimp", "prawn", "mussel", "clam", "seafood"])
    is_chicken = any(c in ings_flat for c in ["chicken", "poultry", "turkey", "duck"])
    
    if is_beef:
        return " Bold Cabernet Sauvignon or a smoky Syrah (cuts through rich fats and complements savory proteins)."
    elif is_seafood:
        return " Crisp Sauvignon Blanc or dry Pinot Grigio (bright acidity enhances delicate seafood flavors)."
    elif is_chicken:
        return " Light Pinot Noir or lightly oaked Chardonnay (balances white meat nicely)."
    elif cuisine in ["Thai", "Indian", "Mexican"] or "chili" in ings_flat:
        return " Chilled off-dry Riesling or a refreshing lager beer (cools down the heat and complements sweet-sour notes)."
    else:
        return " Dry Rosé or sparkling Prosecco (a versatile, refreshing match for vegetable or starch-heavy dishes)."


def invent_recipes(
    user_ingredients: list[str],
    retrieved_recipes: list[dict],
    num_recipes: int = 5,
) -> list[dict]:
    """
    Invent `num_recipes` new recipes from user ingredients + retrieved base recipes.
    Returns a list of invented recipe dicts.
    """
    results = []

    for idx, base in enumerate(retrieved_recipes[: num_recipes + 3]):
        if len(results) >= num_recipes:
            break

        merged  = adapt_ingredients(user_ingredients, base)
        steps   = adapt_steps(base.get("steps", []), user_ingredients, base)
        title   = generate_title(user_ingredients, base, idx)
        explain = generate_explanation(user_ingredients)
        cuisine = base.get("cuisine", "International")

        results.append({
            "title":         title,
            "cuisine":       cuisine,
            "difficulty":    base.get("difficulty", "Medium"),
            "time_minutes":  base.get("time_minutes", 30),
            "servings":      base.get("servings", 4),
            "ingredients":   merged,
            "steps":         steps,
            "explanation":   explain,
            "cuisine_note":  CUISINE_NOTES.get(cuisine, ""),
            "inspired_by":   base.get("title", ""),
            "tags":          base.get("tags", []),
            "flavor_profile": base.get("flavor_profile", []),
            "tips":          COOKING_TIPS.get(cuisine, COOKING_TIPS["International"])[:2],
            "key_technique": base.get("key_technique", ""),
            "score":         base.get("score", 0.0),
            "nutrition":     estimate_nutrition(merged),
            "flavor_percentages": calculate_flavor_profile(merged),
            "plating_guide": get_plating_guide(cuisine),
            "beverage_pairing": get_beverage_pairing(cuisine, merged),
        })

    return results

