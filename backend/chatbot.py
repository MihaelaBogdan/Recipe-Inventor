"""
chatbot.py — RAG Chatbot
====================================
Intents supported:
  find_recipe      — "what can I make with chicken and garlic?"
  recipe_info      — "how do I make carbonara?" / "recipe for risotto"
  technique_info   — "what is braising?" / "explain wok hei"
  substitution     — "what replaces eggs?"
  dietary_filter   — "vegan recipes / gluten free"
  time_filter      — "something quick under 30 minutes"
  cuisine_filter   — "Italian / Thai / Mexican recipes"
  random_recipe    — "surprise me!" / "something random"
  chitchat         — "hello" / "thank you" / "who are you?"
  help             — "help" / "what can you do?"
  unknown          — fallback with suggestions
"""
 
import re
import random
import numpy as np
from intent_examples import INTENT_EXAMPLES
 
 
# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE BASE: cooking techniques
# ─────────────────────────────────────────────────────────────────────────────
TECHNIQUES: dict[str, dict] = {
    "braising": {
        "name": "Braising", "emoji": "🍖",
        "explanation": (
            "Braising is a slow, two-stage cooking technique: ingredients are first seared "
            "at high heat to develop a caramelized crust (Maillard reaction), then slowly "
            "cooked in a covered liquid (wine, stock, water) at low temperature, 150–165°C, "
            "for 1–3 hours. Collagen in the meat transforms into gelatin, creating silky sauces. "
            "Classic examples: Beef Bourguignon, Osso Buco, Coq au Vin."
        ),
        "keywords": ["braising", "braise", "braised", "slow cook", "slow cooked"],
    },
    "sauteing": {
        "name": "Sautéing", "emoji": "🥘",
        "explanation": (
            "Sautéing cooks ingredients quickly in a small amount of fat at high heat, "
            "stirring or moving the pan constantly. The goal is surface caramelization "
            "without overcooking the interior. The word comes from the French 'sauter' "
            "(to jump) — constant movement prevents burning. Essential for vegetables, "
            "mushrooms, finely cut meat. The pan must be hot before adding ingredients."
        ),
        "keywords": ["saute", "sauteing", "sautéing", "sautéed", "stir", "pan fry"],
    },
    "wok hei": {
        "name": "Wok Hei", "emoji": "🔥",
        "explanation": (
            "Wok hei (镬气, 'breath of the wok') is the smoky, slightly charred and intense "
            "flavor that food develops when cooked in an extremely hot wok. It's produced by "
            "rapid moisture evaporation, Maillard reactions at 300°C+, and natural sugar "
            "caramelization. The secret: the wok must be INCANDESCENT, and food added in "
            "small quantities. Any cooling of the wok turns stir-fry into steaming — "
            "this is the most common mistake."
        ),
        "keywords": ["wok hei", "wok", "stir fry", "stir-fry", "high heat wok"],
    },
    "emulsification": {
        "name": "Emulsification", "emoji": "🥚",
        "explanation": (
            "Emulsification combines two liquids that normally don't mix (fat + water) "
            "through an emulsifying agent (lecithin from egg yolk, mustard, miso). "
            "Carbonara: starch from pasta water + egg yolk creates a creamy sauce without cream. "
            "Mayonnaise: oil + egg yolk + acid. "
            "Caesar dressing: oil + lemon + mustard + anchovy. "
            "Key: controlled temperature and constant agitation."
        ),
        "keywords": ["emulsification", "emulsify", "emulsified", "creamy without cream", "emulsion"],
    },
    "blanching": {
        "name": "Blanching", "emoji": "🥦",
        "explanation": (
            "Blanching partially cooks vegetables in salted boiling water (30 sec – 3 min), "
            "followed immediately by cooling in ice water to stop cooking. "
            "Effects: preserves vibrant color (chlorophyll stays stable), "
            "texture stays crisp, bitterness is removed, oxidative enzymes are destroyed. "
            "Essential for spinach in Palak Paneer, green beans in salads, broccoli before freezing."
        ),
        "keywords": ["blanching", "blanch", "blanched", "boiling water ice bath", "ice bath"],
    },
    "reduction": {
        "name": "Reduction", "emoji": "⬇️",
        "explanation": (
            "Reduction concentrates flavors by evaporating liquid over medium-high heat, "
            "uncovered. As water evaporates, sugars, proteins and flavors concentrate, "
            "creating denser and more intense sauces. "
            "Rule: wine is reduced by half before adding stock. "
            "Teriyaki sauce, balsamic reduction, wine glaze — all use this technique. "
            "Don't rush the process with high heat: the risk of burning increases exponentially."
        ),
        "keywords": ["reduction", "reduce", "reducing", "reduced", "thickened", "concentrated"],
    },
    "caramelization": {
        "name": "Caramelization", "emoji": "🍯",
        "explanation": (
            "Caramelization is the thermal oxidation of sugars at 160–180°C, producing "
            "hundreds of new aromatic compounds with notes of butter, nuts, vanilla and complex bitterness. "
            "Different from the Maillard reaction (which involves proteins + sugars). "
            "Caramelized onions require 45–60 minutes over low heat — any shortcut produces "
            "soft, sweated onions, not caramelized ones. French onion soup demonstrates "
            "how transformative patience can be."
        ),
        "keywords": ["caramelization", "caramelize", "caramelized", "caramel", "burnt sugar", "caramelized onions"],
    },
    "maillard": {
        "name": "Maillard Reaction", "emoji": "🥩",
        "explanation": (
            "The Maillard reaction is a chemical reaction between amino acids and reducing sugars "
            "at 140–165°C, creating hundreds of aromatic compounds that give the 'roasted' note, "
            "brown crust and complex flavors. Responsible for: bread crust, seared meat color, "
            "roasted coffee note, tempered chocolate. "
            "CRITICAL: the pan must be dry and meat patted dry with a towel — moisture "
            "lowers temperature below 100°C and produces steam instead of browning."
        ),
        "keywords": ["maillard", "maillard reaction", "browning", "sear", "crust", "brown"],
    },
    "tempering": {
        "name": "Tempering Spices", "emoji": "🌶️",
        "explanation": (
            "Tempering (tadka) is the Indian technique of blooming spices "
            "in hot fat (clarified butter, oil) to release fat-soluble compounds. "
            "Cumin seeds 'pop' in 30 seconds — the signal they're ready. "
            "Everything is then poured hot over the dish (dal, yogurt, soups). "
            "Order matters: whole seeds → onion → garlic → ground spices. "
            "Ground spices go in last — they burn fastest."
        ),
        "keywords": ["tempering", "tadka", "blooming spices", "spices in oil", "bloom"],
    },
    "deglazing": {
        "name": "Deglazing", "emoji": "🍷",
        "explanation": (
            "Deglazing adds liquid (wine, stock, vinegar, citrus juice) "
            "to a hot pan after searing to dissolve the 'fond' — "
            "the caramelized bits stuck to the bottom. The fond contains intense flavors "
            "from Maillard reactions and is the BASE of any good sauce. "
            "Never waste a pan with brown fond! "
            "When adding liquid, the sizzling and steam are normal — "
            "the temperature difference creates instant deglazing."
        ),
        "keywords": ["deglazing", "deglaze", "deglaized", "fond", "pan drippings", "wine in pan"],
    },
    "confit": {
        "name": "Confit", "emoji": "🦆",
        "explanation": (
            "Confit cooks ingredients COMPLETELY SUBMERGED in fat at low temperature "
            "(70–90°C) for a long time. Duck confit cooks in its own fat "
            "for 3–4 hours — the result is incredibly tender meat that falls off the bone. "
            "The technique originally appeared as a preservation method (before refrigerators). "
            "Potatoes confit in olive oil at 90°C = the creamiest potatoes possible. "
            "Garlic confit in oil = sweet, silky paste without the rawness."
        ),
        "keywords": ["confit", "fat poached", "duck confit", "garlic confit", "submerged in fat"],
    },
    "poaching": {
        "name": "Poaching", "emoji": "🥚",
        "explanation": (
            "Poaching cooks delicate foods (eggs, fish, chicken) in liquid at 71–82°C "
            "— below boiling point. Small bubbles on the bottom indicate the correct temperature. "
            "Poached eggs: water with vinegar (reduces spreading of whites), swirl with spoon, "
            "raw egg submerged 3–4 minutes. "
            "Chicken poached in white wine with herbs: the moistest chicken breast possible. "
            "Salmon poached in vegetable stock: tender with absorbed stock flavors."
        ),
        "keywords": ["poaching", "poach", "poached", "poached eggs", "gentle simmer"],
    },
}
 
# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE BASE: ingredient substitutions
# ─────────────────────────────────────────────────────────────────────────────
SUBSTITUTIONS: dict[str, dict] = {
    "eggs": {
        "name": "eggs", "emoji": "🥚",
        "subs": [
            {"sub": "Flax egg", "ratio": "1 tbsp ground flax seeds + 3 tbsp water = 1 egg", "best_for": "cakes, muffins, vegan burgers"},
            {"sub": "Chia egg", "ratio": "1 tbsp chia seeds + 3 tbsp water = 1 egg", "best_for": "dense cakes, bread"},
            {"sub": "Mashed banana", "ratio": "1/4 banana = 1 egg", "best_for": "muffins, pancakes — adds sweetness"},
            {"sub": "Aquafaba (chickpea water)", "ratio": "3 tbsp = 1 whole egg; 2 tbsp = 1 egg white", "best_for": "meringue, vegan mayo, mousse"},
            {"sub": "Yogurt / coconut milk", "ratio": "1/4 cup = 1 egg", "best_for": "moist cakes"},
        ],
    },
    "butter": {
        "name": "butter", "emoji": "🧈",
        "subs": [
            {"sub": "Coconut oil", "ratio": "1:1", "best_for": "cakes, cookies, sauces"},
            {"sub": "Olive oil", "ratio": "3/4 of amount", "best_for": "savory dishes, sautéing"},
            {"sub": "Mashed avocado", "ratio": "1:1", "best_for": "dark cakes (chocolate)"},
            {"sub": "Vegan butter (Violife, etc)", "ratio": "1:1", "best_for": "any butter recipe"},
            {"sub": "Ghee", "ratio": "1:1", "best_for": "high heat cooking — higher smoke point"},
        ],
    },
    "milk": {
        "name": "milk", "emoji": "🥛",
        "subs": [
            {"sub": "Oat milk", "ratio": "1:1", "best_for": "sauces, cakes, drinks — most neutral flavor"},
            {"sub": "Almond milk", "ratio": "1:1", "best_for": "desserts, cereals"},
            {"sub": "Soy milk", "ratio": "1:1", "best_for": "anything — similar protein content to milk"},
            {"sub": "Coconut milk (canned)", "ratio": "1:1", "best_for": "curries, creamy sauces"},
            {"sub": "Water + 1 tbsp butter/oil", "ratio": "1:1", "best_for": "emergency in savory recipes"},
        ],
    },
    "cream": {
        "name": "cream", "emoji": "🍶",
        "subs": [
            {"sub": "Full-fat coconut milk (canned)", "ratio": "1:1", "best_for": "curries, soups, desserts"},
            {"sub": "Cashew cream (soaked cashews + blender)", "ratio": "1:1", "best_for": "pasta, sauces, desserts"},
            {"sub": "Greek yogurt", "ratio": "1:1, added off-heat", "best_for": "sauces — don't boil, it splits"},
            {"sub": "Blended silken tofu", "ratio": "1:1", "best_for": "creamy soups, cheesecake"},
        ],
    },
    "parmesan": {
        "name": "parmesan", "emoji": "🧀",
        "subs": [
            {"sub": "Nutritional yeast", "ratio": "3-4 tbsp per 100g parmesan", "best_for": "pasta, risotto, popcorn — similar umami flavor"},
            {"sub": "Pecorino Romano", "ratio": "1:1", "best_for": "saltier — reduce salt in recipe"},
            {"sub": "Grana Padano", "ratio": "1:1", "best_for": "milder, cheaper"},
            {"sub": "Almonds + nutritional yeast + salt", "ratio": "blend 100g almonds + 4 tbsp yeast + 1 tbsp salt", "best_for": "vegan, pasta/salad topping"},
        ],
    },
    "flour": {
        "name": "flour", "emoji": "🌾",
        "subs": [
            {"sub": "Almond flour", "ratio": "1:1 in most cases", "best_for": "moist cakes, gluten-free"},
            {"sub": "Oat flour (blended oats)", "ratio": "1:1", "best_for": "cakes, cookies, pancakes"},
            {"sub": "Rice flour", "ratio": "1:1", "best_for": "light batters, gluten-free"},
            {"sub": "Cornstarch (thickening)", "ratio": "1 tbsp starch = 2 tbsp flour", "best_for": "sauces, soups, not baking"},
        ],
    },
    "bacon": {
        "name": "bacon", "emoji": "🥓",
        "subs": [
            {"sub": "Smoked tempeh (with liquid smoke + soy)", "ratio": "1:1", "best_for": "closest texture match"},
            {"sub": "King oyster mushrooms (dry fried)", "ratio": "thin slices", "best_for": "similar crispy texture"},
            {"sub": "Dried coconut chips + soy + liquid smoke", "ratio": "50g coconut = bacon strips", "best_for": "salads, vegan BLT"},
            {"sub": "Prosciutto / Pancetta", "ratio": "1:1", "best_for": "if vegan not needed — more refined"},
        ],
    },
    "honey": {
        "name": "honey", "emoji": "🍯",
        "subs": [
            {"sub": "Maple syrup", "ratio": "3/4 of amount", "best_for": "almost identical in baking"},
            {"sub": "Agave syrup", "ratio": "3/4 of amount", "best_for": "more neutral, dissolves easier"},
            {"sub": "Date syrup", "ratio": "1:1", "best_for": "smoothies, desserts with caramel flavor"},
            {"sub": "Brown sugar + water", "ratio": "1 tbsp sugar + 1/4 tbsp water = 1 tbsp honey", "best_for": "cooking emergency"},
        ],
    },
    "wine": {
        "name": "wine", "emoji": "🍷",
        "subs": [
            {"sub": "Vegetable stock + 1 tbsp white wine vinegar", "ratio": "1:1", "best_for": "white wine in risotto, sauces"},
            {"sub": "White/red grape juice + vinegar", "ratio": "3/4 juice + 1/4 vinegar", "best_for": "fruity, for braises"},
            {"sub": "Water + 1-2 tbsp balsamic vinegar", "ratio": "1:1", "best_for": "red wine in sauces"},
            {"sub": "Apple juice", "ratio": "1:1", "best_for": "white wine in pork, chicken"},
        ],
    },
    "soy sauce": {
        "name": "soy sauce", "emoji": "🍶",
        "subs": [
            {"sub": "Tamari (gluten-free)", "ratio": "1:1", "best_for": "identical, without wheat"},
            {"sub": "Coconut aminos", "ratio": "1:1, slightly sweeter", "best_for": "soy-free, paleo"},
            {"sub": "Worcestershire sauce", "ratio": "1:1", "best_for": "more complex, contains anchovy"},
            {"sub": "Miso + water", "ratio": "1 tbsp miso + 1 tbsp water = 2 tbsp soy sauce", "best_for": "deeper umami"},
        ],
    },
}
 
# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE BASE: general cooking tips
# ─────────────────────────────────────────────────────────────────────────────
COOKING_TIPS_GENERAL: list[dict] = [
    {"tip": "Salt your pasta water until it tastes like the sea. Under-salting pasta is the most common kitchen mistake.", "emoji": "🧂"},
    {"tip": "Let meat come to room temperature 30 minutes before cooking. You'll get more even cooking throughout.", "emoji": "🥩"},
    {"tip": "Don't crowd the pan! If you add too many ingredients, the temperature drops and you steam instead of sear.", "emoji": "🍳"},
    {"tip": "Always reserve pasta water before draining. The starch in it binds the sauce perfectly.", "emoji": "🍝"},
    {"tip": "Add spices in layers, not just at the end. Taste and adjust as you go.", "emoji": "🌶️"},
    {"tip": "A real cast iron skillet will be the best product in your kitchen. It lasts a lifetime.", "emoji": "🍳"},
    {"tip": "Acid (lemon, vinegar) added at the end brightens ANY dish. It's the secret magic of restaurants.", "emoji": "🍋"},
    {"tip": "Let meat rest after cooking: 5 min for chicken, 10 min for steak. The juices redistribute.", "emoji": "⏳"},
    {"tip": "Buy a good sharp knife and sharpen it monthly. A good knife completely changes the cooking experience.", "emoji": "🔪"},
    {"tip": "Making good risotto = 18 minutes of stirring + patience. There is no shortcut for this.", "emoji": "🍚"},
]
 
# ─────────────────────────────────────────────────────────────────────────────
# CUISINE MAP (direct English keys matching dataset)
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
    "american": "American",
    "middle eastern": "Middle Eastern",
    "vietnamese": "Vietnamese",
    "greek": "Greek",
    "spanish": "Spanish",
}
 
 
# ─────────────────────────────────────────────────────────────────────────────
# CHATBOT ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class RecipeChatbot:
    """
    RAG Chatbot with semantic intent detection.
    """
 
    def __init__(self, rag_engine, agent=None):
        self.rag = rag_engine
        self.agent = agent
        self.encoder = rag_engine.encoder
 
        # Semantic technique index
        self._technique_keys = list(TECHNIQUES.keys())
        self._technique_texts = [
            f"{v['name']} {' '.join(v['keywords'])}"
            for v in TECHNIQUES.values()
        ]
        self._technique_matrix = self.encoder.encode(self._technique_texts)
 
        # Semantic substitution index
        self._sub_keys = list(SUBSTITUTIONS.keys())
        self._sub_texts = [
            f"{v['name']} {k}"
            for k, v in SUBSTITUTIONS.items()
        ]
        self._sub_matrix = self.encoder.encode(self._sub_texts)
 
        # Semantic intent index
        self._intent_labels = []
        self._intent_vectors = []
        for intent, examples in INTENT_EXAMPLES.items():
            for emb in self.encoder.encode(examples):
                self._intent_labels.append(intent)
                self._intent_vectors.append(emb)
        self._intent_matrix = __import__('numpy').array(self._intent_vectors)
 
        print("Semantic intent + technique + substitution indexes ready.")
 
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
        q = self.encoder.encode([message])[0]
        best_idx, best_score = self._cosine_best(self._intent_matrix, q)
        if best_score < 0.25:
            return "unknown", None
        return self._intent_labels[best_idx], None
 
    # ── Extract ingredients from message ──────────────────────────────────────
    def _extract_ingredients(self, message: str) -> list[str]:
        STOPWORDS = {
            "what", "can", "i", "make", "with", "have", "got", "some", "and", "or",
            "the", "a", "an", "do", "use", "using", "only", "just", "few", "any",
            "recipe", "recipes", "cook", "cooking", "food", "meal", "dish", "for",
            "me", "my", "at", "home", "fridge", "leftovers", "ingredients",
        }
        clean = re.sub(r'[?!.,;:]', ' ', message.lower())
        tokens = [t.strip() for t in re.split(r'[\s,;/]+', clean) if len(t.strip()) > 2]
        result = [t for t in tokens if t not in STOPWORDS]
        return result[:8]
 
    # ── Extract recipe name from message ──────────────────────────────────────
    def _extract_dish_name(self, message: str) -> str:
        patterns = [
            r"how (?:do i|to) make (.+?)[\?!.]?$",
            r"how (?:do i|to) cook (.+?)[\?!.]?$",
            r"recipe for (.+?)[\?!.]?$",
            r"recipe (?:of|for) (.+?)[\?!.]?$",
            r"how (?:do i|to) prepare (.+?)[\?!.]?$",
            r"make me (?:a |some )?(.+?)[\?!.]?$",
            r"steps (?:to|for) (?:make|cook) (.+?)[\?!.]?$",
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
        m = re.search(r'(\d+)\s*(min|minutes?|hours?|hr)', message.lower())
        if m:
            val = int(m.group(1))
            unit = m.group(2)
            return val * 60 if 'h' in unit else val
        if 'quick' in message.lower() or 'fast' in message.lower():
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
                "text": "👋 Hi! I'm **Chef Bot RAG** — your AI cooking assistant! "
                        "Tell me what ingredients you have and I'll find perfect recipes for you. "
                        "I can also explain cooking techniques and suggest ingredient substitutions.",
                "suggestions": ["What can I make with chicken and garlic?", "Explain braising", "Vegan recipes", "Surprise me!"],
            }
 
        if intent == "chitchat_thanks":
            responses = [
                "🙏 You're welcome! Any other culinary questions?",
                "😊 Glad it helped! Enjoy your meal!",
                "👨‍🍳 Happy to help! Let me know what else you're cooking!",
            ]
            return {"type": "text", "text": random.choice(responses), "suggestions": ["Another recipe", "Different technique"]}
 
        if intent == "chitchat_identity":
            return {
                "type": "text",
                "text": "🤖 I'm **Chef Bot RAG** — a culinary chatbot! "
                        "I work through:\n"
                        "• **Semantic intent detection** with sentence-transformers\n"
                        "• **RAG retrieval** with ChromaDB + BM25 hybrid\n"
                        "• **Knowledge bases** for techniques and substitutions\n"
                        "• **Query expansion** with ingredient synonyms\n\n",
                "suggestions": ["How does RAG work?", "What recipes do you have?"],
            }
 
        if intent == "chitchat_bye":
            return {"type": "text", "text": "👋 Goodbye! Enjoy your cooking!", "suggestions": []}
 
        # ── Help ──────────────────────────────────────────────────────────────
        if intent == "help":
            return {
                "type": "help",
                "text": "👨‍🍳 **I can help you with:**",
                "capabilities": [
                    {"icon": "🔍", "title": "Find recipes by ingredients", "example": "What can I make with chicken, garlic and lemon?"},
                    {"icon": "📖", "title": "Explain any recipe in the database", "example": "How do I make carbonara?"},
                    {"icon": "🎓", "title": "Explain cooking techniques", "example": "What is the wok hei technique?"},
                    {"icon": "🔄", "title": "Suggest ingredient substitutions", "example": "What do I use instead of eggs?"},
                    {"icon": "🥗", "title": "Filter by cuisine/diet/time", "example": "Vegan recipes under 30 minutes"},
                    {"icon": "🎲", "title": "Surprise you with a random recipe", "example": "Surprise me!"},
                    {"icon": "💡", "title": "Give general cooking tips", "example": "Give me a cooking tip"},
                ],
            }
 
        # ── Find recipe by ingredients ────────────────────────────────────────
        if intent == "find_recipe":
            ings = self._extract_ingredients(message)
            if not ings:
                return {
                    "type": "text",
                    "text": "🔍 I couldn't extract ingredients from your message. "
                            "Try: **'What can I make with chicken, garlic and lemon?'**",
                    "suggestions": ["What can I make with chicken and garlic?", "Recipe with eggs and spinach"],
                }
 
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
                    "text": f"😕 No recipes found with **{', '.join(ings)}**. Try different ingredients!",
                    "suggestions": ["Recipes with chicken", "Vegetarian recipes"],
                    "agent_logs": agent_logs
                }
 
            from recipe_generator import invent_recipes
            invented = invent_recipes(user_ingredients=ings, retrieved_recipes=recipes, num_recipes=min(3, len(recipes)))
 
            return {
                "type": "recipes",
                "text": f"✅ Found **{len(invented)} recipes** based on your ingredients:",
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
                    "text": "🍳 Tell me which recipe you're looking for! Ex: **'How do I make carbonara?'**",
                    "suggestions": ["How do I make risotto?", "Recipe for pad thai", "How do I make shakshuka?"],
                }
 
            recipes = self.rag.retrieve(query=dish, top_k=1)
            if not recipes:
                return {
                    "type": "text",
                    "text": f"😕 Couldn't find a recipe for **{dish}** in the database. "
                            f"Try searching with the main ingredients!",
                    "suggestions": [f"What can I make with {dish}?", "Surprise me!"],
                }
 
            from recipe_generator import invent_recipes
            base_recipe = recipes[0]
            invented = invent_recipes(user_ingredients=base_recipe.get("ingredients", [])[:3], retrieved_recipes=[base_recipe], num_recipes=1)
            full_rec = invented[0] if invented else base_recipe
 
            return {
                "type": "recipe_detail",
                "text": f"📖 Best match for **{dish}**:",
                "recipe": full_rec,
                "agent_logs": [f"Search for dish: '{dish}' matches '{base_recipe.get('title')}' with score {base_recipe.get('hybrid_score', 0):.2f}"]
            }
 
        # ── Technique info ────────────────────────────────────────────────────
        if intent == "technique_info":
            tech_key = self._extract_technique(message)
            if tech_key and tech_key in TECHNIQUES:
                t = TECHNIQUES[tech_key]
                return {
                    "type": "technique",
                    "emoji": t["emoji"],
                    "title": f"{t['emoji']} {t['name']} ({tech_key})",
                    "text": t["explanation"],
                    "suggestions": [f"Recipe using {t['name'].lower()}", "Another cooking technique"],
                }
            return {
                "type": "technique_list",
                "text": "🎓 **Available cooking techniques** in my knowledge base:",
                "techniques": [
                    {"key": k, "ro": v["name"], "emoji": v["emoji"]}
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
                    "title": f"{s['emoji']} Substitutes for {s['name']}",
                    "text": f"Here are **{len(s['subs'])} alternatives** for {s['name']}:",
                    "substitutions": s["subs"],
                    "suggestions": ["Substitute for milk?", "Replacement for butter", "No eggs in baking"],
                }
            return {
                "type": "substitution_list",
                "text": "🔄 **Ingredients with available substitutions:**",
                "available": [
                    {"key": k, "ro": v["name"], "emoji": v["emoji"]}
                    for k, v in SUBSTITUTIONS.items()
                ],
                "suggestions": ["Substitute for eggs", "What replaces butter?", "No parmesan"],
            }
 
        # ── Dietary filter ────────────────────────────────────────────────────
        if intent == "dietary_filter":
            msg_lower = message.lower()
            tag = None
            if any(w in msg_lower for w in ["vegan"]):
                tag, label = "vegan", "vegan 🌱"
            elif any(w in msg_lower for w in ["vegetarian"]):
                tag, label = "vegetarian", "vegetarian 🥦"
            elif any(w in msg_lower for w in ["gluten", "gluten-free", "gluten free"]):
                tag, label = None, "gluten-free 🌾"
            elif any(w in msg_lower for w in ["keto"]):
                tag, label = "keto", "keto 🥑"
            elif any(w in msg_lower for w in ["paleo"]):
                tag, label = "paleo", "paleo 🍖"
            else:
                tag, label = "vegan", "healthy 🥗"
 
            ings = ["vegetable"] if tag in ("vegan", "vegetarian") else ["protein", "meat"]
            recipes = self.rag.retrieve(query=" ".join(ings), top_k=10)
            if tag:
                recipes = [r for r in recipes if tag in r.get("tags", [])]
            recipes = recipes[:3]
 
            if not recipes:
                return {"type": "text", "text": f"😕 No {label} recipes found with these criteria.", "suggestions": ["Simple vegan recipes", "Surprise me!"]}
 
            from recipe_generator import invent_recipes
            invented = invent_recipes(user_ingredients=ings, retrieved_recipes=recipes, num_recipes=len(recipes))
 
            return {
                "type": "recipes",
                "text": f"🥗 **{label.title()} recipes** from the database:",
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
                    "text": f"😕 No recipes found under {max_t} minutes. Try 30 or 45 minutes!",
                    "suggestions": ["Recipes under 30 minutes", "Quick egg recipes"],
                }
 
            from recipe_generator import invent_recipes
            invented = invent_recipes(user_ingredients=["quick"], retrieved_recipes=fast, num_recipes=len(fast))
 
            return {
                "type": "recipes",
                "text": f"⚡ **Quick recipes under {max_t} minutes:**",
                "recipes": invented,
                "agent_logs": [f"Time filter: recipes under {max_t} minutes from vector index"]
            }
 
        # ── Cuisine filter ────────────────────────────────────────────────────
        if intent == "cuisine_filter":
            msg_lower = message.lower()
            cuisine_en = None
            for term, cuisine in CUISINE_MAP.items():
                if term in msg_lower:
                    cuisine_en = cuisine
                    break
            if not cuisine_en:
                return {
                    "type": "text",
                    "text": "🌍 Which cuisine do you prefer?",
                    "suggestions": ["Italian recipes", "Thai food", "Indian cuisine", "Japanese recipes", "Mexican food"],
                }
            recipes = self.rag.retrieve(query="classic traditional cuisine", filters={"cuisine": cuisine_en}, top_k=3)
            if not recipes:
                return {
                    "type": "text",
                    "text": f"😕 No **{cuisine_en}** recipes found with these criteria.",
                    "suggestions": ["Italian recipes", "Surprise me!"],
                }
 
            from recipe_generator import invent_recipes
            invented = invent_recipes(user_ingredients=["traditional"], retrieved_recipes=recipes, num_recipes=len(recipes))
 
            return {
                "type": "recipes",
                "text": f"🌍 **{cuisine_en} cuisine recipes:**",
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
                "text": "🎲 Here's today's surprise!",
                "recipe": full_rec,
                "suggestions": ["Another surprise!", "Similar recipes"],
                "agent_logs": ["Random recipe selected from vector DB"]
            }
 
        # ── Unknown / fallback ────────────────────────────────────────────────
        tip = random.choice(COOKING_TIPS_GENERAL)
        return {
            "type": "unknown",
            "text": "🤔 I didn't quite understand, but here's a cooking tip for you:",
            "tip": f"{tip['emoji']} {tip['tip']}",
            "suggestions": [
                "What can I make with chicken and garlic?",
                "Explain braising",
                "Substitute for eggs",
                "Vegan recipes",
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
            "description":    r.get("description", ""),
            "key_technique":  r.get("key_technique", ""),
        }
 