"""
chatbot.py — RAG Chatbot fără LLM
====================================
Funcționează EXCLUSIV prin:
  1. Detectare intenție: regex + keywords (fără ML, fără LLM)
  2. Extragere entități: ingrediente, bucătării, tehnici din mesaj
  3. Retrieval RAG: TF-IDF + BM25 pentru întrebări despre rețete
  4. Răspuns din șabloane + baze de cunoștințe hardcodate

Intenții suportate:
  find_recipe      — "ce pot face cu pui și usturoi?"
  recipe_info      — "cum fac carbonara?" / "rețeta de risotto"
  technique_info   — "ce este braising?" / "explică wok hei"
  substitution     — "înlocuiesc ouăle cu ce?"
  dietary_filter   — "rețete vegane / fără gluten"
  time_filter      — "ceva rapid sub 30 minute"
  cuisine_filter   — "rețete italiene / thai / mexicane"
  random_recipe    — "surprinde-mă!" / "ceva aleatoriu"
  chitchat         — "bună ziua" / "mulțumesc" / "cine ești?"
  help             — "ajutor" / "ce poți face?"
  unknown          — fallback cu sugestii
"""

import re
import random
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE BASE: tehnici culinare
# ─────────────────────────────────────────────────────────────────────────────
TECHNIQUES: dict[str, dict] = {
    "braising": {
        "ro": "brezare", "emoji": "",
        "explanation": (
            "Brezarea (braising) este o tehnică de gătit lentă, în două etape: "
            "întâi ingredientele sunt rumenite la temperatură înaltă pentru a dezvolta "
            "o crustă caramelizată (reacția Maillard), apoi gătite lent într-un lichid "
            "acoperit (vin, bulion, apă) la temperatură joasă, 150–165°C, timp de 1–3 ore. "
            "Colagenul din carne se transformă în gelatină, creând sosuri mătăsoase. "
            "Exemple clasice: Beef Bourguignon, Osso Buco, Coq au Vin."
        ),
        "keywords": ["braising", "brezare", "brezat", "slow cook", "fiert lent"],
    },
    "sauteing": {
        "ro": "sotare", "emoji": "",
        "explanation": (
            "Sotarea (sautéing) gătește ingredientele rapid în puțin grăsime la temperatură "
            "înaltă, agitând sau mișcând constant tigaia. Scopul este caramelizarea "
            "superficială fără a găti excesiv interiorul. Cuvântul vine din francezul 'sauter' "
            "(a sări) — mișcarea continuă previne arderea. Crucială pentru legume, ciuperci, "
            "carne tăiată fin. Tigaia trebuie să fie fierbinte înainte de a adăuga ingredientele."
        ),
        "keywords": ["sote", "sotare", "saute", "sauté", "calire", "calit"],
    },
    "wok hei": {
        "ro": "wok hei", "emoji": "",
        "explanation": (
            "Wok hei (镬气, 'suflarea wok-ului') este aroma fumată, ușor carbonizată și "
            "intensă pe care o capătă mâncarea gătită într-un wok extrem de fierbinte. "
            "Se produce prin volatilizarea rapidă a umidității, reacții Maillard la 300°C+, "
            "și caramelizarea zaharurilor naturale. Secretul: wok-ul trebuie să fie "
            "INCANDESCENT, iar mâncarea pusă în cantități mici. Orice racire a wok-ului "
            "transformă stir-fry-ul în fierbere — asta este greșeala cea mai comună."
        ),
        "keywords": ["wok hei", "wok", "stir fry", "prajit wok", "tigaie chinezeasca"],
    },
    "emulsification": {
        "ro": "emulsionare", "emoji": "",
        "explanation": (
            "Emulsionarea combină două lichide care normal nu se amestecă (grăsime + apă) "
            "printr-un agent emulsificator (lecitină din gălbenuș, mustard, miso). "
            "Carbonara: amidonul din apa de paste + gălbenușul creează o sosă cremoasă fără smântână. "
            "Maioneza: ulei + gălbenuș + acid. "
            "Caesar dressing: ulei + lămâie + muștar + anșoa. "
            "Cheia: temperatura controlată și agitarea constantă."
        ),
        "keywords": ["emulsionare", "emulsifiere", "emulsificat", "emulsification", "cremos fara smantana"],
    },
    "blanching": {
        "ro": "opărire", "emoji": "",
        "explanation": (
            "Opărirea (blanching) gătește parțial legumele în apă clocotită cu sare (30 sec – 3 min), "
            "urmat imediat de răcire în apă cu gheață pentru a opri gătirea. "
            "Efecte: păstrează culoarea vibrantă (clorofila rămâne stabilă), "
            "textura rămâne crocantă, se elimină amărăciunea, se distrug enzimele oxidative. "
            "Esențial pentru spanac în Palak Paneer, fasole verde în salate, broccoli înainte de congelare."
        ),
        "keywords": ["oparire", "opărit", "blanching", "blanched", "apa clocotita gheata"],
    },
    "reduction": {
        "ro": "reducție", "emoji": "⬇️",
        "explanation": (
            "Reducția concentrează aromele prin evaporarea lichidului la foc mediu-mare, "
            "fără capac. Pe măsură ce apa se evaporă, zaharurile, proteinele și aromele "
            "se concentrează, creând sosuri mai dense și mai intense. "
            "Regulă: vinul se reduce la jumătate înainte de a adăuga bulionul. "
            "Sosul teriyaki, reducția de balsamic, glazura de vin — toate folosesc această tehnică. "
            "Nu grăbi procesul cu foc mare: riscul de ardere crește exponențial."
        ),
        "keywords": ["reductie", "reducție", "reduction", "reduce", "ingrosat", "concentrat"],
    },
    "caramelization": {
        "ro": "caramelizare", "emoji": "",
        "explanation": (
            "Caramelizarea este oxidarea termică a zaharurilor la 160–180°C, producând "
            "sute de compuși aromatici noi cu note de unt, nucă, vanilie și amărăciune complexă. "
            "Diferă de reacția Maillard (care implică proteine + zaharuri). "
            "Ceapa caramelizată necesită 45–60 minute la foc mic — orice scurtătură produce "
            "ceapă moale și transpirată, nu caramelizată. Supa de ceapă franceză și "
            "bulgurul cu ceapă demonstrează cât de transformatoare poate fi răbdarea."
        ),
        "keywords": ["caramelizare", "caramelizat", "caramelization", "caramel", "zahar ars", "ceapa caramelizata"],
    },
    "maillard": {
        "ro": "reacția Maillard", "emoji": "",
        "explanation": (
            "Reacția Maillard este o reacție chimică între aminoacizi și zaharuri reducătoare "
            "la 140–165°C, creând sute de compuși aromatici ce dau nota de 'prăjit', "
            "crustă brună și arome complexe. Este responsabilă pentru: crusta pâinii, "
            "culoarea cărnii prăjite, nota de cafea prăjită, ciocolata temperată. "
            "CRITIC: tigaia trebuie să fie uscată și carnea uscată cu prosop — umiditatea "
            "scade temperatura sub 100°C și produce abur în loc de rumenire."
        ),
        "keywords": ["maillard", "reactia maillard", "rumenire", "crusta", "brun", "prajit"],
    },
    "tempering": {
        "ro": "temperare condimente", "emoji": "️",
        "explanation": (
            "Temperarea (tadka/tempering) este tehnica indiană de a înflori condimentele "
            "în grăsime fierbinte (unt clarificat, ulei) pentru a elibera compușii "
            "liposolubili. Semințele de chimen 'pocnesc' în 30 secunde — semnalul că sunt gata. "
            "Se toarnă apoi totul fierbinte peste mâncare (dal, iaurt, supe). "
            "Ordinea contează: semințe întregi → ceapă → usturoi → condimente măcinate. "
            "Condimentele măcinate se adaugă ultimele — se ard cel mai rapid."
        ),
        "keywords": ["temperare", "tadka", "tempering", "condimente in ulei", "inflorit condimente", "blooming"],
    },
    "deglazing": {
        "ro": "dezglasat", "emoji": "",
        "explanation": (
            "Dezglasarea (deglazing) adaugă lichid (vin, bulion, oțet, suc de citrice) "
            "într-o tigaie fierbinte după rumenire pentru a dizolva 'fondul' — "
            "resturile caramelizate lipite de fund. Fondul conține flavor-uri intense "
            "din reacțiile Maillard și este BAZA oricărui sos bun. "
            "Nu irosi niciodată o tigaie cu fond maro! "
            "Când adaugi lichidul, zgomotul sffâcâit și aburul sunt normale — "
            "temperaturiie diferite creează dezglasarea instantanee."
        ),
        "keywords": ["dezglasat", "deglazing", "deglaze", "fond", "resturi tigaie", "vin in tigaie"],
    },
    "confit": {
        "ro": "confit", "emoji": "",
        "explanation": (
            "Confit-ul gătește ingredientele COMPLET IMERSATE în grăsime la temperatură joasă "
            "(70–90°C) pentru o perioadă lungă. Rața confit se gătește în propria grăsime "
            "3–4 ore — rezultatul este carne incredibil de fragedă, care se desprinde de pe os. "
            "Tehnica a apărut inițial ca metodă de conservare (înainte de frigider). "
            "Cartofi confit în ulei de măsline la 90°C = cei mai cremoși cartofi posibili. "
            "Usturoi confit în ulei = pastă dulce, mătăsoasă, fără iuțeala crudului."
        ),
        "keywords": ["confit", "confitat", "grasime", "ulei scufundat", "rata confit", "usturoi confit"],
    },
    "poaching": {
        "ro": "braconat / poșare", "emoji": "",
        "explanation": (
            "Poșarea gătește delicate alimente (ouă, pește, pui) în lichid la 71–82°C "
            "— sub punctul de fierbere. Bulele mici pe fund indică temperatura corectă. "
            "Ouă poșate: apă cu oțet (reduce împrăștierea albușului), vârtej cu lingura, "
            "ou crud scufundat 3–4 minute. "
            "Pui poșat în vin alb cu ierburi: cel mai umed piept de pui posibil. "
            "Somon poșat în bulion de legume: fraged și cu aromele bulionului absorbite."
        ),
        "keywords": ["posare", "poșare", "poaching", "posat", "braconate", "oua posate"],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE BASE: substituții ingrediente
# ─────────────────────────────────────────────────────────────────────────────
SUBSTITUTIONS: dict[str, dict] = {
    "eggs": {
        "ro": "ouă", "emoji": "",
        "subs": [
            {"sub": "Ou de in (flax egg)", "ratio": "1 lingură semințe de in măcinate + 3 linguri apă = 1 ou", "best_for": "prăjituri, muffins, burgeri vegani"},
            {"sub": "Ou de chia", "ratio": "1 lingură semințe chia + 3 linguri apă = 1 ou", "best_for": "prăjituri dense, pâine"},
            {"sub": "Piure de banană", "ratio": "1/4 banană = 1 ou", "best_for": "muffins, pancakes — adaugă dulceață"},
            {"sub": "Aquafaba (apa din năut)", "ratio": "3 linguri = 1 ou întreg; 2 linguri = 1 albuș", "best_for": "bezea, maioneza vegană, meringue"},
            {"sub": "Iaurt/lapte de cocos", "ratio": "1/4 cană = 1 ou", "best_for": "prăjituri umede"},
        ],
    },
    "butter": {
        "ro": "unt", "emoji": "",
        "subs": [
            {"sub": "Ulei de cocos", "ratio": "1:1", "best_for": "prăjituri, biscuiți, sosuri"},
            {"sub": "Ulei de măsline", "ratio": "3/4 din cantitate", "best_for": "preparate sărate, sotare"},
            {"sub": "Avocado piure", "ratio": "1:1", "best_for": "prăjituri întunecate (ciocolată)"},
            {"sub": "Unt vegan (Violife, etc)", "ratio": "1:1", "best_for": "orice rețetă cu unt"},
            {"sub": "Ghee", "ratio": "1:1", "best_for": "gătit la temperaturi înalte — punct de fum mai ridicat"},
        ],
    },
    "milk": {
        "ro": "lapte", "emoji": "",
        "subs": [
            {"sub": "Lapte de ovăz", "ratio": "1:1", "best_for": "sosuri, prăjituri, băuturi — cel mai neutru ca gust"},
            {"sub": "Lapte de migdale", "ratio": "1:1", "best_for": "deserturi, cereale"},
            {"sub": "Lapte de soia", "ratio": "1:1", "best_for": "orice — conținut proteic similar laptelui"},
            {"sub": "Lapte de cocos (din cutie)", "ratio": "1:1", "best_for": "currye, sosuri cremoase"},
            {"sub": "Apă + 1 ling unt/ulei", "ratio": "1:1", "best_for": "urgențe în rețete sărate"},
        ],
    },
    "cream": {
        "ro": "smântână/frișcă", "emoji": "",
        "subs": [
            {"sub": "Lapte de cocos integral (din cutie)", "ratio": "1:1", "best_for": "currye, supe, deserturi"},
            {"sub": "Cashew cream (cashews înmuiate + blender)", "ratio": "1:1", "best_for": "paste, sosuri, deserturi"},
            {"sub": "Iaurt grecesc", "ratio": "1:1, adaugat off-heat", "best_for": "sosuri — nu fierbe, se taie"},
            {"sub": "Silken tofu mixat", "ratio": "1:1", "best_for": "supe cremoase, cheesecake"},
        ],
    },
    "parmesan": {
        "ro": "parmezan", "emoji": "",
        "subs": [
            {"sub": "Drojdie nutritivă (nutritional yeast)", "ratio": "3-4 linguri per 100g parmezan", "best_for": "paste, risotto, popcorn — gust umami similar"},
            {"sub": "Pecorino Romano", "ratio": "1:1", "best_for": "mai sărat — reduce sarea din rețetă"},
            {"sub": "Grana Padano", "ratio": "1:1", "best_for": "mai bland, mai ieftin"},
            {"sub": "Migdale + drojdie nutritivă + sare", "ratio": "blend 100g migdale + 4 ling drojdie + 1 ling sare", "best_for": "vegan, topping paste/salate"},
        ],
    },
    "flour": {
        "ro": "făină albă", "emoji": "",
        "subs": [
            {"sub": "Făină de migdale", "ratio": "1:1 în cele mai multe cazuri", "best_for": "prăjituri umede, fără gluten"},
            {"sub": "Făină de ovăz (oats mixate)", "ratio": "1:1", "best_for": "prăjituri, biscuiți, pancakes"},
            {"sub": "Făină de orez", "ratio": "1:1", "best_for": "batter-uri ușoare, fără gluten"},
            {"sub": "Amidon de porumb (îngroșare)", "ratio": "1 ling amidon = 2 ling făină", "best_for": "sosuri, supe, nu baking"},
        ],
    },
    "bacon": {
        "ro": "bacon", "emoji": "",
        "subs": [
            {"sub": "Tempeh afumat (afumat cu fum lichid + soia)", "ratio": "1:1", "best_for": "cel mai aproape de texture"},
            {"sub": "Ciuperci king oyster (prăjite la uscat)", "ratio": "felii subțiri", "best_for": "texture crocantă similară"},
            {"sub": "Cocos chips uscate + soia + fum lichid", "ratio": "50g cocos = bacon strips", "best_for": "salate, BLT vegan"},
            {"sub": "Prosciutto / Pancetta", "ratio": "1:1", "best_for": "dacă nu e nevoie de vegan — mai fin"},
        ],
    },
    "honey": {
        "ro": "miere", "emoji": "",
        "subs": [
            {"sub": "Sirop de arțar (maple syrup)", "ratio": "3/4 din cantitate", "best_for": "aproape identic în baking"},
            {"sub": "Sirop de agave", "ratio": "3/4 din cantitate", "best_for": "mai neutru, se dizolvă mai ușor"},
            {"sub": "Sirop de dată", "ratio": "1:1", "best_for": "smoothies, deserturi cu gust caramelizat"},
            {"sub": "Zahăr brun + apă", "ratio": "1 ling zahăr + 1/4 ling apă = 1 ling miere", "best_for": "urgențe la gătit"},
        ],
    },
    "wine": {
        "ro": "vin alb/roșu pentru gătit", "emoji": "",
        "subs": [
            {"sub": "Bulion de legume + 1 ling oțet de vin alb", "ratio": "1:1", "best_for": "vin alb în risotto, sosuri"},
            {"sub": "Suc de struguri alb/roșu + oțet", "ratio": "3/4 suc + 1/4 oțet", "best_for": "fructat, pentru braise"},
            {"sub": "Apă + 1-2 ling oțet balsamic", "ratio": "1:1", "best_for": "pentru vin roșu în sosuri"},
            {"sub": "Suc de mere", "ratio": "1:1", "best_for": "vin alb în porc, pui"},
        ],
    },
    "soy sauce": {
        "ro": "sos de soia", "emoji": "",
        "subs": [
            {"sub": "Tamari (fără gluten)", "ratio": "1:1", "best_for": "identic, fără grâu"},
            {"sub": "Coconut aminos", "ratio": "1:1, mai dulce", "best_for": "soia-free, paleo"},
            {"sub": "Worcestershire sauce", "ratio": "1:1", "best_for": "mai complex, conține anșoa"},
            {"sub": "Miso + apă", "ratio": "1 ling miso + 1 ling apă = 2 ling sos soia", "best_for": "umami mai profund"},
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE BASE: sfaturi generale gătit
# ─────────────────────────────────────────────────────────────────────────────
COOKING_TIPS_GENERAL: list[dict] = [
    {"tip": "Sărează apa de paste până gustă ca marea. Sub-sărarea pastelor este cea mai comună greșeală din bucătărie.", "emoji": ""},
    {"tip": "Lasă carnea să ajungă la temperatura camerei 30 minute înainte de a o găti. Vei obține o gătire mai uniformă.", "emoji": ""},
    {"tip": "Nu aglomera tigaia! Dacă pui prea multe ingrediente, temperatura scade și se fierbe în loc să se prăjească.", "emoji": ""},
    {"tip": "Rezervă întotdeauna apă de paste înainte de a scurge. Amidonul din ea leagă sosul perfect.", "emoji": ""},
    {"tip": "Condimentele se adaugă în straturi, nu doar la final. Gustă și ajustează pe parcurs.", "emoji": "️"},
    {"tip": "O tigaie reală de fontă neagră (cast iron) va fi cel mai bun produs din bucătăria ta. Durează toată viața.", "emoji": ""},
    {"tip": "Acidul (lămâie, oțet) adăugat la final luminează ORICE fel de mâncare. E magia secretă a restaurantelor.", "emoji": ""},
    {"tip": "Lasă carnea să se odihnească după gătire: 5 min pentru pui, 10 min pentru friptură. Sucurile se redistribuie.", "emoji": "⏳"},
    {"tip": "Cumpără un cuțit de bucătărie bun și ascuțit-l lunar. Un cuțit bun schimbă complet experiența gătitului.", "emoji": ""},
    {"tip": "Gătitul unui risotto bun = 18 minute de amestecat + răbdare. Nu există scurtătură pentru asta.", "emoji": ""},
]

# ─────────────────────────────────────────────────────────────────────────────
# INTENT PATTERNS (regex în română + engleză)
# ─────────────────────────────────────────────────────────────────────────────
INTENT_PATTERNS: list[tuple] = [
    # find_recipe: "ce pot face cu X" / "am X în casă" / "folosesc X"
    (r"(ce pot|ce poti|ce putem|ce sa|cum sa) (face|gati|pregati|fac|faci|gatim|combina|combini).+cu (.+)", "find_recipe"),
    (r"(am|avem|folosesc|folosim) (.+) (acasa|la mine|disponibil|si nu stiu)", "find_recipe"),
    (r"(ingrediente?|ce fac cu|reteta? cu) (.+)", "find_recipe"),
    (r"reteta? (noua|inventata|creativa) cu (.+)", "find_recipe"),
    (r"(foloseste|include[sz]?|care contine) (.+)", "find_recipe"),

    # recipe_info: "cum fac X" / "rețeta de X"
    (r"(cum fac|cum se face|cum prepari?|cum gatesti?|prepara|fa[- ]mi) (.+)", "recipe_info"),
    (r"(reteta? (de|pentru|la)|recipe for) (.+)", "recipe_info"),
    (r"(explica[- ]mi|arata[- ]mi|da[- ]mi) (reteta?|prepararea?) (.+)", "recipe_info"),
    (r"pas (cu pas|by step).+?(pentru|de) (.+)", "recipe_info"),

    # technique_info: "ce este X" / "explică tehnica X"
    (r"(ce este|ce[- ]i cu|ce inseamna|explica[- ]?mi|cum functioneaza|ce face|ce e) (.+)", "technique_info"),
    (r"tehnica? (de )?(de )?(brasare|brezare|sotare|wok|confit|emulsionare|maillard|blanching|braising|reduction|caramelizare|temperare|poaching|deglazing)", "technique_info"),

    # substitution: "înlocuiesc X" / "ce pun în loc de X"
    (r"(inlocuiesc|inlocui|in loc de|alternativa (la|pentru)|substitut (la|pentru)|fara|nu am) (.+)", "substitution"),
    (r"ce (pun|bag|folosesc) in loc de (.+)", "substitution"),
    (r"(.+) (se poate inlocui|pot inlocui cu)", "substitution"),

    # dietary filter
    (r"(retete?|ceva|mancare|faza) (vegan|vegetarian|fara gluten|fara lactate|fara carne|pescatarian|keto|paleo)", "dietary_filter"),
    (r"(vegan|vegetarian|plant.?based|fara gluten|dairy.?free|gluten.?free)", "dietary_filter"),

    # time filter
    (r"(ceva |reteta? |mancare )?(rapid|repede|grabita?|quick|fast|simplu|sub|maxim) ?(\d+)? ?(min|minute|ore?)?", "time_filter"),
    (r"(sub|maxim|cel mult|in) (\d+) (minute|min|ore?)", "time_filter"),

    # cuisine filter
    (r"(retete?|ceva|mancare|bucatarie) (italian[ae]?|thai|indian[ae]?|japonez[ae]?|chinez[ae]?|mexican[ae]?|french?|francez[ae]?|coreean[ae]?|mediteranean[ae]?|oriental[ae]?|middle eastern|american[ae]?)", "cuisine_filter"),
    (r"(italian[ae]?|thai|indian[ae]?|japonez[ae]?|chinez[ae]?|mexican[ae]?|french?|francez[ae]?|coreean[ae]?|mediteranean[ae]?) (food|mancare|retete?|bucatarie)?", "cuisine_filter"),

    # random
    (r"(surprinde[- ]?ma|surprinde|aleatorie?|random|altceva|altceva|nu stiu|nu ma decid|orice|indiferent)", "random_recipe"),

    # help
    (r"(ajutor|help|ce poti|ce stii|ce faci|functii|comenzi|capabil)", "help"),

    # chitchat
    (r"(buna|salut|hello|hi|hey|bine ai venit)", "chitchat_greet"),
    (r"(multumesc|mersi|thanks|thank you|super|grozav|misto|fain|bravo)", "chitchat_thanks"),
    (r"(cine esti|ce esti|despre tine|cum te cheama|name|who are you)", "chitchat_identity"),
    (r"(pa|la revedere|bye|goodbye|seeya)", "chitchat_bye"),
]

# ─────────────────────────────────────────────────────────────────────────────
# CUISINE MAP (RO → EN key used in DB)
# ─────────────────────────────────────────────────────────────────────────────
CUISINE_MAP: dict[str, str] = {
    "italian": "Italian", "italiana": "Italian", "italiene": "Italian", "italiana": "Italian",
    "thai": "Thai", "thailand": "Thai",
    "indian": "Indian", "indiana": "Indian", "indiene": "Indian",
    "chinez": "Chinese", "chineza": "Chinese", "chineze": "Chinese", "chinese": "Chinese",
    "japonez": "Japanese", "japoneza": "Japanese", "japoneze": "Japanese", "japanese": "Japanese",
    "coreean": "Korean", "coreana": "Korean", "coreene": "Korean", "korean": "Korean",
    "mexican": "Mexican", "mexicana": "Mexican", "mexicane": "Mexican",
    "francez": "French", "franceza": "French", "franceze": "French", "french": "French",
    "mediteranean": "Mediterranean", "mediteraneana": "Mediterranean", "mediterranean": "Mediterranean",
    "american": "American", "americana": "American", "americane": "American",
    "oriental": "Middle Eastern", "orientala": "Middle Eastern", "middle eastern": "Middle Eastern",
    "vietnamese": "Vietnamese", "vietnamez": "Vietnamese",
}


# ─────────────────────────────────────────────────────────────────────────────
# ROMANIAN TO ENGLISH TRANSLATION MAP
# ─────────────────────────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────────────────────
# CHATBOT ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class RecipeChatbot:
    """
    RAG Chatbot fără LLM.
    Combină pattern matching pentru intenție cu retrieval RAG pentru conținut.
    """

    def __init__(self, rag_engine, agent=None):
        self.rag = rag_engine
        self.agent = agent
        self.compiled = [(re.compile(p, re.IGNORECASE), intent) for p, intent in INTENT_PATTERNS]

    # ── Detect intent ─────────────────────────────────────────────────────────
    def _detect_intent(self, message: str) -> tuple[str, re.Match | None]:
        for pattern, intent in self.compiled:
            m = pattern.search(message)
            if m:
                return intent, m
        return "unknown", None

    # ── Extract ingredients from message ──────────────────────────────────────
    def _extract_ingredients(self, message: str) -> list[str]:
        """Simple heuristic: split on common separators and clean stopwords."""
        STOPWORDS = {
            "ce", "cu", "si", "sau", "am", "la", "de", "un", "o", "al", "in", "pe",
            "din", "pentru", "mai", "ca", "pot", "fac", "am", "face", "faci", "avem",
            "acasa", "disponibil", "putin", "mult", "ceva", "reteta", "gatesc", "gatim",
            "ingrediente", "folosesc", "am", "niste", "cateva",
        }
        clean = re.sub(r'[?!.,;:]', ' ', message.lower())
        tokens = [t.strip() for t in re.split(r'[\s,;/]+|\bși\b|\bsi\b', clean) if len(t.strip()) > 2]
        result = [t for t in tokens if t not in STOPWORDS]
        return result[:8]  # max 8 ingredients from chat

    # ── Extract recipe name from message ──────────────────────────────────────
    def _extract_dish_name(self, message: str) -> str:
        patterns = [
            r"cum fac (.+?)[\?!.]?$",
            r"cum se face (.+?)[\?!.]?$",
            r"reteta? de (.+?)[\?!.]?$",
            r"reteta? pentru (.+?)[\?!.]?$",
            r"reteta? la (.+?)[\?!.]?$",
            r"prepara (.+?)[\?!.]?$",
            r"fa[- ]mi (.+?)[\?!.]?$",
        ]
        for p in patterns:
            m = re.search(p, message.lower())
            if m:
                return m.group(1).strip()
        return ""

    # ── Extract technique from message ────────────────────────────────────────
    def _extract_technique(self, message: str) -> str | None:
        msg_lower = message.lower()
        for key, data in TECHNIQUES.items():
            kws = data.get("keywords", []) + [key, data.get("ro", "")]
            if any(kw in msg_lower for kw in kws):
                return key
        return None

    # ── Extract substitution target ───────────────────────────────────────────
    def _extract_sub_target(self, message: str) -> str | None:
        def stems_match(w1: str, w2: str) -> bool:
            def stem(w):
                w = w.lower().strip()
                w = w.replace("ă", "a").replace("â", "a").replace("î", "i").replace("ș", "s").replace("ț", "t")
                return w[:3]
            return stem(w1) == stem(w2) and len(w1) >= 2 and len(w2) >= 2

        msg_lower = message.lower()
        patterns = [
            r"in loc de (.+?)[\?!.,]?$",
            r"inlocuiesc (.+?) cu",
            r"inlocuiesc (.+?)[\?!.,]?$",
            r"inlocuitor pentru (.+?)[\?!.,]?$",
            r"fara (.+?)[\?!.,]?$",
            r"nu am (.+?)[\?!.,]?$",
            r"alternativa la (.+?)[\?!.,]?$",
        ]
        for p in patterns:
            m = re.search(p, msg_lower)
            if m:
                candidate = m.group(1).strip()
                # Match to substitution keys
                for key, data in SUBSTITUTIONS.items():
                    ro_name = data.get("ro", "").lower()
                    if key in candidate or ro_name in candidate or candidate in key or stems_match(candidate, ro_name) or stems_match(candidate, key):
                        return key
                # Try partial match
                for key in SUBSTITUTIONS:
                    if any(w in candidate for w in key.split()):
                        return key
        
        # Fallback: scan for any substitution ingredient in raw text
        for word in msg_lower.split():
            # Clean word
            w_clean = re.sub(r'[?!.,;:]', '', word)
            for key, data in SUBSTITUTIONS.items():
                ro_name = data.get("ro", "").lower()
                if stems_match(w_clean, ro_name) or stems_match(w_clean, key) or w_clean == ro_name or w_clean == key:
                    return key
        return None

    # ── Extract time limit ────────────────────────────────────────────────────
    def _extract_time(self, message: str) -> int | None:
        m = re.search(r'(\d+)\s*(min|minute|ore?)', message.lower())
        if m:
            val = int(m.group(1))
            unit = m.group(2)
            return val * 60 if 'or' in unit else val
        if 'rapid' in message.lower() or 'repede' in message.lower():
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
                "text": " Salut! Sunt **Chef Bot RAG** — un chatbot culinar care funcționează 100% fără LLM! "
                        "Pot să-ți găsesc rețete, să explic tehnici culinare, să sugerez substituții "
                        "și să inventez rețete noi din ingredientele tale. Ce gătim azi?",
                "suggestions": ["Ce pot face cu pui și usturoi?", "Explică-mi ce este braising", "Rețete vegane rapide", "Surprinde-mă!"],
            }

        if intent == "chitchat_thanks":
            responses = [
                " Cu plăcere! Mai ai întrebări culinare?",
                " Mă bucur că a ajutat! Poftă bună!",
                "‍ La dispoziție! Spune-mi ce mai gătești!",
            ]
            return {"type": "text", "text": random.choice(responses), "suggestions": ["Mai vreau o rețetă", "Altă tehnică culinară"]}

        if intent == "chitchat_identity":
            return {
                "type": "text",
                "text": " Sunt **Chef Bot RAG** — un chatbot culinar construit fără niciun LLM! "
                        "Funcționez prin:\n"
                        "• **Detectare intenție** cu regex și keywords\n"
                        "• **Retrieval RAG** cu BM25 + TF-IDF bigramic\n"
                        "• **Baze de cunoștințe** hardcodate pentru tehnici și substituții\n"
                        "• **Query expansion** cu sinonime de ingrediente\n\n"
                        "Nu știu să generez text nou — doar să GĂSESC și să ORGANIZEZ informațiile din baza de date!",
                "suggestions": ["Cum funcționează RAG?", "Ce rețete ai?"],
            }

        if intent == "chitchat_bye":
            return {"type": "text", "text": " La revedere! Poftă bună la gătit! ️", "suggestions": []}

        # ── Help ──────────────────────────────────────────────────────────────
        if intent == "help":
            return {
                "type": "help",
                "text": "‍ **Pot să te ajut cu:**",
                "capabilities": [
                    {"icon": "", "title": "Găsesc rețete după ingrediente", "example": "Ce pot face cu pui, usturoi și lămâie?"},
                    {"icon": "", "title": "Explic orice rețetă din baza de date", "example": "Cum fac carbonara?"},
                    {"icon": "", "title": "Explic tehnici culinare", "example": "Ce este tehnica wok hei?"},
                    {"icon": "", "title": "Sugerez substituții de ingrediente", "example": "Ce pun în loc de ouă?"},
                    {"icon": "", "title": "Filtrez după bucătărie/dietă/timp", "example": "Rețete vegane sub 30 minute"},
                    {"icon": "", "title": "Îți surprind cu o rețetă aleatorie", "example": "Surprinde-mă!"},
                    {"icon": "", "title": "Dau sfaturi generale de gătit", "example": "Dă-mi un sfat culinar"},
                ],
            }

        # ── Find recipe by ingredients ────────────────────────────────────────
        if intent == "find_recipe":
            ings = self._extract_ingredients(message)
            if not ings:
                return {
                    "type": "text",
                    "text": " Nu am reușit să extrag ingrediente din mesajul tău. "
                            "Încearcă: **'Ce pot face cu pui, usturoi și lămâie?'**",
                    "suggestions": ["Ce pot face cu pui și usturoi?", "Rețetă cu ouă și spanac"],
                }
            
            # Translate ingredients to English for indexing compatibility
            translated_ings = [RO_TO_EN.get(i, i) for i in ings]
            
            agent_logs = []
            if self.agent:
                agent_res = self.agent.run_agentic_retrieval(translated_ings, filters={"cuisine": "Any", "difficulty": "Any"})
                recipes = agent_res["recipes"]
                agent_logs = agent_res["logs"]
            else:
                query_str = " ".join(translated_ings)
                recipes = self.rag.retrieve(query=query_str, top_k=3)
                agent_logs = [f"Retrieval run for query: {query_str}"]

            if not recipes:
                return {
                    "type": "text",
                    "text": f" Nu am găsit rețete cu **{', '.join(ings)}**. Încearcă alte ingrediente!",
                    "suggestions": ["Rețete cu pui", "Rețete vegetariene"],
                    "agent_logs": agent_logs
                }
            
            from recipe_generator import invent_recipes
            invented = invent_recipes(user_ingredients=translated_ings, retrieved_recipes=recipes, num_recipes=min(3, len(recipes)))
            
            return {
                "type": "recipes",
                "text": f" Am adaptat **{len(invented)} rețete** pentru tine bazate pe ingredientele cerute:",
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
                    "text": " Spune-mi ce rețetă cauți! Ex: **'Cum fac carbonara?'**",
                    "suggestions": ["Cum fac risotto?", "Rețeta de pad thai", "Cum fac shakshuka?"],
                }
            
            translated_dish = " ".join([RO_TO_EN.get(w, w) for w in dish.lower().split()])
            
            recipes = self.rag.retrieve(query=translated_dish, top_k=1)
            if not recipes:
                return {
                    "type": "text",
                    "text": f" Nu am găsit rețeta pentru **{dish}** în baza de date. "
                            f"Încearcă să cauți cu ingredientele principale!",
                    "suggestions": [f"Ce pot face cu {dish}?", "Surprinde-mă!"],
                }
            
            from recipe_generator import invent_recipes
            base_recipe = recipes[0]
            invented = invent_recipes(user_ingredients=base_recipe.get("ingredients", [])[:3], retrieved_recipes=[base_recipe], num_recipes=1)
            full_rec = invented[0] if invented else base_recipe
            
            return {
                "type": "recipe_detail",
                "text": f" Am găsit cea mai potrivită rețetă pentru **{dish}**:",
                "recipe": full_rec,
                "agent_logs": [f"Căutare după preparat: '{translated_dish}' matches '{base_recipe.get('title')}' with score {base_recipe.get('hybrid_score', 0):.2f}"]
            }

        # ── Technique info ────────────────────────────────────────────────────
        if intent == "technique_info":
            tech_key = self._extract_technique(message)
            if tech_key and tech_key in TECHNIQUES:
                t = TECHNIQUES[tech_key]
                return {
                    "type": "technique",
                    "emoji": t["emoji"],
                    "title": f"{t['emoji']} {t['ro'].title()} ({tech_key})",
                    "text": t["explanation"],
                    "suggestions": [f"Rețetă care folosește {t['ro']}", "Altă tehnică culinară"],
                }
            # Generic unknown technique
            return {
                "type": "technique_list",
                "text": " **Tehnici culinare disponibile** în baza mea de cunoștințe:",
                "techniques": [
                    {"key": k, "ro": v["ro"], "emoji": v["emoji"]}
                    for k, v in TECHNIQUES.items()
                ],
                "suggestions": ["Ce este braising?", "Explică-mi wok hei", "Ce este emulsionarea?"],
            }

        # ── Substitution ──────────────────────────────────────────────────────
        if intent == "substitution":
            target = self._extract_sub_target(message)
            if target and target in SUBSTITUTIONS:
                s = SUBSTITUTIONS[target]
                return {
                    "type": "substitution",
                    "emoji": s["emoji"],
                    "title": f"{s['emoji']} Substituții pentru {s['ro']}",
                    "text": f"Iată **{len(s['subs'])} alternative** pentru {s['ro']}:",
                    "substitutions": s["subs"],
                    "suggestions": ["Ce pun în loc de lapte?", "Înlocuitor pentru unt", "Fără ouă în prăjituri"],
                }
            return {
                "type": "substitution_list",
                "text": " **Ingrediente cu substituții disponibile:**",
                "available": [
                    {"key": k, "ro": v["ro"], "emoji": v["emoji"]}
                    for k, v in SUBSTITUTIONS.items()
                ],
                "suggestions": ["Înlocuitor pentru ouă", "Ce pun în loc de unt?", "Fără parmezan"],
            }

        # ── Dietary filter ────────────────────────────────────────────────────
        if intent == "dietary_filter":
            msg_lower = message.lower()
            tag = None
            if any(w in msg_lower for w in ["vegan", "vegana", "vegane"]):
                tag, label = "vegan", "vegane "
            elif any(w in msg_lower for w in ["vegetarian", "vegetariana", "vegetariene"]):
                tag, label = "vegetarian", "vegetariene "
            elif any(w in msg_lower for w in ["gluten", "fara gluten"]):
                tag, label = None, "fără gluten "
            else:
                tag, label = "vegan", "sănătoase "

            ings = ["vegetable"] if tag == "vegan" else ["egg", "cheese"]
            recipes = self.rag.retrieve(query=" ".join(ings), top_k=10)
            if tag:
                recipes = [r for r in recipes if tag in r.get("tags", [])]
            recipes = recipes[:3]
            
            if not recipes:
                return {"type": "text", "text": f" Nu am găsit rețete {label} cu aceste criterii.", "suggestions": ["Rețete vegane simple", "Surprinde-mă!"]}
            
            from recipe_generator import invent_recipes
            invented = invent_recipes(user_ingredients=ings, retrieved_recipes=recipes, num_recipes=len(recipes))
            
            return {
                "type": "recipes",
                "text": f" **Rețete {label}** din baza de date:",
                "recipes": invented,
                "agent_logs": [f"Filtrare dietă: '{tag or 'gluten-free'}' pe rezultate RAG"]
            }

        # ── Time filter ───────────────────────────────────────────────────────
        if intent == "time_filter":
            max_t = self._extract_time(message) or 30
            recipes = self.rag.retrieve(query="quick fast easy", top_k=15)
            fast = [r for r in recipes if r.get("time_minutes", 999) <= max_t][:3]
            if not fast:
                return {
                    "type": "text",
                    "text": f" Nu am găsit rețete sub {max_t} minute. Încearcă 30 sau 45 minute!",
                    "suggestions": ["Rețete sub 30 minute", "Ceva rapid cu ouă"],
                }
            
            from recipe_generator import invent_recipes
            invented = invent_recipes(user_ingredients=["quick"], retrieved_recipes=fast, num_recipes=len(fast))
            
            return {
                "type": "recipes",
                "text": f" **Rețete rapide sub {max_t} minute:**",
                "recipes": invented,
                "agent_logs": [f"Filtrare timp: rețete sub {max_t} minute din vector index"]
            }

        # ── Cuisine filter ────────────────────────────────────────────────────
        if intent == "cuisine_filter":
            msg_lower = message.lower()
            cuisine_en = None
            for ro_term, en_term in CUISINE_MAP.items():
                if ro_term in msg_lower:
                    cuisine_en = en_term
                    break
            if not cuisine_en:
                return {
                    "type": "text",
                    "text": " Ce bucătărie preferi?",
                    "suggestions": ["Rețete italiene", "Rețete thai", "Rețete indiene", "Rețete japoneze", "Rețete mexicane"],
                }
            recipes = self.rag.retrieve(query="classic traditional cuisine", filters={"cuisine": cuisine_en}, top_k=3)
            if not recipes:
                return {
                    "type": "text",
                    "text": f" Nu am găsit rețete din bucătăria **{cuisine_en}** cu aceste criterii.",
                    "suggestions": ["Rețete italiene", "Surprinde-mă!"],
                }
            
            from recipe_generator import invent_recipes
            invented = invent_recipes(user_ingredients=["traditional"], retrieved_recipes=recipes, num_recipes=len(recipes))
            
            return {
                "type": "recipes",
                "text": f" **Rețete din bucătăria {cuisine_en}:**",
                "recipes": invented,
                "agent_logs": [f"Filtrare bucătărie: '{cuisine_en}'"]
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
                "text": f" Iată surpriza zilei!",
                "recipe": full_rec,
                "suggestions": ["Altă surpriză!", "Rețete similare"],
                "agent_logs": ["Rețetă aleatorie selectată din vector DB"]
            }

        # ── Unknown / fallback ────────────────────────────────────────────────
        tip = random.choice(COOKING_TIPS_GENERAL)
        return {
            "type": "unknown",
            "text": " Nu am înțeles întrebarea, dar am un sfat culinar pentru tine:",
            "tip": f"{tip['emoji']} {tip['tip']}",
            "suggestions": [
                "Ce pot face cu pui și usturoi?",
                "Explică-mi ce este braising",
                "Înlocuitor pentru ouă",
                "Rețete vegane rapide",
                "Ajutor",
            ],
        }

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _recipe_summary(self, r: dict) -> dict:
        return {
            "title":        r.get("title", ""),
            "cuisine":      r.get("cuisine", ""),
            "difficulty":   r.get("difficulty", ""),
            "time_minutes": r.get("time_minutes", 0),
            "servings":     r.get("servings", 4),
            "tags":         r.get("tags", [])[:3],
            "flavor_profile": r.get("flavor_profile", [])[:3],
            "ingredients":  r.get("ingredients", [])[:6],
            "score":        round(r.get("hybrid_score", r.get("score", 0)), 3),
        }

    def _recipe_full(self, r: dict) -> dict:
        return {
            "title":        r.get("title", ""),
            "cuisine":      r.get("cuisine", ""),
            "difficulty":   r.get("difficulty", ""),
            "time_minutes": r.get("time_minutes", 0),
            "servings":     r.get("servings", 4),
            "ingredients":  r.get("ingredients", []),
            "steps":        r.get("steps", []),
            "tags":         r.get("tags", []),
            "flavor_profile": r.get("flavor_profile", []),
            "description":  r.get("description", ""),
            "key_technique": r.get("key_technique", ""),
        }
