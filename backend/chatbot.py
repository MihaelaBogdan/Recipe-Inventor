"""
chatbot.py — RAG Chatbot without LLM
====================================
Operates EXCLUSIVELY through:
  1. Intent detection: semantic similarity + regex patterns
  2. Entity extraction: ingredients, cuisines, techniques from messages
  3. RAG retrieval: TF-IDF + BM25 for recipe matching
  4. Response formatting via templates and localized knowledge bases
"""
 
import re
import random
import numpy as np
from intent_examples import INTENT_EXAMPLES
 
 
# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE BASE: Culinary Techniques
# ─────────────────────────────────────────────────────────────────────────────
TECHNIQUES: dict[str, dict] = {
    "braising": {
        "ro": "braising", "emoji": "🍲",
        "explanation": (
            "Braising is a slow, two-step cooking technique: "
            "first ingredients are seared at high heat to develop "
            "a caramelized crust (Maillard reaction), then cooked slowly in a "
            "covered liquid (wine, broth, water) at a low temperature, 150-165°C, for 1-3 hours. "
            "Collagen in meat melts into gelatin, creating rich, silky sauces. "
            "Classic examples: Beef Bourguignon, Osso Buco, Coq au Vin."
        ),
        "keywords": ["braising", "braised", "slow cook", "slow cooked", "braise"],
    },
    "sauteing": {
        "ro": "sauteing", "emoji": "🍳",
        "explanation": (
            "Sautéing cooks ingredients quickly in a small amount of fat over high heat, "
            "constantly shaking or tossing the pan. The goal is surface caramelization "
            "without overcooking the interior. The word comes from the French 'sauter' "
            "(to jump) — the continuous motion prevents burning. Crucial for vegetables, mushrooms, "
            "and finely cut meat. The pan must be hot before adding ingredients."
        ),
        "keywords": ["saute", "sautéing", "sauté", "pan fry", "pan fried"],
    },
    "wok hei": {
        "ro": "wok hei", "emoji": "🔥",
        "explanation": (
            "Wok hei (镬气, 'breath of the wok') is the smoky, slightly charred, and "
            "intense flavor that food cooked in an extremely hot wok acquires. "
            "It is produced by the rapid volatilization of moisture, Maillard reactions at 300°C+, "
            "and caramelization of natural sugars. The secret: the wok must be red-hot, "
            "and the food cooked in small batches. Any cooling of the wok turns the stir-fry "
            "into boiling — the most common stir-frying mistake."
        ),
        "keywords": ["wok hei", "wok", "stir fry", "stir-fry", "chinese pan"],
    },
    "emulsification": {
        "ro": "emulsification", "emoji": "🥣",
        "explanation": (
            "Emulsification combines two liquids that normally do not mix (fat + water) "
            "through an emulsifying agent (lecithin from egg yolk, mustard, miso). "
            "Carbonara: pasta water starch + egg yolk creates a creamy sauce without cream. "
            "Mayonnaise: oil + yolk + acid. Caesar dressing: oil + lemon + mustard + anchovy. "
            "The key: controlled temperature and constant agitation."
        ),
        "keywords": ["emulsification", "emulsify", "emulsified", "creamy without cream"],
    },
    "blanching": {
        "ro": "blanching", "emoji": "🥦",
        "explanation": (
            "Blanching partially cooks vegetables in salted boiling water (30 sec – 3 min), "
            "followed immediately by cooling in ice water to stop cooking. "
            "Effects: preserves vibrant color (chlorophyll remains stable), "
            "texture remains crisp, bitterness is removed, and oxidative enzymes are destroyed. "
            "Essential for spinach in Palak Paneer, green beans in salads, and broccoli before freezing."
        ),
        "keywords": ["blanching", "blanch", "blanched", "boiling water ice"],
    },
    "reduction": {
        "ro": "reduction", "emoji": "⬇️",
        "explanation": (
            "Reduction concentrates flavors by evaporating liquid over medium-high heat, "
            "uncovered. As water evaporates, sugars, proteins, and flavor compounds "
            "concentrate, creating thicker and more intense sauces. "
            "Rule: reduce wine by half before adding broth. "
            "Teriyaki sauce, balsamic reduction, wine glaze — all use this technique. "
            "Do not rush the process with high heat: the risk of burning increases exponentially."
        ),
        "keywords": ["reduction", "reduce", "reduced", "thickened", "concentrated"],
    },
    "caramelization": {
        "ro": "caramelization", "emoji": "🧅",
        "explanation": (
            "Caramelization is the thermal oxidation of sugars at 160-180°C, producing "
            "hundreds of new flavor compounds with buttery, nutty, vanilla notes and complex bitterness. "
            "It differs from the Maillard reaction (which involves proteins + sugars). "
            "Caramelizing onions requires 45-60 minutes on low heat — any shortcut produces "
            "soft, sweaty onions, not caramelized ones. French onion soup demonstrates how "
            "transformative patience can be."
        ),
        "keywords": ["caramelization", "caramelize", "caramelized", "caramel", "burnt sugar", "caramelized onions"],
    },
    "maillard": {
        "ro": "Maillard reaction", "emoji": "🥩",
        "explanation": (
            "The Maillard reaction is a chemical reaction between amino acids and reducing sugars "
            "at 140-165°C, creating hundreds of flavor compounds that give the note of 'fried', "
            "brown crust, and complex savory flavors. It is responsible for: bread crust, "
            "the color of seared meat, the note of roasted coffee, and tempered chocolate. "
            "CRITICAL: the pan must be dry and the meat patted dry with a paper towel — moisture "
            "drops the temperature below 100°C and steams instead of searing."
        ),
        "keywords": ["maillard", "maillard reaction", "searing", "seared", "crust", "brown", "browning"],
    },
    "tempering": {
        "ro": "spice tempering", "emoji": "🌶️",
        "explanation": (
            "Tempering (tadka/tempering) is the Indian technique of blooming spices in hot fat "
            "(clarified butter, oil) to release fat-soluble flavor compounds. "
            "Cumin seeds 'pop' in 30 seconds — the signal they are ready. Then, the sizzling "
            "mixture is poured hot over the dish (dal, yogurt, soups). "
            "Order matters: whole seeds -> onions -> garlic -> ground spices. "
            "Ground spices are added last — they burn fastest."
        ),
        "keywords": ["tempering", "tadka", "spices in oil", "blooming", "bloom spices"],
    },
    "deglazing": {
        "ro": "deglazing", "emoji": "🍷",
        "explanation": (
            "Deglazing adds liquid (wine, broth, vinegar, citrus juice) into a hot pan "
            "after searing to dissolve the 'fond' — the caramelized residues stuck to the bottom. "
            "Fond contains intense flavors from Maillard reactions and is the basis of any good pan sauce. "
            "Never waste a pan with brown fond! When you add the liquid, sizzling and steam are normal — "
            "the temperature difference creates instant deglazing."
        ),
        "keywords": ["deglazing", "deglaze", "fond", "pan residues", "wine in pan"],
    },
    "confit": {
        "ro": "confit", "emoji": "🦆",
        "explanation": (
            "Confit cooks ingredients completely submerged in fat at a low temperature (70-90°C) "
            "for a long period. Duck confit cooks in its own fat for 3-4 hours — the result is "
            "incredibly tender meat falling off the bone. The technique originally appeared as "
            "a preservation method (before refrigeration). Potatoes confit in olive oil at 90°C = "
            "the creamiest potatoes possible. Garlic confit in oil = sweet, silky paste without raw garlic's sharpness."
        ),
        "keywords": ["confit", "fat", "submerged in oil", "duck confit", "garlic confit"],
    },
    "poaching": {
        "ro": "poaching", "emoji": "🥚",
        "explanation": (
            "Poaching cooks delicate foods (eggs, fish, chicken) in liquid at 71-82°C — "
            "below the boiling point. Tiny bubbles at the bottom indicate the correct temperature. "
            "Poached eggs: water with vinegar (reduces egg white spreading), whirlpool with a spoon, "
            "slide raw egg in for 3-4 minutes. Poached chicken in white wine with herbs: the moistest "
            "chicken breast possible. Poached salmon in vegetable broth: tender and flavorful."
        ),
        "keywords": ["poach", "poaching", "poached", "poached eggs"],
    },
}
 
# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE BASE: Ingredient Substitutions
# ─────────────────────────────────────────────────────────────────────────────
SUBSTITUTIONS: dict[str, dict] = {
    "eggs": {
        "ro": "eggs", "emoji": "🥚",
        "subs": [
            {"sub": "Flax egg", "ratio": "1 tbsp ground flaxseeds + 3 tbsp water = 1 egg", "best_for": "cakes, muffins, vegan burgers"},
            {"sub": "Chia egg", "ratio": "1 tbsp chia seeds + 3 tbsp water = 1 egg", "best_for": "dense cakes, bread"},
            {"sub": "Mashed banana", "ratio": "1/4 banana = 1 egg", "best_for": "muffins, pancakes — adds sweetness"},
            {"sub": "Aquafaba (chickpea water)", "ratio": "3 tbsp = 1 whole egg; 2 tbsp = 1 egg white", "best_for": "meringue, vegan mayonnaise, mousses"},
            {"sub": "Coconut milk or yogurt", "ratio": "1/4 cup = 1 egg", "best_for": "moist cakes"},
        ],
    },
    "butter": {
        "ro": "butter", "emoji": "🧈",
        "subs": [
            {"sub": "Coconut oil", "ratio": "1:1", "best_for": "cakes, cookies, sauces"},
            {"sub": "Olive oil", "ratio": "3/4 of the amount", "best_for": "savory dishes, sautéing"},
            {"sub": "Mashed avocado", "ratio": "1:1", "best_for": "dark baked goods (chocolate)"},
            {"sub": "Vegan butter", "ratio": "1:1", "best_for": "any butter recipe"},
            {"sub": "Ghee", "ratio": "1:1", "best_for": "high-heat cooking — higher smoke point"},
        ],
    },
    "milk": {
        "ro": "milk", "emoji": "🥛",
        "subs": [
            {"sub": "Oat milk", "ratio": "1:1", "best_for": "sauces, baking, drinks — most neutral flavor"},
            {"sub": "Almond milk", "ratio": "1:1", "best_for": "desserts, cereals"},
            {"sub": "Soy milk", "ratio": "1:1", "best_for": "anything — protein content similar to dairy milk"},
            {"sub": "Coconut milk (canned)", "ratio": "1:1", "best_for": "curries, creamy sauces"},
            {"sub": "Water + 1 tbsp butter/oil", "ratio": "1:1", "best_for": "emergency in savory recipes"},
        ],
    },
    "cream": {
        "ro": "cream", "emoji": "🥛",
        "subs": [
            {"sub": "Full-fat coconut milk (canned)", "ratio": "1:1", "best_for": "curries, soups, desserts"},
            {"sub": "Cashew cream (soaked cashews blended)", "ratio": "1:1", "best_for": "pasta, sauces, desserts"},
            {"sub": "Greek yogurt", "ratio": "1:1, added off-heat", "best_for": "sauces — do not boil, it curdles"},
            {"sub": "Blended silken tofu", "ratio": "1:1", "best_for": "creamy soups, cheesecakes"},
        ],
    },
    "parmesan": {
        "ro": "parmesan", "emoji": "🧀",
        "subs": [
            {"sub": "Nutritional yeast", "ratio": "3-4 tbsp per 100g parmesan", "best_for": "pasta, risotto, popcorn — similar umami taste"},
            {"sub": "Pecorino Romano", "ratio": "1:1", "best_for": "saltier — reduce added salt in recipe"},
            {"sub": "Grana Padano", "ratio": "1:1", "best_for": "milder, budget alternative"},
            {"sub": "Almonds + nutritional yeast + salt", "ratio": "blend 100g almonds + 4 tbsp yeast + 1 tsp salt", "best_for": "vegan topping for pasta/salads"},
        ],
    },
    "flour": {
        "ro": "all-purpose flour", "emoji": "🌾",
        "subs": [
            {"sub": "Almond flour", "ratio": "1:1 in most cases", "best_for": "moist cakes, gluten-free"},
            {"sub": "Oat flour (blended oats)", "ratio": "1:1", "best_for": "cakes, cookies, pancakes"},
            {"sub": "Rice flour", "ratio": "1:1", "best_for": "light batters, gluten-free"},
            {"sub": "Cornstarch (thickening)", "ratio": "1 tbsp cornstarch = 2 tbsp flour", "best_for": "sauces, soups, not baking"},
        ],
    },
    "bacon": {
        "ro": "bacon", "emoji": "🥓",
        "subs": [
            {"sub": "Smoked tempeh (soy + liquid smoke)", "ratio": "1:1", "best_for": "closest in texture"},
            {"sub": "Dry-fried king oyster mushrooms", "ratio": "thinly sliced", "best_for": "similar crispy texture"},
            {"sub": "Toasted coconut chips + soy + liquid smoke", "ratio": "50g coconut chips", "best_for": "salads, vegan BLT"},
            {"sub": "Prosciutto / Pancetta", "ratio": "1:1", "best_for": "if not vegan — finer texture"},
        ],
    },
    "honey": {
        "ro": "honey", "emoji": "🍯",
        "subs": [
            {"sub": "Maple syrup", "ratio": "3/4 of the amount", "best_for": "almost identical in baking"},
            {"sub": "Agave syrup", "ratio": "3/4 of the amount", "best_for": "milder, dissolves easier"},
            {"sub": "Date syrup", "ratio": "1:1", "best_for": "smoothies, desserts with caramelized flavor"},
            {"sub": "Brown sugar + water", "ratio": "1 tbsp sugar + 1/4 tbsp water = 1 tbsp honey", "best_for": "emergency cooking"},
        ],
    },
    "wine": {
        "ro": "cooking wine", "emoji": "🍷",
        "subs": [
            {"sub": "Vegetable broth + 1 tbsp white wine vinegar", "ratio": "1:1", "best_for": "white wine in risotto, sauces"},
            {"sub": "White or red grape juice + vinegar", "ratio": "3/4 juice + 1/4 vinegar", "best_for": "fruity, for braising"},
            {"sub": "Water + 1-2 tbsp balsamic vinegar", "ratio": "1:1", "best_for": "red wine in sauces"},
            {"sub": "Apple juice", "ratio": "1:1", "best_for": "white wine in pork, chicken"},
        ],
    },
    "soy sauce": {
        "ro": "soy sauce", "emoji": "🧉",
        "subs": [
            {"sub": "Tamari (gluten-free)", "ratio": "1:1", "best_for": "identical, wheat-free"},
            {"sub": "Coconut aminos", "ratio": "1:1, sweeter", "best_for": "soy-free, paleo"},
            {"sub": "Worcestershire sauce", "ratio": "1:1", "best_for": "more complex, contains anchovies"},
            {"sub": "Miso + water", "ratio": "1 tbsp miso + 1 tbsp water = 2 tbsp soy sauce", "best_for": "deeper umami"},
        ],
    },
}
 
# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE BASE: General Cooking Tips
# ─────────────────────────────────────────────────────────────────────────────
COOKING_TIPS_GENERAL: list[dict] = [
    {"tip": "Salt pasta water until it tastes like the sea. Under-salting pasta is the most common kitchen mistake.", "emoji": "🧂"},
    {"tip": "Let meat come to room temperature for 30 minutes before cooking. You will get more even cooking.", "emoji": "🥩"},
    {"tip": "Do not crowd the pan! If you put too many ingredients, the temperature drops and it boils instead of frying.", "emoji": "🍳"},
    {"tip": "Always reserve pasta water before draining. The starch in it binds the sauce perfectly.", "emoji": "🍝"},
    {"tip": "Add spices in layers, not just at the end. Taste and adjust along the way.", "emoji": "🌶️"},
    {"tip": "A real cast iron skillet will be the best product in your kitchen. It lasts a lifetime.", "emoji": "🍳"},
    {"tip": "Acid (lemon, vinegar) added at the end brightens ANY dish. It's the secret magic of restaurants.", "emoji": "🍋"},
    {"tip": "Let meat rest after cooking: 5 min for chicken, 10 min for steak. Juices redistribute.", "emoji": "⏳"},
    {"tip": "Buy a good kitchen knife and sharpen it monthly. A good knife completely changes the cooking experience.", "emoji": "🔪"},
    {"tip": "Cooking a good risotto = 18 minutes of stirring + patience. There is no shortcut for this.", "emoji": "🍚"},
]
 
# ─────────────────────────────────────────────────────────────────────────────
# INTENT PATTERNS (English matching regexes)
# ─────────────────────────────────────────────────────────────────────────────
INTENT_PATTERNS: list[tuple] = [
    # find_recipe
    (r"(what can i|how to|what to) (make|cook|prepare|do).+with (.+)", "find_recipe"),
    (r"(i have|we have|using) (.+) (at home|in the fridge|in the kitchen|available)", "find_recipe"),
    (r"(ingredients?|recipe with|what to do with) (.+)", "find_recipe"),
    (r"recipe containing (.+)", "find_recipe"),

    # recipe_info
    (r"(how do i make|how to make|how to cook|how to prepare|recipe for|give me the recipe for) (.+)", "recipe_info"),
    (r"recipe of (.+)", "recipe_info"),
    (r"step by step (for|to make) (.+)", "recipe_info"),

    # technique_info
    (r"(what is|what does|explain|explain to me|how does) (.+?)( technique)?$", "technique_info"),
    (r"technique of (braising|sauteing|wok|confit|emulsification|maillard|blanching|reduction|caramelization|tempering|poaching|deglazing)", "technique_info"),

    # substitution
    (r"(substitute|replace|instead of|alternative for|alternative to|without|no) (.+)", "substitution"),
    (r"what can i use in place of (.+)", "substitution"),
    (r"(.+) substitute", "substitution"),

    # dietary filter
    (r"(vegan|vegetarian|gluten.?free|dairy.?free|plant.?based|keto|paleo) (recipes?|food|dish|something)?", "dietary_filter"),

    # time filter
    (r"(quick|fast|easy|simple) (recipes?|food|dish)? under (\d+)? ?(min|minutes|hours?)?", "time_filter"),
    (r"under (\d+) (minutes|min|hours?)", "time_filter"),

    # cuisine filter
    (r"(italian|thai|indian|japanese|chinese|mexican|french|korean|mediterranean) (food|recipes?|dishes|cuisine)?", "cuisine_filter"),

    # random
    (r"(surprise me|random|something random|choose for me|give me an idea|whatever)", "random_recipe"),

    # help
    (r"(help|commands|features|what can you do|how to use)", "help"),

    # chitchat
    (r"(hello|hi|hey|good morning|welcome)", "chitchat_greet"),
    (r"(thank you|thanks|great|awesome|perfect)", "chitchat_thanks"),
    (r"(who are you|what are you|your name|about you|are you a robot)", "chitchat_identity"),
    (r"(bye|goodbye|see you|see ya)", "chitchat_bye"),
]

# ─────────────────────────────────────────────────────────────────────────────
# CUISINE MAP
# ─────────────────────────────────────────────────────────────────────────────
CUISINE_MAP: dict[str, str] = {
    "italian": "Italian",
    "thai": "Thai",
    "indian": "Indian",
    "chinese": "Chinese",
    "japanese": "Japanese",
    "korean": "Korean",
    "mexican": "Mexican",
    "french": "French",
    "mediterranean": "Mediterranean",
    "vietnamese": "Vietnamese",
}

# Keep map just in case Romanian inputs are sent
RO_TO_EN: dict[str, str] = {
    "pui": "chicken", "gaina": "chicken", "puiului": "chicken",
    "usturoi": "garlic", "usturoiului": "garlic",
    "ceapa": "onion", "cepei": "onion",
    "cartof": "potato", "cartofi": "potato", "cartofii": "potato",
    "orez": "rice", "orezului": "rice",
    "paste": "pasta", "spaghete": "pasta", "macaroane": "pasta", "penne": "pasta",
    "spanac": "spinach", "spanacului": "spinach",
    "ciuperci": "mushroom", "ciuperca": "mushroom", "ciupercile": "mushroom",
    "ou": "egg", "oua": "egg", "ouale": "egg", "ouelor": "egg",
    "lapte": "milk", "laptelui": "milk",
    "unt": "butter", "untului": "butter",
    "rosie": "tomato", "rosii": "tomato", "rosiile": "tomato",
    "lamaie": "lemon", "lamai": "lemon", "lamaia": "lemon",
    "peste": "fish", "pestelui": "fish",
    "salata": "salad", "salate": "salad",
    "sare": "salt", "sarii": "salt",
    "piper": "pepper", "piperului": "pepper",
    "ulei": "oil", "uleiului": "oil",
    "carne": "meat", "carnii": "meat",
    "porc": "pork", "porcului": "pork",
    "vita": "beef", "vitei": "beef",
    "branza": "cheese", "cascaval": "cheese", "parmezan": "parmesan",
    "morcov": "carrot", "morcovi": "carrot", "morcovii": "carrot",
    "dovlecel": "zucchini", "dovlecei": "zucchini",
    "vanata": "eggplant", "vinete": "eggplant",
    "ardei": "pepper", "ardei gras": "bell pepper",
    "creveti": "shrimp",
    "iaurt": "yogurt", "iaurtului": "yogurt",
    "miere": "honey", "mierii": "honey",
    "zahar": "sugar", "zaharului": "sugar",
    "faina": "flour", "fainei": "flour",
    "vin": "wine", "vinului": "wine",
    "smantana": "cream", "smantanei": "cream",
    "mar": "apple", "mere": "apple", "merele": "apple",
    "paine": "bread", "panii": "bread",
    "naut": "chickpeas", "nautului": "chickpeas",
    "broccoli": "broccoli",
}


class RecipeChatbot:
    """
    RAG Chatbot with semantic intent detection.
    """

    def __init__(self, rag_engine, agent=None):
        self.rag = rag_engine
        self.agent = agent
        self.encoder = rag_engine.encoder

        # Index techniques semantically
        self._technique_keys = list(TECHNIQUES.keys())
        self._technique_texts = [
            f"{v['name']} {' '.join(v['keywords'])}"
            for v in TECHNIQUES.values()
        ]
        self._technique_matrix = self.encoder.encode(self._technique_texts)

        # Index substitutions semantically
        self._sub_keys = list(SUBSTITUTIONS.keys())
        self._sub_texts = [
            f"{v['name']} {k}"
            for k, v in SUBSTITUTIONS.items()
        ]
        self._sub_matrix = self.encoder.encode(self._sub_texts)

        # Index intents semantically
        self._intent_labels = []
        self._intent_vectors = []
        for intent, examples in INTENT_EXAMPLES.items():
            for emb in self.encoder.encode(examples):
                self._intent_labels.append(intent)
                self._intent_vectors.append(emb)
        self._intent_matrix = np.array(self._intent_vectors)

        print(f"Semantic intent + technique + substitution indexes ready.")

    # ── Cosine similarity helper ──────────────────────────────────────────────
    def _cosine_best(self, matrix, query_vec):
        import numpy as np
        norms = np.linalg.norm(matrix, axis=1)
        q_norm = np.linalg.norm(query_vec)
        if q_norm == 0:
            return 0, 0.0
        sims = matrix @ query_vec / (norms * q_norm + 1e-9)
        best = int(np.argmax(sims))
        return best, float(sims[best])

    # ── Detect intent ─────────────────────────────────────────────────────────
    def _detect_intent(self, message: str) -> tuple[str, None]:
        # Perform simple regex matching first for reliability
        msg_clean = message.lower().strip()
        for pattern, intent in INTENT_PATTERNS:
            if re.search(pattern, msg_clean):
                return intent, None

        # Fallback to semantic matching
        q = self.encoder.encode([message])[0]
        best_idx, best_score = self._cosine_best(self._intent_matrix, q)
        if best_score < 0.25:
            return "unknown", None
        return self._intent_labels[best_idx], None

    # ── Extract ingredients from message ──────────────────────────────────────
    def _extract_ingredients(self, message: str) -> list[str]:
        STOPWORDS = {
            "what", "can", "i", "we", "make", "cook", "prepare", "do", "with",
            "have", "at", "home", "in", "the", "fridge", "kitchen", "available",
            "some", "any", "recipe", "ingredients", "using", "and", "or", "for",
            "on", "to", "under", "minutes", "min", "quick", "easy", "simple",
            "fast", "get", "show", "give", "me", "how", "make"
        }
        clean = re.sub(r'[?!.,;:]', ' ', message.lower())
        tokens = [t.strip() for t in clean.split() if len(t.strip()) > 2]
        result = [t for t in tokens if t not in STOPWORDS]
        return result[:8]

    # ── Extract recipe name from message ──────────────────────────────────────
    def _extract_dish_name(self, message: str) -> str:
        patterns = [
            r"how do i make (.+?)[\?!.]?$",
            r"how to make (.+?)[\?!.]?$",
            r"how to cook (.+?)[\?!.]?$",
            r"how to prepare (.+?)[\?!.]?$",
            r"recipe for (.+?)[\?!.]?$",
            r"give me the recipe for (.+?)[\?!.]?$",
            r"recipe of (.+?)[\?!.]?$",
        ]
        for p in patterns:
            m = re.search(p, message.lower())
            if m:
                return m.group(1).strip()
        return ""

    # ── Extract technique from message ────────────────────────────────────────
    def _extract_technique(self, message: str) -> str | None:
        q = self.encoder.encode([message])[0]
        best_idx, best_score = self._cosine_best(self._technique_matrix, q)
        if best_score < 0.30:
            return None
        return self._technique_keys[best_idx]

    # ── Extract substitution target ───────────────────────────────────────────
    def _extract_sub_target(self, message: str) -> str | None:
        q = self.encoder.encode([message])[0]
        best_idx, best_score = self._cosine_best(self._sub_matrix, q)
        if best_score < 0.30:
            return None
        return self._sub_keys[best_idx]

    # ── Extract time limit ────────────────────────────────────────────────────
    def _extract_time(self, message: str) -> int | None:
        m = re.search(r'(\d+)\s*(min|minute|hour|hr)s?', message.lower())
        if m:
            val = int(m.group(1))
            unit = m.group(2)
            return val * 60 if 'hour' in unit or 'hr' in unit else val
        if 'quick' in message.lower() or 'fast' in message.lower() or 'repede' in message.lower():
            return 30
        return None

    # ── Build response ────────────────────────────────────────────────────────
    def respond(self, message: str) -> dict:
        intent, match = self._detect_intent(message)
        return self._build_response(intent, message)

    def _build_response(self, intent: str, message: str) -> dict:

        # ── Chitchat ─────────────────────────────────────────────────────────
        if intent == "chitchat_greet":
            return {
                "type": "text",
                "text": " Hi! I am **Chef Bot RAG** — your culinary AI assistant! "
                        "I can help you find recipes, explain cooking techniques, suggest ingredient substitutions, "
                        "and invent new recipes based on what you have in your kitchen. What are we cooking today?",
                "suggestions": ["What can I make with chicken and garlic?", "Explain what braising is", "Quick vegan recipes", "Surprise me!"],
            }

        if intent == "chitchat_thanks":
            responses = [
                " You're welcome! Do you have any other culinary questions?",
                " Glad I could help! Enjoy your meal!",
                " At your service! Tell me what else you're cooking!",
            ]
            return {"type": "text", "text": random.choice(responses), "suggestions": ["I want another recipe", "Explain another technique"]}

        if intent == "chitchat_identity":
            return {
                "type": "text",
                "text": " I am **Chef Bot RAG** — a culinary chatbot! "
                        "I operate using:\n"
                        "• **Semantic intent detection** with sentence-transformers\n"
                        "• **RAG retrieval** with hybrid ChromaDB + BM25 search\n"
                        "• **Knowledge bases** for culinary techniques and substitutions\n"
                        "• **Query expansion** with ingredient synonyms\n\n",
                "suggestions": ["How does RAG work?", "What recipes do you have?"],
            }

        if intent == "chitchat_bye":
            return {"type": "text", "text": " Goodbye! Happy cooking!", "suggestions": []}

        # ── Help ──────────────────────────────────────────────────────────────
        if intent == "help":
            return {
                "type": "help",
                "text": " **I can help you with:**",
                "capabilities": [
                    {"icon": "🔍", "title": "Find recipes by ingredients", "example": "What can I make with chicken, garlic, and lemon?"},
                    {"icon": "📖", "title": "Explain any recipe in the database", "example": "How to make carbonara?"},
                    {"icon": "🔥", "title": "Explain cooking techniques", "example": "What is the wok hei technique?"},
                    {"icon": "🔄", "title": "Suggest ingredient substitutions", "example": "What can I use instead of eggs?"},
                    {"icon": "⏱️", "title": "Filter by cuisine/diet/time", "example": "Vegan recipes under 30 minutes"},
                    {"icon": "🎲", "title": "Surprise you with a random recipe", "example": "Surprise me!"},
                    {"icon": "💡", "title": "Provide general cooking tips", "example": "Give me a cooking tip"},
                ],
            }

        # ── Find recipe by ingredients ────────────────────────────────────────
        if intent == "find_recipe":
            ings = self._extract_ingredients(message)
            if not ings:
                return {
                    "type": "text",
                    "text": " I couldn't extract any ingredients from your message. "
                            "Try: **'What can I make with chicken, garlic, and lemon?'**",
                    "suggestions": ["What can I make with chicken and garlic?", "Recipe with eggs and spinach"],
                }

            translated_ings = [RO_TO_EN.get(i, i) for i in ings]

            agent_logs = []
            if self.agent:
                agent_res = self.agent.run_agentic_retrieval(ings, filters={"cuisine": "Any", "difficulty": "Any"})
                recipes = agent_res["recipes"]
                agent_logs = agent_res["logs"]
            else:
                query_str = " ".join(ings)
                recipes = self.rag.retrieve(query=query_str, top_k=3)
                agent_logs = [f"Retrieval run for query: {query_str}"]

            if not recipes:
                return {
                    "type": "text",
                    "text": f" I couldn't find any recipes with **{', '.join(ings)}**. Try other ingredients!",
                    "suggestions": ["Chicken recipes", "Vegetarian recipes"],
                    "agent_logs": agent_logs
                }

            from recipe_generator import invent_recipes
            invented = invent_recipes(user_ingredients=translated_ings, retrieved_recipes=recipes, num_recipes=min(3, len(recipes)))

            return {
                "type": "recipes",
                "text": f" I adapted **{len(invented)} recipes** for you based on your ingredients:",
                "recipes": invented,
                "query_ingredients": ings,
                "agent_logs": agent_logs
            }

        # ── Recipe info ───────────────────────────────────────────────────────
        if intent == "recipe_info":
            dish = self._extract_dish_name(message)
            if not dish:
                dish_tokens = self._extract_ingredients(message)
                dish = " ".join(dish_tokens[:3])
            if not dish:
                return {
                    "type": "text",
                    "text": " Tell me what recipe you are looking for! E.g. **'How to make carbonara?'**",
                    "suggestions": ["How to make risotto?", "Pad thai recipe", "How to make shakshuka?"],
                }

            translated_dish = " ".join([RO_TO_EN.get(w, w) for w in dish.lower().split()])

            recipes = self.rag.retrieve(query=translated_dish, top_k=1)
            if not recipes:
                return {
                    "type": "text",
                    "text": f" I couldn't find the recipe for **{dish}** in the database. "
                            f"Try searching with its main ingredients!",
                    "suggestions": [f"What can I make with {dish}?", "Surprise me!"],
                }

            from recipe_generator import invent_recipes
            base_recipe = recipes[0]
            invented = invent_recipes(user_ingredients=base_recipe.get("ingredients", [])[:3], retrieved_recipes=[base_recipe], num_recipes=1)
            full_rec = invented[0] if invented else base_recipe

            return {
                "type": "recipe_detail",
                "text": f" I found the best matching recipe for **{dish}**:",
                "recipe": full_rec,
                "agent_logs": [f"Search for dish: '{translated_dish}' matches '{base_recipe.get('title')}' with score {base_recipe.get('hybrid_score', 0):.2f}"]
            }

        # ── Technique info ────────────────────────────────────────────────────
        if intent == "technique_info":
            tech_key = self._extract_technique(message)
            if tech_key and tech_key in TECHNIQUES:
                t = TECHNIQUES[tech_key]
                return {
                    "type": "technique",
                    "emoji": t["emoji"],
                    "title": f"{t['emoji']} {tech_key.title()}",
                    "text": t["explanation"],
                    "suggestions": [f"Recipe using {tech_key}", "Other cooking technique"],
                }
            return {
                "type": "technique_list",
                "text": " **Culinary techniques available** in my knowledge base:",
                "techniques": [
                    {"key": k, "ro": k, "emoji": v["emoji"]}
                    for k, v in TECHNIQUES.items()
                ],
                "suggestions": ["What is braising?", "Explain wok hei", "What is emulsification?"],
            }

        # ── Substitution ──────────────────────────────────────────────────────
        if intent == "substitution":
            target = self._extract_sub_target(message)
            if target and target in SUBSTITUTIONS:
                s = SUBSTITUTIONS[target]
                return {
                    "type": "substitution",
                    "emoji": s["emoji"],
                    "title": f"{s['emoji']} Substitutions for {target}",
                    "text": f"Here are **{len(s['subs'])} alternatives** for {target}:",
                    "substitutions": s["subs"],
                    "suggestions": ["What can I use instead of milk?", "Butter substitute", "No eggs in baking"],
                }
            return {
                "type": "substitution_list",
                "text": " **Ingredients with available substitutions:**",
                "available": [
                    {"key": k, "ro": k, "emoji": v["emoji"]}
                    for k, v in SUBSTITUTIONS.items()
                ],
                "suggestions": ["Egg substitute", "What can I use instead of butter?", "No parmesan"],
            }

        # ── Dietary filter ────────────────────────────────────────────────────
        if intent == "dietary_filter":
            msg_lower = message.lower()
            tag = None
            if "vegan" in msg_lower:
                tag, label = "vegan", "vegan "
            elif "vegetarian" in msg_lower:
                tag, label = "vegetarian", "vegetarian "
            elif "gluten" in msg_lower:
                tag, label = None, "gluten-free "
            else:
                tag, label = "vegan", "healthy "

            ings = ["vegetable"] if tag == "vegan" else ["egg", "cheese"]
            recipes = self.rag.retrieve(query=" ".join(ings), top_k=10)
            if tag:
                recipes = [r for r in recipes if tag in r.get("tags", [])]
            recipes = recipes[:3]

            if not recipes:
                return {"type": "text", "text": f" I couldn't find any {label}recipes with these criteria.", "suggestions": ["Simple vegan recipes", "Surprise me!"]}

            from recipe_generator import invent_recipes
            invented = invent_recipes(user_ingredients=ings, retrieved_recipes=recipes, num_recipes=len(recipes))

            return {
                "type": "recipes",
                "text": f" **{label.capitalize()}recipes** in the database:",
                "recipes": invented,
                "agent_logs": [f"Diet filter: '{tag or 'gluten-free'}' on RAG results"]
            }

        # ── Time filter ───────────────────────────────────────────────────────
        if intent == "time_filter":
            max_t = self._extract_time(message) or 30
            recipes = self.rag.retrieve(query="quick fast easy", top_k=15)
            fast = [r for r in recipes if r.get("time_minutes", 999) <= max_t][:3]
            if not fast:
                return {
                    "type": "text",
                    "text": f" I couldn't find any recipes under {max_t} minutes. Try 30 or 45 minutes!",
                    "suggestions": ["Recipes under 30 minutes", "Quick eggs dish"],
                }

            from recipe_generator import invent_recipes
            invented = invent_recipes(user_ingredients=["quick"], retrieved_recipes=fast, num_recipes=len(fast))

            return {
                "type": "recipes",
                "text": f" **Quick recipes under {max_t} minutes:**",
                "recipes": invented,
                "agent_logs": [f"Time filter: recipes under {max_t} minutes from vector index"]
            }

        # ── Cuisine filter ────────────────────────────────────────────────────
        if intent == "cuisine_filter":
            msg_lower = message.lower()
            cuisine_en = None
            for ro_term, en_term in CUISINE_MAP.items():
                if ro_term in msg_lower or en_term.lower() in msg_lower:
                    cuisine_en = en_term
                    break
            if not cuisine_en:
                return {
                    "type": "text",
                    "text": " Which cuisine do you prefer?",
                    "suggestions": ["Italian recipes", "Thai recipes", "Indian recipes", "Japanese recipes", "Mexican recipes"],
                }
            recipes = self.rag.retrieve(query="classic traditional cuisine", filters={"cuisine": cuisine_en}, top_k=3)
            if not recipes:
                return {
                    "type": "text",
                    "text": f" I couldn't find any recipes from **{cuisine_en}** cuisine with these criteria.",
                    "suggestions": ["Italian recipes", "Surprise me!"],
                }

            from recipe_generator import invent_recipes
            invented = invent_recipes(user_ingredients=["traditional"], retrieved_recipes=recipes, num_recipes=len(recipes))

            return {
                "type": "recipes",
                "text": f" **Recipes from {cuisine_en} cuisine:**",
                "recipes": invented,
                "agent_logs": [f"Cuisine filter: '{cuisine_en}'"]
            }

        # ── Random ────────────────────────────────────────────────────────────
        if intent == "random_recipe":
            all_r = self.rag.recipes
            recipe = random.choice(all_r)

            from recipe_generator import invent_recipes
            invented = invent_recipes(user_ingredients=recipe.get("ingredients", [])[:3], retrieved_recipes=[recipe], num_recipes=1)
            full_rec = invented[0] if invented else recipe

            return {
                "type": "recipe_detail",
                "text": f" Here is the surprise recipe of the day!",
                "recipe": full_rec,
                "suggestions": ["Another surprise!", "Similar recipes"],
                "agent_logs": ["Random recipe selected from vector DB"]
            }

        # ── Unknown / fallback ────────────────────────────────────────────────
        tip = random.choice(COOKING_TIPS_GENERAL)
        return {
            "type": "unknown",
            "text": " I didn't quite understand your question, but here is a quick cooking tip:",
            "tip": f"{tip['emoji']} {tip['tip']}",
            "suggestions": [
                "What can I make with chicken and garlic?",
                "Explain what braising is",
                "Substitute for eggs",
                "Quick vegan recipes",
                "Help",
            ],
        }

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _recipe_summary(self, r: dict) -> dict:
        return {
            "title":          r.get("title", ""),
            "cuisine":        r.get("cuisine", ""),
            "difficulty":     r.get("difficulty", ""),
            "time_minutes":   r.get("time_minutes", 0),
            "servings":       r.get("servings", 4),
            "tags":           r.get("tags", [])[:3],
            "flavor_profile": r.get("flavor_profile", [])[:3],
            "ingredients":    r.get("ingredients", [])[:6],
            "score":          round(r.get("hybrid_score", r.get("score", 0)), 3),
        }

    def _recipe_full(self, r: dict) -> dict:
        return {
            "title":          r.get("title", ""),
            "cuisine":        r.get("cuisine", ""),
            "difficulty":     r.get("difficulty", ""),
            "time_minutes":   r.get("time_minutes", 0),
            "servings":       r.get("servings", 4),
            "ingredients":    r.get("ingredients", []),
            "steps":          r.get("steps", []),
            "tags":           r.get("tags", []),
            "flavor_profile": r.get("flavor_profile", []),
            "description":  r.get("description", ""),
            "key_technique": r.get("key_technique", ""),
        }
