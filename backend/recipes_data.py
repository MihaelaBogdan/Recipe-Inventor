"""
recipes_data.py
---------------
60 hand-crafted base recipes across 8 cuisines.
generate_variations() expands them to 300+ total entries for rich RAG coverage.
"""

import copy
import re

# ─────────────────────────────────────────────────────────────────────────────
# BASE RECIPES  (60 entries)
# ─────────────────────────────────────────────────────────────────────────────
BASE_RECIPES = [
    # ── ITALIAN ──────────────────────────────────────────────────────────────
    {
        "id": 1, "title": "Spaghetti Carbonara", "cuisine": "Italian",
        "difficulty": "Medium", "time_minutes": 25, "servings": 4,
        "ingredients": ["spaghetti", "eggs", "pancetta", "parmesan cheese", "black pepper", "garlic"],
        "steps": [
            "Cook spaghetti in generously salted boiling water until al dente. Reserve 1 cup pasta water before draining.",
            "Fry pancetta with sliced garlic in a dry skillet over medium heat until golden and crispy, about 5 min.",
            "Whisk 3 whole eggs with 100 g grated parmesan and a very generous amount of cracked black pepper.",
            "Remove skillet from heat. Add drained pasta and toss to coat in the pancetta fat.",
            "Quickly pour the egg-parmesan mixture over the pasta while tossing constantly. Add pasta water splash by splash to create a glossy, creamy sauce—never let it scramble.",
            "Serve immediately in warm bowls, topped with extra parmesan and freshly cracked pepper.",
        ],
        "tags": ["pasta", "egg-based", "quick", "Roman", "no-cream"],
        "flavor_profile": ["rich", "savory", "creamy", "umami", "peppery"],
        "description": "Classic Roman pasta where eggs emulsify into a silky, cream-free sauce.",
        "key_technique": "emulsification", "protein_type": "pork",
    },
    {
        "id": 2, "title": "Margherita Pizza", "cuisine": "Italian",
        "difficulty": "Medium", "time_minutes": 45, "servings": 4,
        "ingredients": ["pizza dough", "tomato sauce", "fresh mozzarella", "fresh basil", "olive oil", "salt"],
        "steps": [
            "Preheat oven to 250 °C (480 °F) with a pizza stone or heavy baking sheet inside for 30 minutes.",
            "Stretch pizza dough into a thin 30 cm circle on a floured surface, leaving a thick border.",
            "Spread a thin layer of tomato sauce, leaving a 2 cm border for the crust.",
            "Tear fresh mozzarella and distribute evenly over the sauce.",
            "Slide pizza onto the hot stone and bake 8–10 minutes until crust is charred and cheese bubbles.",
            "Remove, immediately scatter fresh basil, drizzle with olive oil. Slice and serve.",
        ],
        "tags": ["pizza", "vegetarian", "baked", "Neapolitan"],
        "flavor_profile": ["fresh", "savory", "milky", "herbaceous"],
        "description": "The definitive Neapolitan pizza—three colours of the Italian flag in every slice.",
        "key_technique": "high-heat baking", "protein_type": "none",
    },
    {
        "id": 3, "title": "Mushroom Risotto", "cuisine": "Italian",
        "difficulty": "Hard", "time_minutes": 50, "servings": 4,
        "ingredients": ["arborio rice", "porcini mushrooms", "parmesan cheese", "white wine", "shallots", "butter", "vegetable broth", "garlic", "parsley", "olive oil"],
        "steps": [
            "Soak dried porcini in 300 ml hot water 20 min. Strain and reserve the soaking liquid.",
            "Sauté shallots and garlic in butter + olive oil over medium heat until translucent, about 4 min.",
            "Add arborio rice and toast 2 min, stirring constantly, until edges turn translucent.",
            "Pour in white wine and stir until fully absorbed.",
            "Add warm broth one ladle at a time, stirring constantly and waiting until absorbed before adding more—about 18–20 min total. Add porcini and their soaking liquid halfway through.",
            "Finish with a generous knob of butter and parmesan (mantecatura). Rest 2 min, garnish with parsley.",
        ],
        "tags": ["risotto", "vegetarian", "mushroom", "umami-rich"],
        "flavor_profile": ["earthy", "creamy", "umami", "savory"],
        "description": "The meditative Italian rice dish that rewards patience with extraordinary creaminess.",
        "key_technique": "gradual absorption", "protein_type": "none",
    },
    {
        "id": 4, "title": "Penne all'Arrabbiata", "cuisine": "Italian",
        "difficulty": "Easy", "time_minutes": 25, "servings": 4,
        "ingredients": ["penne pasta", "canned tomatoes", "garlic", "dried red chili", "olive oil", "parsley", "salt"],
        "steps": [
            "Cook penne in heavily salted boiling water until al dente.",
            "Sauté sliced garlic and crumbled dried red chilies in generous olive oil over medium heat, 2 min.",
            "Add crushed tomatoes, season with salt, and simmer 15 min until sauce thickens.",
            "Toss drained pasta in the spicy tomato sauce, adding pasta water if needed.",
            "Finish with fresh chopped parsley and a drizzle of good olive oil.",
        ],
        "tags": ["pasta", "vegan", "spicy", "quick", "Roman"],
        "flavor_profile": ["spicy", "tangy", "garlicky", "bright"],
        "description": "Rome's angriest pasta—simple, fiery, and absolutely addictive.",
        "key_technique": "sauce reduction", "protein_type": "none",
    },
    {
        "id": 5, "title": "Pasta Primavera", "cuisine": "Italian",
        "difficulty": "Easy", "time_minutes": 30, "servings": 4,
        "ingredients": ["spaghetti", "zucchini", "bell peppers", "cherry tomatoes", "garlic", "basil", "olive oil", "parmesan cheese", "lemon"],
        "steps": [
            "Cook spaghetti in salted boiling water until al dente.",
            "Sauté sliced zucchini and bell peppers in olive oil over high heat 5 min until lightly charred.",
            "Add garlic and cherry tomatoes, cook 3 more min until tomatoes blister.",
            "Toss in drained pasta, squeeze over lemon juice, add pasta water as needed.",
            "Finish with torn basil, grated parmesan, and a drizzle of olive oil.",
        ],
        "tags": ["pasta", "vegetarian", "spring", "colorful", "fresh"],
        "flavor_profile": ["fresh", "bright", "herbaceous", "light"],
        "description": "A celebration of spring vegetables tossed with pasta in a light olive oil sauce.",
        "key_technique": "high-heat sauté", "protein_type": "none",
    },
    {
        "id": 6, "title": "Fettuccine Alfredo", "cuisine": "Italian",
        "difficulty": "Easy", "time_minutes": 20, "servings": 4,
        "ingredients": ["fettuccine", "butter", "parmesan cheese", "black pepper", "garlic"],
        "steps": [
            "Cook fettuccine in heavily salted water until al dente. Reserve 2 cups pasta water.",
            "Melt butter in a large skillet with minced garlic over low heat.",
            "Add pasta and a big splash of pasta water; toss vigorously.",
            "Add parmesan gradually while tossing and adding water until a creamy emulsified sauce forms.",
            "Season with cracked black pepper and serve immediately with extra parmesan.",
        ],
        "tags": ["pasta", "vegetarian", "creamy", "indulgent", "quick"],
        "flavor_profile": ["buttery", "rich", "creamy", "savory"],
        "description": "Rome's butter-and-parmesan pasta—three ingredients, infinite comfort.",
        "key_technique": "emulsification", "protein_type": "none",
    },
    {
        "id": 7, "title": "Ribollita Toscana", "cuisine": "Italian",
        "difficulty": "Medium", "time_minutes": 60, "servings": 6,
        "ingredients": ["cannellini beans", "kale", "stale bread", "canned tomatoes", "onion", "carrot", "celery", "garlic", "olive oil", "rosemary", "vegetable broth"],
        "steps": [
            "Sauté diced onion, carrot, and celery in olive oil for 8 min (soffritto).",
            "Add garlic, rosemary, and tomatoes. Cook 5 min.",
            "Add cannellini beans and broth. Simmer 20 min.",
            "Add chopped kale and torn stale bread. Simmer 15 more min, stirring often—the bread should dissolve into the soup.",
            "The soup should be very thick, almost porridge-like. Season generously.",
            "Serve drizzled with the best olive oil you have.",
        ],
        "tags": ["soup", "vegan", "Tuscan", "hearty", "bread"],
        "flavor_profile": ["earthy", "hearty", "savory", "rustic"],
        "description": "Tuscany's iconic 'reboiled' bread-and-bean soup—humble peasant food elevated to art.",
        "key_technique": "slow braising", "protein_type": "legumes",
    },
    {
        "id": 8, "title": "Pesto alla Genovese Pasta", "cuisine": "Italian",
        "difficulty": "Easy", "time_minutes": 20, "servings": 4,
        "ingredients": ["spaghetti", "fresh basil", "pine nuts", "parmesan cheese", "garlic", "olive oil", "lemon"],
        "steps": [
            "Blend basil, pine nuts, garlic, and parmesan in a food processor while slowly streaming in olive oil.",
            "Season with lemon juice and salt. Do not heat—pesto is served raw.",
            "Cook spaghetti in salted boiling water until al dente.",
            "Toss drained pasta with pesto, loosening with pasta water until silky.",
            "Serve with extra parmesan and a basil leaf.",
        ],
        "tags": ["pasta", "vegetarian", "no-cook sauce", "Genovese", "fresh"],
        "flavor_profile": ["herbaceous", "nutty", "bright", "savory"],
        "description": "Liguria's emerald sauce—basil, pine nuts, and parmesan in perfect harmony.",
        "key_technique": "cold emulsion", "protein_type": "none",
    },
    {
        "id": 9, "title": "Melanzane alla Parmigiana", "cuisine": "Italian",
        "difficulty": "Hard", "time_minutes": 90, "servings": 6,
        "ingredients": ["eggplant", "tomato sauce", "mozzarella", "parmesan cheese", "basil", "olive oil", "flour", "eggs"],
        "steps": [
            "Slice eggplant 1 cm thick, salt generously, rest 30 min, pat dry.",
            "Dredge in flour, dip in beaten egg, and pan-fry in olive oil until golden both sides.",
            "In a baking dish, layer: tomato sauce, fried eggplant, mozzarella, basil, parmesan. Repeat layers.",
            "Finish with a generous layer of parmesan on top.",
            "Bake at 180 °C for 35 min until golden and bubbling.",
            "Rest 15 min before serving—it slices better and tastes even better warm.",
        ],
        "tags": ["baked", "vegetarian", "southern Italian", "comfort", "layered"],
        "flavor_profile": ["rich", "savory", "milky", "hearty"],
        "description": "Southern Italy's crown jewel—layers of fried eggplant, tomato, and bubbling cheese.",
        "key_technique": "layered baking", "protein_type": "none",
    },
    {
        "id": 10, "title": "Osso Buco Milanese", "cuisine": "Italian",
        "difficulty": "Hard", "time_minutes": 120, "servings": 4,
        "ingredients": ["veal shanks", "onion", "carrot", "celery", "white wine", "canned tomatoes", "beef broth", "garlic", "lemon zest", "parsley", "olive oil"],
        "steps": [
            "Tie veal shanks with kitchen twine. Season with salt, dredge in flour.",
            "Sear in a Dutch oven in olive oil over high heat until deeply browned all sides.",
            "Remove shanks. Sauté diced onion, carrot, and celery in same pan 8 min.",
            "Add wine, scraping up browned bits. Add tomatoes, broth, garlic. Return shanks.",
            "Cover and braise at 160 °C for 90 min until meat falls from bone.",
            "Mix lemon zest, garlic, and parsley for gremolata. Scatter over each shank before serving with saffron risotto.",
        ],
        "tags": ["braised", "veal", "Milanese", "special occasion", "slow-cooked"],
        "flavor_profile": ["rich", "deep", "savory", "wine-braised"],
        "description": "Milan's signature braised veal shank finished with bright lemon gremolata.",
        "key_technique": "braising", "protein_type": "veal",
    },

    # ── THAI ─────────────────────────────────────────────────────────────────
    {
        "id": 11, "title": "Pad Thai", "cuisine": "Thai",
        "difficulty": "Medium", "time_minutes": 25, "servings": 2,
        "ingredients": ["rice noodles", "shrimp", "eggs", "bean sprouts", "green onion", "peanuts", "tamarind paste", "fish sauce", "palm sugar", "garlic", "red chili"],
        "steps": [
            "Soak rice noodles in warm water 30 min until pliable. Mix tamarind, fish sauce, and palm sugar for the sauce.",
            "Heat wok over very high heat. Stir-fry shrimp and garlic in oil 2 min. Push to side.",
            "Scramble eggs in center of wok, breaking them up as they cook.",
            "Add noodles and sauce. Toss everything vigorously 3 min.",
            "Add bean sprouts and green onion. Toss 1 min.",
            "Serve topped with crushed peanuts, lime wedge, chili flakes, and extra fish sauce on the side.",
        ],
        "tags": ["noodles", "seafood", "Thai street food", "stir-fry"],
        "flavor_profile": ["tangy", "savory", "sweet", "nutty", "umami"],
        "description": "Thailand's beloved street noodles—perfect balance of sweet, sour, and savory.",
        "key_technique": "wok stir-fry", "protein_type": "seafood",
    },
    {
        "id": 12, "title": "Thai Green Curry", "cuisine": "Thai",
        "difficulty": "Medium", "time_minutes": 35, "servings": 4,
        "ingredients": ["chicken thighs", "coconut milk", "green curry paste", "eggplant", "zucchini", "Thai basil", "fish sauce", "palm sugar", "kaffir lime leaves", "bamboo shoots"],
        "steps": [
            "Fry green curry paste in a splash of coconut milk until very fragrant, about 3 min.",
            "Add remaining coconut milk and bring to a gentle simmer.",
            "Add chicken thighs and cook 15 min until cooked through.",
            "Add eggplant, zucchini, and bamboo shoots. Simmer 5 min.",
            "Season with fish sauce and palm sugar to balance flavors.",
            "Stir in Thai basil and kaffir lime leaves. Serve with jasmine rice.",
        ],
        "tags": ["curry", "Thai", "chicken", "coconut", "aromatic"],
        "flavor_profile": ["herby", "creamy", "spicy", "aromatic", "bright"],
        "description": "Thailand's vibrant green curry—herbal, coconut-rich, and fragrant with Thai basil.",
        "key_technique": "paste frying + coconut extraction", "protein_type": "chicken",
    },
    {
        "id": 13, "title": "Tom Yum Goong", "cuisine": "Thai",
        "difficulty": "Medium", "time_minutes": 30, "servings": 4,
        "ingredients": ["shrimp", "lemongrass", "galangal", "kaffir lime leaves", "mushrooms", "fish sauce", "lime juice", "red chili", "cilantro", "coconut milk"],
        "steps": [
            "Bruise lemongrass, galangal, and kaffir lime leaves. Simmer in 1 litre water 10 min.",
            "Add mushrooms and shrimp. Cook until shrimp turn pink, about 3 min.",
            "Season with fish sauce and lime juice. Add chili to taste.",
            "Stir in a splash of coconut milk for creaminess (Tom Kha variation).",
            "Remove lemongrass and galangal pieces. Garnish with cilantro and serve hot.",
        ],
        "tags": ["soup", "Thai", "seafood", "spicy", "aromatic"],
        "flavor_profile": ["sour", "spicy", "aromatic", "savory", "bright"],
        "description": "Thailand's electric hot-and-sour soup with fragrant aromatics and plump shrimp.",
        "key_technique": "aromatic infusion", "protein_type": "seafood",
    },

    # ── INDIAN ───────────────────────────────────────────────────────────────
    {
        "id": 14, "title": "Chicken Tikka Masala", "cuisine": "Indian",
        "difficulty": "Medium", "time_minutes": 50, "servings": 4,
        "ingredients": ["chicken breast", "yogurt", "canned tomatoes", "heavy cream", "garlic", "ginger", "garam masala", "cumin", "coriander", "turmeric", "paprika", "onion", "butter"],
        "steps": [
            "Marinate chicken in yogurt, garlic, ginger, and half the spices for at least 1 hour.",
            "Grill or broil marinated chicken until charred on the outside. Cut into chunks.",
            "Sauté onion in butter until deeply golden, 12 min. Add remaining garlic and ginger.",
            "Add all spices and cook 2 min until fragrant. Add tomatoes and simmer 15 min.",
            "Blend sauce until smooth. Return to pan, add cream, simmer 5 min.",
            "Add chicken tikka to the sauce and simmer 5 min. Serve with basmati rice and naan.",
        ],
        "tags": ["curry", "Indian", "chicken", "creamy", "aromatic"],
        "flavor_profile": ["rich", "creamy", "spiced", "tangy", "warming"],
        "description": "The world's most beloved curry—smoky tikka chicken in a velvety tomato-cream sauce.",
        "key_technique": "tandoor marination + sauce reduction", "protein_type": "chicken",
    },
    {
        "id": 15, "title": "Dal Tadka", "cuisine": "Indian",
        "difficulty": "Easy", "time_minutes": 35, "servings": 4,
        "ingredients": ["red lentils", "onion", "canned tomatoes", "garlic", "ginger", "cumin", "turmeric", "coriander", "butter", "red chili", "lemon", "cilantro"],
        "steps": [
            "Rinse red lentils and simmer with turmeric and water until completely soft, about 20 min.",
            "Make the tadka: heat butter in a small pan, fry cumin seeds until they pop.",
            "Add onion to tadka and cook until golden. Add garlic, ginger, and tomatoes.",
            "Add coriander and chili. Cook until tomatoes break down, about 8 min.",
            "Pour tadka over lentils and stir. Simmer together 5 min.",
            "Finish with lemon juice and fresh cilantro. Serve with rice or naan.",
        ],
        "tags": ["Indian", "lentils", "vegan", "protein-rich", "comfort"],
        "flavor_profile": ["earthy", "warming", "spiced", "tangy", "hearty"],
        "description": "India's soul food—creamy lentils hit with a sizzling spiced butter tadka.",
        "key_technique": "tadka (tempering spices)", "protein_type": "legumes",
    },
    {
        "id": 16, "title": "Palak Paneer", "cuisine": "Indian",
        "difficulty": "Medium", "time_minutes": 40, "servings": 4,
        "ingredients": ["paneer", "spinach", "onion", "canned tomatoes", "garlic", "ginger", "heavy cream", "garam masala", "cumin", "turmeric", "butter"],
        "steps": [
            "Blanch spinach in boiling water 2 min, then blend to a smooth purée.",
            "Fry paneer cubes in butter until golden on all sides. Set aside.",
            "Sauté onion until deep golden, 12 min. Add garlic and ginger.",
            "Add tomatoes and all spices. Cook until oil separates, about 10 min.",
            "Stir in spinach purée and simmer 10 min. Add cream.",
            "Fold in paneer cubes gently. Simmer 5 min and serve with naan.",
        ],
        "tags": ["Indian", "vegetarian", "paneer", "spinach", "creamy"],
        "flavor_profile": ["earthy", "creamy", "mildly spiced", "warming"],
        "description": "India's beloved cottage cheese in vibrant spiced spinach gravy.",
        "key_technique": "spice layering + vegetable purée", "protein_type": "dairy",
    },
    {
        "id": 17, "title": "Sweet Potato Coconut Curry", "cuisine": "Indian",
        "difficulty": "Easy", "time_minutes": 35, "servings": 4,
        "ingredients": ["sweet potato", "coconut milk", "chickpeas", "spinach", "red curry paste", "ginger", "garlic", "lime", "cilantro", "jasmine rice", "onion"],
        "steps": [
            "Sauté onion in oil until soft. Add garlic and ginger.",
            "Add red curry paste and fry 2 min until fragrant.",
            "Add diced sweet potatoes and coconut milk. Simmer 15 min until tender.",
            "Add chickpeas and simmer 5 more min.",
            "Stir in spinach until wilted. Season with lime juice and salt.",
            "Serve over jasmine rice topped with fresh cilantro and a lime wedge.",
        ],
        "tags": ["vegan", "curry", "sweet potato", "coconut", "easy"],
        "flavor_profile": ["creamy", "sweet", "spiced", "warming", "bright"],
        "description": "Velvety coconut curry with sweet potato and chickpeas—vegan comfort at its finest.",
        "key_technique": "paste frying + coconut simmering", "protein_type": "legumes",
    },

    # ── CHINESE ──────────────────────────────────────────────────────────────
    {
        "id": 18, "title": "Classic Egg Fried Rice", "cuisine": "Chinese",
        "difficulty": "Easy", "time_minutes": 15, "servings": 4,
        "ingredients": ["cooked rice", "eggs", "soy sauce", "garlic", "ginger", "peas", "carrot", "green onion", "sesame oil", "vegetable oil"],
        "steps": [
            "Use day-old cold rice—freshly cooked rice is too wet.",
            "Heat wok until smoking. Stir-fry diced carrot and peas 2 min. Add garlic and ginger.",
            "Push vegetables to side, scramble eggs in center until just set.",
            "Add rice and toss everything together vigorously 3–4 min over highest heat.",
            "Season with soy sauce and drizzle with sesame oil. Toss to combine.",
            "Scatter sliced green onion and serve immediately.",
        ],
        "tags": ["rice", "Chinese", "quick", "leftover rice", "wok"],
        "flavor_profile": ["savory", "smoky", "umami", "simple"],
        "description": "The ultimate fridge-cleaner—leftover rice transformed into golden, smoky perfection.",
        "key_technique": "wok hei", "protein_type": "eggs",
    },
    {
        "id": 19, "title": "Kung Pao Chicken", "cuisine": "Chinese",
        "difficulty": "Medium", "time_minutes": 30, "servings": 4,
        "ingredients": ["chicken breast", "peanuts", "dried red chili", "soy sauce", "Shaoxing wine", "Szechuan pepper", "garlic", "ginger", "rice vinegar", "sugar", "cornstarch", "green onion"],
        "steps": [
            "Marinate diced chicken in soy sauce, Shaoxing wine, and cornstarch for 15 min.",
            "Mix sauce: soy sauce, vinegar, sugar, and a cornstarch slurry. Set aside.",
            "Stir-fry dried chilies and Szechuan pepper in hot oil until fragrant but not burned.",
            "Add chicken and stir-fry until cooked through and golden.",
            "Add garlic and ginger, then pour in sauce. Toss until thickened.",
            "Add peanuts and green onion. Serve over steamed rice.",
        ],
        "tags": ["Chinese", "Sichuan", "spicy", "stir-fry", "peanuts"],
        "flavor_profile": ["spicy", "tangy", "sweet", "nutty", "numbing"],
        "description": "Sichuan's legendary stir-fry with the iconic ma la (numbing-spicy) sensation.",
        "key_technique": "velveting + wok toss", "protein_type": "chicken",
    },
    {
        "id": 20, "title": "Mapo Tofu", "cuisine": "Chinese",
        "difficulty": "Medium", "time_minutes": 25, "servings": 4,
        "ingredients": ["silken tofu", "ground pork", "doubanjiang", "soy sauce", "Szechuan pepper", "garlic", "ginger", "chili oil", "cornstarch", "green onion", "chicken broth"],
        "steps": [
            "Cut silken tofu into 2 cm cubes. Handle gently to avoid breaking.",
            "Fry ground pork in oil until browned and rendered.",
            "Add doubanjiang and cook until oil turns red, about 2 min.",
            "Add garlic and ginger. Pour in chicken broth and bring to simmer.",
            "Slide in tofu gently. Simmer 5 min to absorb flavors.",
            "Thicken with cornstarch slurry. Drizzle chili oil and grind Szechuan pepper on top. Garnish with green onion.",
        ],
        "tags": ["Chinese", "Sichuan", "tofu", "spicy", "numbing"],
        "flavor_profile": ["spicy", "numbing", "savory", "rich", "silky"],
        "description": "Sichuan's most electric dish—silky tofu in a fiery, numbing ma la sauce.",
        "key_technique": "ma la sauce building", "protein_type": "pork",
    },

    # ── JAPANESE ─────────────────────────────────────────────────────────────
    {
        "id": 21, "title": "Teriyaki Salmon", "cuisine": "Japanese",
        "difficulty": "Easy", "time_minutes": 20, "servings": 4,
        "ingredients": ["salmon fillets", "soy sauce", "mirin", "sake", "sugar", "ginger", "garlic", "sesame seeds", "green onion"],
        "steps": [
            "Mix soy sauce, mirin, sake, and sugar in a saucepan. Simmer until reduced by half and syrupy.",
            "Score salmon skin with a sharp knife. Season with salt.",
            "Sear salmon skin-side down in a hot non-stick pan 4 min until skin is crispy.",
            "Flip and cook 2 more min. Brush generously with teriyaki glaze.",
            "Caramelize under a high heat for 1 min.",
            "Serve over steamed rice with sesame seeds and sliced green onion.",
        ],
        "tags": ["Japanese", "salmon", "fish", "glazed", "quick"],
        "flavor_profile": ["sweet", "savory", "umami", "caramelized"],
        "description": "Glazed salmon with Japan's iconic sweet-savory teriyaki sauce.",
        "key_technique": "glaze reduction + searing", "protein_type": "fish",
    },
    {
        "id": 22, "title": "Miso Ramen", "cuisine": "Japanese",
        "difficulty": "Hard", "time_minutes": 90, "servings": 2,
        "ingredients": ["ramen noodles", "white miso paste", "pork broth", "chashu pork", "soft-boiled egg", "nori", "green onion", "corn", "butter", "sesame seeds", "bamboo shoots"],
        "steps": [
            "Make chashu: roll pork belly, tie, and braise in soy sauce, mirin, and sake for 2 hours. Slice and sear.",
            "Make marinated soft-boiled eggs: boil 6.5 min, peel, marinate in soy, mirin, and water overnight.",
            "Whisk miso paste with a small amount of hot pork broth until smooth. Add to main broth.",
            "Cook ramen noodles per package instructions.",
            "Ladle miso broth into bowls. Add noodles.",
            "Top with chashu, halved marinated egg, corn, bamboo shoots, nori, a pat of butter, sesame seeds, and green onion.",
        ],
        "tags": ["ramen", "Japanese", "pork", "noodles", "umami-bomb"],
        "flavor_profile": ["rich", "umami", "savory", "complex", "warming"],
        "description": "Hokkaido-style miso ramen—Japan's most warming bowl, rich with fermented soybean depth.",
        "key_technique": "layered broth building", "protein_type": "pork",
    },

    # ── KOREAN ───────────────────────────────────────────────────────────────
    {
        "id": 23, "title": "Korean Beef Bulgogi", "cuisine": "Korean",
        "difficulty": "Easy", "time_minutes": 30, "servings": 4,
        "ingredients": ["beef sirloin", "soy sauce", "sesame oil", "garlic", "ginger", "sugar", "green onion", "Asian pear", "sesame seeds", "steamed rice"],
        "steps": [
            "Slice beef very thinly (partially freeze for easier slicing). Blend pear, soy sauce, sesame oil, garlic, ginger, and sugar for marinade.",
            "Marinate beef for at least 30 min (overnight for best flavour).",
            "Cook in a very hot cast-iron pan in small batches to get caramelised edges.",
            "Each batch cooks in 2–3 min—don't crowd the pan.",
            "Scatter sesame seeds and green onions over the cooked beef.",
            "Serve over steamed rice with kimchi and banchan (Korean side dishes).",
        ],
        "tags": ["Korean", "beef", "marinated", "grilled", "BBQ"],
        "flavor_profile": ["sweet", "savory", "nutty", "garlicky", "caramelised"],
        "description": "Korea's iconic fire meat—thinly sliced, pear-marinated beef caramelised to perfection.",
        "key_technique": "high-heat caramelisation", "protein_type": "beef",
    },
    {
        "id": 24, "title": "Bibimbap", "cuisine": "Korean",
        "difficulty": "Medium", "time_minutes": 40, "servings": 2,
        "ingredients": ["steamed rice", "ground beef", "spinach", "carrot", "mushrooms", "zucchini", "egg", "gochujang", "sesame oil", "soy sauce", "garlic"],
        "steps": [
            "Prepare each vegetable separately: blanch spinach and season with sesame oil; julienne and stir-fry carrot; sauté mushrooms and zucchini with garlic.",
            "Cook ground beef with soy sauce and garlic until caramelised.",
            "Fry egg sunny-side up.",
            "Warm a stone bowl (dolsot) if available. Add rice as base.",
            "Arrange vegetables and beef in colourful sections around the bowl.",
            "Top with fried egg and a generous spoonful of gochujang. Mix everything before eating.",
        ],
        "tags": ["Korean", "rice bowl", "colourful", "balanced", "mixed"],
        "flavor_profile": ["savory", "spicy", "nutty", "earthy", "balanced"],
        "description": "Korea's iconic mixed bowl—rice crowned with colourful vegetables, beef, egg, and gochujang.",
        "key_technique": "individual component preparation", "protein_type": "beef",
    },

    # ── VIETNAMESE ───────────────────────────────────────────────────────────
    {
        "id": 25, "title": "Vietnamese Pho Bo", "cuisine": "Vietnamese",
        "difficulty": "Hard", "time_minutes": 180, "servings": 6,
        "ingredients": ["beef bones", "rice noodles", "beef sirloin", "bean sprouts", "Thai basil", "lime", "hoisin sauce", "star anise", "cinnamon", "cloves", "ginger", "onion", "fish sauce"],
        "steps": [
            "Char onion and ginger directly over flame until blackened—essential for broth depth.",
            "Blanch beef bones 5 min, discard water, rinse bones clean.",
            "Simmer cleaned bones with charred aromatics, star anise, cinnamon, and cloves for 3+ hours.",
            "Strain broth, season with fish sauce and salt.",
            "Soak rice noodles in warm water until soft. Slice beef paper-thin.",
            "Assemble bowls: noodles, raw beef slices (boiling broth will cook them), then ladle boiling broth over. Serve with bean sprouts, basil, lime, and hoisin on the side.",
        ],
        "tags": ["Vietnamese", "soup", "beef", "noodles", "slow-cooked"],
        "flavor_profile": ["clear", "deeply savory", "aromatic", "warming", "fresh"],
        "description": "Vietnam's soul-warming noodle soup—clarity of broth is its art form.",
        "key_technique": "long-extraction broth", "protein_type": "beef",
    },

    # ── MEDITERRANEAN ────────────────────────────────────────────────────────
    {
        "id": 26, "title": "Shakshuka", "cuisine": "Mediterranean",
        "difficulty": "Easy", "time_minutes": 30, "servings": 4,
        "ingredients": ["eggs", "canned tomatoes", "bell peppers", "onion", "garlic", "cumin", "smoked paprika", "red chili", "feta cheese", "olive oil", "parsley"],
        "steps": [
            "Sauté diced onion and bell peppers in olive oil over medium heat until softened, 8 min.",
            "Add garlic, cumin, paprika, and chili. Cook 2 min until fragrant.",
            "Add crushed tomatoes and simmer 10 min until sauce thickens.",
            "Create wells in the sauce and crack eggs into each well. Cover the pan.",
            "Cook until whites are just set but yolks remain runny, about 5–7 min.",
            "Crumble feta over the top, scatter fresh parsley, and serve from the pan with crusty bread.",
        ],
        "tags": ["eggs", "Mediterranean", "vegetarian", "one-pan", "breakfast"],
        "flavor_profile": ["tangy", "savory", "spiced", "bright", "rich"],
        "description": "Middle Eastern eggs poached in rich spiced tomato sauce—perfect at any meal.",
        "key_technique": "egg poaching in sauce", "protein_type": "eggs",
    },
    {
        "id": 27, "title": "Greek Moussaka", "cuisine": "Mediterranean",
        "difficulty": "Hard", "time_minutes": 120, "servings": 8,
        "ingredients": ["eggplant", "ground lamb", "canned tomatoes", "onion", "garlic", "cinnamon", "allspice", "red wine", "parmesan cheese", "butter", "flour", "whole milk", "eggs", "nutmeg"],
        "steps": [
            "Salt eggplant slices, rest 30 min, pat dry. Brush with olive oil and bake at 200 °C until golden.",
            "Brown ground lamb with onion and garlic. Add wine, tomatoes, cinnamon, and allspice. Simmer 20 min.",
            "Make béchamel: melt butter, whisk in flour, gradually add hot milk stirring constantly until thick. Season with nutmeg. Off heat, stir in beaten eggs.",
            "In a large baking dish: layer eggplant, meat sauce, eggplant, then pour béchamel over top.",
            "Sprinkle with parmesan and bake at 180 °C for 45 min until golden.",
            "Rest 20 min before cutting—essential for clean slices.",
        ],
        "tags": ["Greek", "lamb", "baked", "layered", "special occasion"],
        "flavor_profile": ["rich", "spiced", "creamy", "savory", "warming"],
        "description": "Greece's magnificent layered casserole—spiced lamb, silky eggplant, and cloud-like béchamel.",
        "key_technique": "layered baking + béchamel", "protein_type": "lamb",
    },
    {
        "id": 28, "title": "Spanakopita", "cuisine": "Mediterranean",
        "difficulty": "Medium", "time_minutes": 60, "servings": 8,
        "ingredients": ["spinach", "feta cheese", "eggs", "phyllo dough", "onion", "olive oil", "dill", "nutmeg"],
        "steps": [
            "Wilt spinach and squeeze out ALL excess water. Chop finely.",
            "Mix spinach with crumbled feta, beaten eggs, sautéed onion, dill, and a pinch of nutmeg.",
            "Brush a baking dish with olive oil. Layer 8 sheets of phyllo, brushing each with oil.",
            "Spread spinach-feta filling evenly. Top with 8 more phyllo sheets, each brushed with oil.",
            "Score top layers into diamonds before baking.",
            "Bake at 180 °C for 45 min until deeply golden and crisp. Cool 10 min before serving.",
        ],
        "tags": ["Greek", "vegetarian", "phyllo", "cheese", "baked"],
        "flavor_profile": ["savory", "herbaceous", "tangy", "flaky", "rich"],
        "description": "Greece's iconic spinach and feta pie encased in shatteringly crisp phyllo.",
        "key_technique": "phyllo layering", "protein_type": "eggs",
    },
    {
        "id": 29, "title": "Lemon Herb Salmon", "cuisine": "Mediterranean",
        "difficulty": "Easy", "time_minutes": 25, "servings": 4,
        "ingredients": ["salmon fillets", "lemon", "dill", "garlic", "olive oil", "capers", "white wine", "parsley", "salt", "black pepper"],
        "steps": [
            "Season salmon with salt and pepper. Let sit at room temperature 10 min.",
            "Heat an oven-safe skillet with olive oil over high heat.",
            "Sear salmon skin-side up 3 min until golden. Flip.",
            "Add garlic, white wine, lemon juice, and capers to the pan.",
            "Transfer to oven at 200 °C for 6–8 min until just cooked through.",
            "Spoon pan juices over salmon, garnish with dill and parsley.",
        ],
        "tags": ["Mediterranean", "fish", "healthy", "quick", "lemon"],
        "flavor_profile": ["bright", "herbaceous", "briny", "light", "savory"],
        "description": "Pan-seared salmon finished in a bright lemon-caper sauce—Mediterranean at its finest.",
        "key_technique": "pan-to-oven method", "protein_type": "fish",
    },
    {
        "id": 30, "title": "Baked Feta Pasta", "cuisine": "Italian",
        "difficulty": "Easy", "time_minutes": 40, "servings": 4,
        "ingredients": ["cherry tomatoes", "feta cheese", "garlic", "olive oil", "penne pasta", "fresh basil", "red chili flakes", "black pepper"],
        "steps": [
            "Place cherry tomatoes in a baking dish. Nestle a block of feta in the centre.",
            "Scatter whole garlic cloves and chili flakes around the tomatoes. Drizzle generously with olive oil.",
            "Bake at 200 °C for 30–35 min until tomatoes burst and feta is golden.",
            "While baking, cook pasta until al dente. Reserve pasta water.",
            "Smash feta and burst tomatoes together to form a creamy sauce. Add pasta water.",
            "Toss in drained pasta and fresh basil. Season and serve immediately.",
        ],
        "tags": ["pasta", "vegetarian", "viral", "baked", "easy"],
        "flavor_profile": ["tangy", "creamy", "savory", "bright", "garlicky"],
        "description": "The viral baked feta pasta—cherry tomatoes and feta become a dreamy sauce.",
        "key_technique": "oven roasting to create sauce", "protein_type": "none",
    },
    {
        "id": 31, "title": "Lamb Souvlaki", "cuisine": "Mediterranean",
        "difficulty": "Easy", "time_minutes": 30, "servings": 4,
        "ingredients": ["lamb leg", "lemon", "olive oil", "oregano", "garlic", "pita bread", "tzatziki", "tomatoes", "red onion", "salt"],
        "steps": [
            "Cut lamb into 3 cm cubes. Marinate in lemon juice, olive oil, garlic, and oregano for 2+ hours.",
            "Thread lamb onto skewers. Season with salt.",
            "Grill over high heat 3–4 min per side until nicely charred but still pink inside.",
            "Warm pita briefly on the grill.",
            "Load pita with grilled lamb, sliced tomatoes, red onion, and generous tzatziki.",
            "Wrap in foil and serve immediately.",
        ],
        "tags": ["Greek", "lamb", "grilled", "street food", "skewers"],
        "flavor_profile": ["charred", "herbaceous", "lemony", "savory", "cooling"],
        "description": "Greece's favourite street food—smoky grilled lamb wrapped in warm pita with tzatziki.",
        "key_technique": "marinating + high-heat grilling", "protein_type": "lamb",
    },
    {
        "id": 32, "title": "Turkish Red Lentil Soup", "cuisine": "Mediterranean",
        "difficulty": "Easy", "time_minutes": 35, "servings": 6,
        "ingredients": ["red lentils", "onion", "carrot", "garlic", "cumin", "paprika", "red pepper flakes", "lemon", "olive oil", "dried mint", "vegetable broth"],
        "steps": [
            "Sauté diced onion, carrot, and garlic in olive oil until soft, about 8 min.",
            "Add cumin, paprika, and lentils. Stir to coat in spices.",
            "Pour in broth and simmer until lentils completely dissolve, about 20 min.",
            "Blend until smooth. Adjust consistency with water.",
            "Make paprika oil: heat olive oil, add paprika and red pepper flakes for 30 sec.",
            "Serve soup drizzled with paprika oil, squeeze of lemon, and dried mint.",
        ],
        "tags": ["Turkish", "soup", "vegan", "lentils", "budget"],
        "flavor_profile": ["earthy", "smoky", "warming", "tangy", "comforting"],
        "description": "Turkey's most beloved soup—silky blended lentils with a vibrant paprika oil finish.",
        "key_technique": "blending + finishing oil", "protein_type": "legumes",
    },
    {
        "id": 33, "title": "Grilled Halloumi Salad", "cuisine": "Mediterranean",
        "difficulty": "Easy", "time_minutes": 20, "servings": 4,
        "ingredients": ["halloumi cheese", "cucumber", "cherry tomatoes", "kalamata olives", "lemon", "fresh mint", "olive oil", "watermelon", "arugula", "honey"],
        "steps": [
            "Slice halloumi 1 cm thick. Pat dry.",
            "Grill in a hot dry pan 2–3 min per side until golden grill marks form.",
            "Arrange arugula, sliced tomatoes, cucumber, and watermelon on a platter.",
            "Place grilled halloumi on top of the salad.",
            "Drizzle with olive oil and lemon juice. Drizzle honey over the cheese.",
            "Scatter olives and fresh mint. Serve immediately while halloumi is warm.",
        ],
        "tags": ["Mediterranean", "vegetarian", "salad", "grilled", "cheese"],
        "flavor_profile": ["salty", "sweet", "bright", "fresh", "savory"],
        "description": "Grilled salty halloumi against sweet watermelon and tangy dressing—summer on a plate.",
        "key_technique": "contact grilling", "protein_type": "dairy",
    },

    # ── MEXICAN ──────────────────────────────────────────────────────────────
    {
        "id": 34, "title": "Tacos Al Pastor", "cuisine": "Mexican",
        "difficulty": "Hard", "time_minutes": 60, "servings": 6,
        "ingredients": ["pork shoulder", "pineapple", "achiote paste", "garlic", "white onion", "cilantro", "lime", "dried guajillo chili", "white corn tortillas", "orange juice"],
        "steps": [
            "Blend dried chilies, achiote paste, garlic, orange juice, and spices into a marinade.",
            "Slice pork thinly, marinate for at least 4 hours or overnight.",
            "Stack marinated pork on a vertical spit with pineapple slices, or cook in a hot cast-iron pan in batches.",
            "Cook until nicely caramelised and slightly charred.",
            "Shave or chop the cooked pork with bits of charred pineapple.",
            "Serve on warm double corn tortillas with diced white onion, cilantro, and lime.",
        ],
        "tags": ["Mexican", "pork", "tacos", "marinated", "street food"],
        "flavor_profile": ["smoky", "tangy", "sweet", "spiced", "charred"],
        "description": "Mexico City's legendary vertical-spit pork tacos—smoky, spiced, kissed by pineapple.",
        "key_technique": "vertical spit roasting / skillet caramelisation", "protein_type": "pork",
    },
    {
        "id": 35, "title": "Black Bean Enchiladas", "cuisine": "Mexican",
        "difficulty": "Medium", "time_minutes": 45, "servings": 6,
        "ingredients": ["black beans", "corn tortillas", "enchilada sauce", "cheddar cheese", "onion", "garlic", "cumin", "sour cream", "avocado", "cilantro"],
        "steps": [
            "Sauté diced onion and garlic until soft. Add black beans and cumin. Season and mash half.",
            "Warm corn tortillas briefly to make them pliable.",
            "Fill each tortilla with black bean mixture, roll up, and place seam-down in a baking dish.",
            "Pour enchilada sauce over all the enchiladas. Top with shredded cheese.",
            "Bake at 190 °C for 20 min until cheese is melted and bubbling.",
            "Top with sour cream, sliced avocado, and fresh cilantro.",
        ],
        "tags": ["Mexican", "vegetarian", "baked", "beans", "comfort"],
        "flavor_profile": ["savory", "earthy", "cheesy", "spiced", "hearty"],
        "description": "Corn tortillas wrapped around smoky black beans and bathed in red enchilada sauce.",
        "key_technique": "sauce bathing + baking", "protein_type": "legumes",
    },
    {
        "id": 36, "title": "Shrimp Ceviche", "cuisine": "Mexican",
        "difficulty": "Easy", "time_minutes": 30, "servings": 4,
        "ingredients": ["shrimp", "lime juice", "orange juice", "red onion", "cilantro", "jalapeño", "avocado", "cucumber", "canned tomatoes", "salt"],
        "steps": [
            "Cook shrimp briefly in boiling water until just pink. Cool immediately in ice water.",
            "Dice shrimp and place in a bowl. Cover with lime and orange juice.",
            "Finely dice red onion, jalapeño, tomatoes, and cucumber. Add to shrimp.",
            "Marinate in the refrigerator 20 min—acid will continue to 'cook' the shrimp.",
            "Just before serving, fold in diced avocado.",
            "Season with salt, garnish with cilantro. Serve with tostadas.",
        ],
        "tags": ["Mexican", "seafood", "fresh", "no-cook", "summer"],
        "flavor_profile": ["bright", "citrusy", "fresh", "spicy", "light"],
        "description": "Mexico's refreshing seafood dish where citrus 'cooks' fresh shrimp beautifully.",
        "key_technique": "citrus denaturation", "protein_type": "seafood",
    },
    {
        "id": 37, "title": "Chilaquiles Verdes", "cuisine": "Mexican",
        "difficulty": "Easy", "time_minutes": 25, "servings": 4,
        "ingredients": ["tortilla chips", "tomatillos", "serrano chili", "garlic", "onion", "cilantro", "eggs", "queso fresco", "sour cream", "avocado"],
        "steps": [
            "Blend tomatillos, serrano, garlic, onion, and cilantro until smooth.",
            "Fry the blended salsa verde in oil for 3–4 min until darkened and fragrant.",
            "Add tortilla chips to the sauce and toss gently—they should soften slightly but keep some texture.",
            "Make fried or scrambled eggs separately.",
            "Plate chilaquiles and top with eggs, crumbled queso fresco, dollops of sour cream.",
            "Fan sliced avocado and garnish with extra cilantro.",
        ],
        "tags": ["Mexican", "breakfast", "quick", "tomatillo", "tortilla chips"],
        "flavor_profile": ["tangy", "savory", "fresh", "spicy", "creamy"],
        "description": "Mexico's ultimate breakfast—tortilla chips simmered in tangy salsa verde.",
        "key_technique": "sauce-softening chips", "protein_type": "eggs",
    },
    {
        "id": 38, "title": "Slow-Cooked Carnitas", "cuisine": "Mexican",
        "difficulty": "Easy", "time_minutes": 180, "servings": 8,
        "ingredients": ["pork shoulder", "orange", "lime", "garlic", "cumin", "oregano", "bay leaves", "salt", "lard", "white corn tortillas", "cilantro"],
        "steps": [
            "Cut pork shoulder into large chunks. Season heavily with salt, cumin, and oregano.",
            "Place pork in a deep pot with orange juice, lime juice, garlic, and bay leaves. Add just enough lard to cover.",
            "Cook uncovered over medium heat for 2 hours, flipping occasionally as liquid evaporates.",
            "Once liquid has evaporated and pork fries in its own fat, cook until crispy on all sides.",
            "Remove and shred or chop into chunks.",
            "Serve in warm double tortillas with fresh cilantro, diced onion, salsa, and lime.",
        ],
        "tags": ["Mexican", "pork", "slow-cooked", "crispy", "street food"],
        "flavor_profile": ["savory", "crispy", "citrusy", "rich", "caramelised"],
        "description": "Michoacán's famous braised-then-fried pork—impossibly juicy inside, shatteringly crispy outside.",
        "key_technique": "confit then frying", "protein_type": "pork",
    },
    {
        "id": 39, "title": "Chicken Mole Negro", "cuisine": "Mexican",
        "difficulty": "Hard", "time_minutes": 120, "servings": 6,
        "ingredients": ["chicken thighs", "dark chocolate", "dried ancho chili", "dried mulato chili", "canned tomatoes", "onion", "garlic", "sesame seeds", "peanuts", "raisins", "cinnamon", "cumin", "chicken broth"],
        "steps": [
            "Toast dried chilies in a dry pan until fragrant. Soak in hot water 20 min. Blend with soaking liquid.",
            "Toast sesame seeds, peanuts, raisins, and spices separately until golden.",
            "Char tomatoes and onion directly over flame until blackened.",
            "Blend all components together into a thick paste.",
            "Fry the paste in oil 5 min, then add broth and dark chocolate. Simmer 30 min.",
            "Add browned chicken and braise 30 more min until sauce is thick and complex. Serve with rice.",
        ],
        "tags": ["Mexican", "chicken", "chocolate", "complex", "Oaxacan"],
        "flavor_profile": ["complex", "rich", "smoky", "subtly sweet", "deeply savory"],
        "description": "Oaxaca's legendary sauce with 30+ ingredients—chocolate and chili in perfect balance.",
        "key_technique": "multi-component toasting + long reduction", "protein_type": "chicken",
    },

    # ── AMERICAN ─────────────────────────────────────────────────────────────
    {
        "id": 40, "title": "BBQ Pulled Pork", "cuisine": "American",
        "difficulty": "Easy", "time_minutes": 240, "servings": 8,
        "ingredients": ["pork shoulder", "BBQ sauce", "apple cider vinegar", "brown sugar", "smoked paprika", "garlic powder", "onion powder", "cayenne", "salt", "brioche buns", "coleslaw"],
        "steps": [
            "Mix paprika, brown sugar, garlic powder, onion powder, cayenne, and salt for the dry rub.",
            "Coat pork shoulder thoroughly in the rub. Rest overnight if possible.",
            "Cook in a slow cooker on low 8 hours (or oven at 150 °C for 4–5 hours), with apple cider vinegar.",
            "Remove pork and shred with two forks. Discard excess fat.",
            "Toss shredded pork with BBQ sauce. Return to cooker briefly to warm.",
            "Pile onto brioche buns with creamy coleslaw.",
        ],
        "tags": ["American", "BBQ", "pork", "sandwich", "slow-cooked"],
        "flavor_profile": ["smoky", "sweet", "tangy", "rich", "caramelised"],
        "description": "Southern BBQ pulled pork—fall-apart tender, smoky, bathed in tangy sauce.",
        "key_technique": "low-and-slow braising", "protein_type": "pork",
    },
    {
        "id": 41, "title": "New England Clam Chowder", "cuisine": "American",
        "difficulty": "Medium", "time_minutes": 45, "servings": 6,
        "ingredients": ["clams", "potatoes", "heavy cream", "bacon", "onion", "celery", "butter", "flour", "clam juice", "thyme", "bay leaves"],
        "steps": [
            "Fry bacon until crispy. Remove. Sauté onion and celery in bacon fat.",
            "Add flour and cook 2 min to make a roux.",
            "Add clam juice and diced potatoes. Simmer until potatoes are just tender.",
            "Add clams and heavy cream. Simmer gently—never boil.",
            "Season with thyme, bay leaves, salt, and white pepper.",
            "Serve in sourdough bread bowls topped with crispy bacon and oyster crackers.",
        ],
        "tags": ["American", "seafood", "soup", "New England", "creamy"],
        "flavor_profile": ["creamy", "briny", "savory", "rich", "comforting"],
        "description": "New England's legendary thick creamy clam chowder—best in a sourdough bowl.",
        "key_technique": "roux-thickened cream soup", "protein_type": "seafood",
    },
    {
        "id": 42, "title": "Cajun Jambalaya", "cuisine": "American",
        "difficulty": "Medium", "time_minutes": 60, "servings": 6,
        "ingredients": ["shrimp", "andouille sausage", "chicken thighs", "long-grain rice", "bell peppers", "onion", "celery", "garlic", "Cajun seasoning", "canned tomatoes", "chicken broth", "thyme"],
        "steps": [
            "Brown andouille sausage in a large Dutch oven. Remove. Brown chicken pieces.",
            "Sauté the 'holy trinity': diced onion, bell pepper, and celery until soft.",
            "Add garlic and Cajun seasoning. Cook 2 min.",
            "Add rice, tomatoes, broth, and thyme. Return chicken and sausage.",
            "Cover and simmer 20–25 min until rice absorbs all liquid.",
            "Add shrimp in last 5 min. Fluff rice, remove bay leaves, adjust seasoning.",
        ],
        "tags": ["Cajun", "American", "rice", "seafood", "sausage", "one-pot"],
        "flavor_profile": ["spicy", "smoky", "savory", "hearty", "Southern"],
        "description": "Louisiana's one-pot celebration of shrimp, sausage, and rice in bold Cajun spices.",
        "key_technique": "one-pot rice absorption", "protein_type": "mixed",
    },
    {
        "id": 43, "title": "Baked Mac and Cheese", "cuisine": "American",
        "difficulty": "Medium", "time_minutes": 50, "servings": 8,
        "ingredients": ["macaroni", "sharp cheddar", "gruyere cheese", "butter", "flour", "whole milk", "Dijon mustard", "cayenne", "Worcestershire sauce", "panko breadcrumbs"],
        "steps": [
            "Cook macaroni until just barely al dente (it cooks more in the oven).",
            "Make mornay sauce: melt butter, whisk in flour, gradually add hot milk until thick.",
            "Off heat, stir in cheddar, gruyere, mustard, Worcestershire, and cayenne.",
            "Combine pasta and cheese sauce. Pour into a buttered baking dish.",
            "Top with panko breadcrumbs tossed in melted butter.",
            "Bake at 190 °C for 25 min. Broil 2–3 min for a golden crust. Rest 5 min before serving.",
        ],
        "tags": ["American", "pasta", "cheese", "comfort", "baked"],
        "flavor_profile": ["cheesy", "rich", "creamy", "crispy topping", "indulgent"],
        "description": "The ultimate baked mac—three-cheese mornay sauce, crispy panko crown.",
        "key_technique": "mornay sauce + baked crust", "protein_type": "none",
    },
    {
        "id": 44, "title": "Classic Caesar Salad", "cuisine": "American",
        "difficulty": "Easy", "time_minutes": 20, "servings": 4,
        "ingredients": ["romaine lettuce", "parmesan cheese", "croutons", "anchovy fillets", "lemon", "garlic", "egg yolk", "Dijon mustard", "Worcestershire sauce", "olive oil"],
        "steps": [
            "Mash anchovies and garlic to a paste. Whisk in egg yolk, lemon, Dijon, and Worcestershire.",
            "Slowly drizzle in olive oil while whisking to emulsify. Season.",
            "Tear romaine into bite-size pieces. Toss generously with dressing.",
            "Add croutons and toss again.",
            "Top with shaved parmesan and cracked black pepper.",
            "Serve immediately.",
        ],
        "tags": ["American", "salad", "classic", "anchovy", "parmesan"],
        "flavor_profile": ["savory", "umami", "creamy", "garlicky", "bright"],
        "description": "The world's most famous salad—anchovy and egg dressing that became an icon.",
        "key_technique": "dressing emulsification", "protein_type": "none",
    },
    {
        "id": 45, "title": "Chicken Pot Pie", "cuisine": "American",
        "difficulty": "Medium", "time_minutes": 75, "servings": 6,
        "ingredients": ["chicken breast", "peas", "carrots", "celery", "onion", "garlic", "butter", "flour", "chicken broth", "heavy cream", "thyme", "pie crust", "egg"],
        "steps": [
            "Cook chicken and cube into chunks. Sauté vegetables in butter until soft.",
            "Add flour and cook 2 min. Gradually add warm broth and cream, stirring until thick gravy forms.",
            "Add chicken, peas, and thyme. Season well. Let filling cool slightly.",
            "Line a deep pie dish with pastry. Pour in filling.",
            "Top with second pastry sheet. Crimp edges, cut steam vents, brush with egg wash.",
            "Bake at 200 °C for 35–40 min until deep golden. Rest 10 min before serving.",
        ],
        "tags": ["American", "chicken", "comfort", "baked", "pastry"],
        "flavor_profile": ["rich", "savory", "creamy", "flaky", "warming"],
        "description": "Classic American comfort in pastry—creamy chicken and vegetables in a flaky crust.",
        "key_technique": "double-crust pie", "protein_type": "chicken",
    },

    # ── FRENCH ───────────────────────────────────────────────────────────────
    {
        "id": 46, "title": "French Onion Soup", "cuisine": "French",
        "difficulty": "Medium", "time_minutes": 90, "servings": 6,
        "ingredients": ["onions", "beef broth", "gruyere cheese", "baguette", "butter", "white wine", "thyme", "bay leaves", "garlic", "cognac"],
        "steps": [
            "Slice 2 kg onions thinly. Cook in butter over medium-low heat for 45–60 min, stirring occasionally, until deeply caramelised and jammy.",
            "Add cognac and flambé. Add wine and reduce by half.",
            "Add broth, thyme, and bay leaves. Simmer 20 min. Remove bay leaves. Season.",
            "Toast baguette slices until dry and crispy.",
            "Ladle soup into oven-safe bowls. Float toasted baguette on top.",
            "Cover entirely with grated gruyere. Broil until molten, bubbling, and golden. Serve immediately.",
        ],
        "tags": ["French", "soup", "onion", "cheese", "baked"],
        "flavor_profile": ["sweet", "savory", "rich", "umami", "deep"],
        "description": "France's glorious onion soup—45 min of caramelisation rewarded with extraordinary depth.",
        "key_technique": "long caramelisation + broiling", "protein_type": "none",
    },
    {
        "id": 47, "title": "Ratatouille Niçoise", "cuisine": "French",
        "difficulty": "Medium", "time_minutes": 75, "servings": 6,
        "ingredients": ["eggplant", "zucchini", "canned tomatoes", "bell peppers", "onion", "garlic", "olive oil", "thyme", "basil", "herbes de Provence"],
        "steps": [
            "Sauté diced onion and bell peppers in olive oil over medium heat until soft, 10 min.",
            "Add garlic, eggplant, and zucchini. Cook 10 more min.",
            "Add tomatoes, herbes de Provence, and thyme. Cover and simmer 30 min.",
            "For the 'confit byaldi' presentation: thinly slice all vegetables on a mandoline. Arrange overlapping circles in a baking dish.",
            "Drizzle with olive oil and bake at 180 °C for 40 min.",
            "Top with fresh basil and serve.",
        ],
        "tags": ["French", "vegetarian", "Provençal", "roasted", "summer"],
        "flavor_profile": ["earthy", "sweet", "herbaceous", "Mediterranean"],
        "description": "Provence's colourful vegetable stew—beautiful layered or rustic, always deeply flavoured.",
        "key_technique": "slow braising + confit", "protein_type": "none",
    },
    {
        "id": 48, "title": "Coq au Vin", "cuisine": "French",
        "difficulty": "Hard", "time_minutes": 90, "servings": 4,
        "ingredients": ["chicken pieces", "red wine", "bacon", "mushrooms", "pearl onions", "garlic", "chicken broth", "thyme", "bay leaves", "butter", "flour", "cognac"],
        "steps": [
            "Brown chicken pieces in butter until deeply golden on all sides. Set aside.",
            "Fry bacon lardons. Add pearl onions and mushrooms until browned.",
            "Add garlic and cognac. Flambé carefully.",
            "Return chicken to pot. Pour in wine and just enough broth to barely cover.",
            "Add thyme and bay leaves. Simmer covered for 45 min until chicken is tender.",
            "Remove chicken. Reduce sauce over high heat until silky. Whisk in a butter knob. Return chicken and serve with crusty bread.",
        ],
        "tags": ["French", "chicken", "wine", "braised", "bistro"],
        "flavor_profile": ["rich", "wine-forward", "savory", "earthy", "deep"],
        "description": "French countryside classic—chicken braised in red wine until impossibly tender.",
        "key_technique": "wine braising + sauce reduction", "protein_type": "chicken",
    },
    {
        "id": 49, "title": "Quiche Lorraine", "cuisine": "French",
        "difficulty": "Medium", "time_minutes": 70, "servings": 8,
        "ingredients": ["eggs", "heavy cream", "bacon", "gruyere cheese", "pie crust", "onion", "nutmeg", "salt", "white pepper"],
        "steps": [
            "Blind bake the pastry shell: line tart pan with parchment and weights, bake at 190 °C for 15 min.",
            "Fry bacon until crispy. Drain. Sauté onion until soft.",
            "Whisk eggs and cream until smooth. Season with nutmeg, salt, and white pepper.",
            "Scatter bacon and onion in the blind-baked shell. Pour custard over. Top with gruyere.",
            "Bake at 180 °C for 30–35 min until just set with a slight wobble in the centre.",
            "Cool 10 min before slicing. Serve warm or at room temperature.",
        ],
        "tags": ["French", "egg", "tart", "bacon", "cheese"],
        "flavor_profile": ["rich", "creamy", "savory", "smoky", "eggy"],
        "description": "France's classic custard tart—silky egg-cream filling with smoky bacon in flaky pastry.",
        "key_technique": "blind baking + custard setting", "protein_type": "eggs",
    },
    {
        "id": 50, "title": "Beef Bourguignon", "cuisine": "French",
        "difficulty": "Hard", "time_minutes": 180, "servings": 6,
        "ingredients": ["beef chuck", "red wine", "bacon", "mushrooms", "pearl onions", "carrots", "garlic", "tomato paste", "beef broth", "thyme", "bay leaves", "butter", "flour"],
        "steps": [
            "Marinate beef in wine with vegetables and herbs overnight for best results.",
            "Brown bacon in a Dutch oven. Brown beef in batches—don't crowd. Set aside.",
            "Sauté carrots and garlic. Add tomato paste and cook 2 min.",
            "Return beef, add wine marinade and broth. Bring to simmer.",
            "Braise covered in oven at 160 °C for 2.5 hours until beef is very tender.",
            "Sauté mushrooms and pearl onions separately in butter. Add to the braised beef. Adjust sauce consistency and serve with mashed potatoes.",
        ],
        "tags": ["French", "beef", "wine", "braised", "winter", "special occasion"],
        "flavor_profile": ["rich", "deep", "wine-forward", "earthy", "savory"],
        "description": "Julia Child's masterpiece—Burgundy beef braised in wine until it melts on the tongue.",
        "key_technique": "overnight marination + long braising", "protein_type": "beef",
    },

    # ── MIDDLE EASTERN ───────────────────────────────────────────────────────
    {
        "id": 51, "title": "Chicken Shawarma", "cuisine": "Middle Eastern",
        "difficulty": "Medium", "time_minutes": 45, "servings": 6,
        "ingredients": ["chicken thighs", "yogurt", "lemon", "cumin", "turmeric", "cinnamon", "garlic", "pita bread", "tahini", "tomatoes", "cucumber", "sumac", "red onion"],
        "steps": [
            "Mix yogurt, lemon, all spices, and garlic for marinade. Coat chicken and marinate 4+ hours.",
            "Grill chicken on high heat 5–6 min per side until charred and cooked through.",
            "Rest 5 min then slice thinly against the grain.",
            "Warm pita breads on the grill.",
            "Make garlic-tahini sauce: blend tahini, garlic, lemon, and water to a drizzlable consistency.",
            "Load pita with chicken, tomatoes, cucumber, red onion, and generous garlic-tahini sauce.",
        ],
        "tags": ["Middle Eastern", "chicken", "marinated", "street food", "yogurt"],
        "flavor_profile": ["spiced", "charred", "tangy", "aromatic", "creamy"],
        "description": "The Levant's ultimate street food—spiced, charred chicken with garlic-tahini sauce.",
        "key_technique": "yogurt marination + high-heat grilling", "protein_type": "chicken",
    },
    {
        "id": 52, "title": "Lamb Kofta", "cuisine": "Middle Eastern",
        "difficulty": "Easy", "time_minutes": 30, "servings": 4,
        "ingredients": ["ground lamb", "onion", "parsley", "cumin", "coriander", "cinnamon", "allspice", "red chili", "fresh mint", "garlic", "pita bread", "tzatziki"],
        "steps": [
            "Grate onion and squeeze out all moisture. Mix with ground lamb, herbs, and all spices.",
            "Knead mixture well for 3 min—this develops protein and helps it hold on skewers.",
            "Shape into elongated cylinders around flat metal skewers.",
            "Grill over high heat 3–4 min per side until nicely charred.",
            "Rest 3 min.",
            "Serve in warm pita with tzatziki, sliced tomatoes, and fresh mint.",
        ],
        "tags": ["Middle Eastern", "lamb", "grilled", "skewers", "spiced"],
        "flavor_profile": ["spiced", "herby", "charred", "savory", "aromatic"],
        "description": "Ground lamb seasoned with warm spices and fresh herbs, grilled on skewers.",
        "key_technique": "protein development + grilling", "protein_type": "lamb",
    },
    {
        "id": 53, "title": "Fattoush Salad", "cuisine": "Middle Eastern",
        "difficulty": "Easy", "time_minutes": 20, "servings": 4,
        "ingredients": ["romaine lettuce", "tomatoes", "cucumber", "radishes", "sumac", "lemon", "olive oil", "pita chips", "fresh mint", "parsley", "pomegranate seeds"],
        "steps": [
            "Toast or fry pita pieces until golden and crispy. Season with sumac.",
            "Chop all vegetables into similar bite-size pieces.",
            "Make dressing: whisk lemon juice, olive oil, and a generous amount of sumac.",
            "Toss vegetables with dressing.",
            "Add pita chips and toss briefly—they should stay slightly crispy.",
            "Garnish with pomegranate seeds and fresh mint.",
        ],
        "tags": ["Middle Eastern", "salad", "vegan", "fresh", "sumac"],
        "flavor_profile": ["tangy", "fresh", "bright", "crispy", "herbaceous"],
        "description": "The Levant's bright bread salad—vegetables dressed with sumac and lemony vinaigrette.",
        "key_technique": "crispy bread integration", "protein_type": "none",
    },
    {
        "id": 54, "title": "Red Lentil Shorba", "cuisine": "Middle Eastern",
        "difficulty": "Easy", "time_minutes": 35, "servings": 6,
        "ingredients": ["red lentils", "onion", "garlic", "carrot", "cumin", "turmeric", "coriander", "lemon", "olive oil", "red chili", "vegetable broth", "cilantro"],
        "steps": [
            "Sauté diced onion, carrot, and garlic in olive oil until soft.",
            "Add all spices and stir for 1 min.",
            "Add rinsed red lentils and vegetable broth. Bring to boil.",
            "Reduce heat and simmer 20–25 min until lentils completely dissolve.",
            "Blend until smooth. Adjust consistency with water.",
            "Serve with a swirl of olive oil, squeeze of lemon, fresh cilantro, and warm flatbread.",
        ],
        "tags": ["Middle Eastern", "soup", "vegan", "lentils", "warming"],
        "flavor_profile": ["earthy", "warming", "spiced", "smooth", "comforting"],
        "description": "The Middle East's nourishing red lentil soup, scented with cumin and turmeric.",
        "key_technique": "spice blooming + blending", "protein_type": "legumes",
    },
    {
        "id": 55, "title": "Baba Ganoush", "cuisine": "Middle Eastern",
        "difficulty": "Easy", "time_minutes": 45, "servings": 6,
        "ingredients": ["eggplant", "tahini", "garlic", "lemon", "olive oil", "parsley", "cumin", "smoked paprika", "salt"],
        "steps": [
            "Char eggplant directly on a gas flame, turning occasionally, until completely blackened outside and collapsed—15–20 min.",
            "Place in a colander and rest 10 min to drain excess liquid.",
            "Scoop out flesh, discarding charred skin.",
            "Mash eggplant with tahini, garlic, lemon juice, and cumin until smooth but slightly chunky.",
            "Season generously with salt. Rest 30 min—flavours improve greatly.",
            "Serve drizzled with olive oil, smoked paprika, and parsley alongside warm pita.",
        ],
        "tags": ["Middle Eastern", "dip", "vegan", "eggplant", "smoked"],
        "flavor_profile": ["smoky", "creamy", "tangy", "nutty", "earthy"],
        "description": "Levantine eggplant dip defined by fire-charred smokiness and tahini richness.",
        "key_technique": "direct flame charring", "protein_type": "none",
    },

    # ── VEGETARIAN / VEGAN ───────────────────────────────────────────────────
    {
        "id": 56, "title": "Buddha Bowl with Tahini Dressing", "cuisine": "International",
        "difficulty": "Easy", "time_minutes": 30, "servings": 2,
        "ingredients": ["quinoa", "chickpeas", "sweet potato", "kale", "avocado", "cucumber", "tahini", "lemon", "garlic", "olive oil", "smoked paprika", "cumin"],
        "steps": [
            "Cook quinoa per package instructions. Season with lemon and olive oil.",
            "Toss sweet potato cubes with olive oil, paprika, and cumin. Roast at 200 °C for 25 min.",
            "Toss chickpeas with paprika and roast alongside sweet potato until crispy.",
            "Massage kale with olive oil and lemon until tender.",
            "Make tahini dressing: whisk tahini, garlic, lemon, and water to drizzling consistency.",
            "Build bowls: quinoa base, arranged piles of each topping, sliced avocado and cucumber. Drizzle generously with tahini dressing.",
        ],
        "tags": ["vegetarian", "vegan", "healthy", "bowl", "balanced"],
        "flavor_profile": ["nutty", "earthy", "creamy", "bright", "satisfying"],
        "description": "The balanced, nourishing bowl—grains, roasted vegetables, and creamy tahini dressing.",
        "key_technique": "component roasting + assembly", "protein_type": "legumes",
    },
    {
        "id": 57, "title": "Mushroom Stroganoff", "cuisine": "International",
        "difficulty": "Easy", "time_minutes": 30, "servings": 4,
        "ingredients": ["mixed mushrooms", "sour cream", "onion", "garlic", "smoked paprika", "Dijon mustard", "pasta", "butter", "parsley", "white wine"],
        "steps": [
            "Cook pasta until al dente. Reserve pasta water.",
            "Sauté onion in butter until golden. Add garlic.",
            "Add mushrooms over high heat—don't stir immediately, let them brown well.",
            "Add white wine and reduce by half. Stir in paprika and mustard.",
            "Remove from heat and stir in sour cream. Season well.",
            "Toss in pasta with a splash of pasta water. Garnish with fresh parsley.",
        ],
        "tags": ["vegetarian", "mushroom", "pasta", "creamy", "quick"],
        "flavor_profile": ["earthy", "creamy", "savory", "slightly tangy"],
        "description": "Meat-free stroganoff where mushrooms provide all the depth and richness needed.",
        "key_technique": "high-heat mushroom browning", "protein_type": "none",
    },
    {
        "id": 58, "title": "Falafel Bowl", "cuisine": "Middle Eastern",
        "difficulty": "Medium", "time_minutes": 50, "servings": 4,
        "ingredients": ["dried chickpeas", "onion", "garlic", "parsley", "cilantro", "cumin", "coriander", "baking powder", "sesame seeds", "tahini", "lemon", "pita", "tomatoes"],
        "steps": [
            "Soak dried chickpeas overnight (do NOT use canned—they make falafel fall apart).",
            "Blend soaked chickpeas with onion, garlic, fresh herbs, and spices until coarse-textured.",
            "Add baking powder and rest mixture 30 min in the fridge.",
            "Roll into balls, coat in sesame seeds.",
            "Deep fry at 180 °C for 3–4 min until deep golden, or bake at 220 °C for 20 min.",
            "Blend tahini with garlic, lemon, and water for sauce. Serve falafel in pita with salad and tahini sauce.",
        ],
        "tags": ["Middle Eastern", "vegan", "fried", "chickpeas", "street food"],
        "flavor_profile": ["herby", "crispy", "earthy", "nutty", "fresh"],
        "description": "The Levant's iconic herb-flecked chickpea fritter—crispy outside, fluffy inside.",
        "key_technique": "proper dry chickpea use + deep frying", "protein_type": "legumes",
    },
    {
        "id": 59, "title": "Shakshuka with White Beans", "cuisine": "Mediterranean",
        "difficulty": "Easy", "time_minutes": 30, "servings": 4,
        "ingredients": ["eggs", "white beans", "canned tomatoes", "spinach", "garlic", "onion", "cumin", "smoked paprika", "feta cheese", "olive oil", "fresh parsley"],
        "steps": [
            "Sauté onion and garlic in olive oil until soft.",
            "Add cumin, paprika, and canned tomatoes. Simmer 10 min.",
            "Stir in white beans and spinach until wilted.",
            "Create wells and crack eggs into each. Cover and cook until whites are set.",
            "Top with crumbled feta and parsley.",
            "Serve directly from the pan with crusty bread.",
        ],
        "tags": ["vegetarian", "eggs", "Mediterranean", "beans", "one-pan"],
        "flavor_profile": ["savory", "creamy", "spiced", "tangy"],
        "description": "A protein-packed shakshuka variation with white beans and wilted spinach.",
        "key_technique": "egg poaching in sauce", "protein_type": "eggs",
    },
    {
        "id": 60, "title": "Lentil Soup with Crispy Leeks", "cuisine": "International",
        "difficulty": "Easy", "time_minutes": 40, "servings": 6,
        "ingredients": ["green lentils", "leeks", "carrots", "celery", "garlic", "cumin", "coriander", "lemon", "vegetable broth", "olive oil", "fresh thyme", "bay leaves"],
        "steps": [
            "Slice leeks thinly. Fry half in olive oil until crispy and golden. Set aside for garnish.",
            "Sauté remaining leeks, carrots, and celery until soft, about 8 min.",
            "Add garlic, cumin, and coriander. Cook 1 min.",
            "Add lentils, broth, thyme, and bay leaves. Simmer 25 min until lentils are tender.",
            "Remove bay leaves. Partially blend for a chunky-smooth texture.",
            "Season with lemon juice and salt. Serve topped with crispy leeks.",
        ],
        "tags": ["vegetarian", "vegan", "soup", "lentils", "comfort"],
        "flavor_profile": ["earthy", "warming", "hearty", "bright"],
        "description": "Comforting lentil soup elevated by a topping of shatteringly crispy fried leeks.",
        "key_technique": "partial blending + crispy garnish", "protein_type": "legumes",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# VARIATION GENERATOR  →  turns 60 base recipes into 300+ total
# ─────────────────────────────────────────────────────────────────────────────
def _sub_vegan(ing: str) -> str:
    subs = {
        "chicken": "tofu", "beef": "seitan", "pork": "jackfruit", "lamb": "lentils",
        "eggs": "flax eggs", "egg": "flax egg",
        "butter": "vegan butter", "cream": "coconut cream", "heavy cream": "coconut cream",
        "whole milk": "oat milk", "milk": "oat milk",
        "parmesan cheese": "nutritional yeast", "parmesan": "nutritional yeast",
        "feta cheese": "vegan feta", "feta": "vegan feta",
        "mozzarella": "vegan mozzarella", "cheddar": "vegan cheddar",
        "gruyere cheese": "vegan cheese", "gruyere": "vegan cheese",
        "halloumi cheese": "firm tofu", "halloumi": "firm tofu",
        "sour cream": "coconut yogurt", "yogurt": "coconut yogurt",
        "bacon": "smoked tempeh", "pancetta": "smoked tempeh",
        "shrimp": "hearts of palm", "salmon": "marinated tofu",
        "anchovy": "nori flakes", "fish sauce": "soy sauce",
    }
    for k, v in subs.items():
        if k in ing.lower():
            return v
    return ing


def _sub_lighter(ing: str) -> str:
    subs = {
        "heavy cream": "Greek yogurt", "cream": "low-fat Greek yogurt",
        "butter": "olive oil", "bacon": "turkey bacon", "pancetta": "prosciutto",
        "sour cream": "light Greek yogurt", "whole milk": "skimmed milk",
    }
    for k, v in subs.items():
        if k in ing.lower():
            return v
    return ing


def generate_variations(base_recipes):
    """Expands 60 base recipes to ~300 entries via 4 variation types."""
    all_recipes = list(base_recipes)

    for recipe in base_recipes:
        bid = recipe["id"]

        # ── 1. Spicy version ──────────────────────────────────────────────
        spicy = copy.deepcopy(recipe)
        spicy["id"] = f"{bid}_spicy"
        spicy["title"] = f"Fiery {recipe['title']}"
        spicy["tags"] = recipe["tags"] + ["spicy", "extra-hot"]
        spicy["flavor_profile"] = recipe["flavor_profile"] + ["fiery"]
        if not any("chili" in i.lower() or "cayenne" in i.lower() for i in spicy["ingredients"]):
            spicy["ingredients"] = list(spicy["ingredients"]) + ["red chili flakes", "cayenne pepper"]
        if spicy["steps"]:
            spicy["steps"] = list(spicy["steps"])
            spicy["steps"][-1] += " Finish with a drizzle of chili oil for an extra kick."
        all_recipes.append(spicy)

        # ── 2. Quick 30-minute version ────────────────────────────────────
        quick = copy.deepcopy(recipe)
        quick["id"] = f"{bid}_quick"
        quick["title"] = f"Quick {recipe['title']}"
        quick["difficulty"] = "Easy"
        quick["time_minutes"] = min(recipe["time_minutes"], 30)
        quick["tags"] = recipe["tags"] + ["30-minute", "quick", "weeknight"]
        quick["steps"] = list(recipe["steps"])[:4] + ["Taste, adjust seasoning, and serve immediately."]
        all_recipes.append(quick)

        # ── 3. Vegan version (skip already-vegan recipes) ─────────────────
        if "vegan" not in recipe.get("tags", []):
            vegan = copy.deepcopy(recipe)
            vegan["id"] = f"{bid}_vegan"
            vegan["title"] = f"Plant-Based {recipe['title']}"
            vegan["tags"] = recipe["tags"] + ["vegan", "plant-based", "dairy-free"]
            vegan["protein_type"] = "legumes"
            vegan["ingredients"] = [_sub_vegan(i) for i in recipe["ingredients"]]
            vegan["steps"] = [
                s.replace("chicken", "tofu").replace("beef", "seitan")
                 .replace("pork", "jackfruit").replace("butter", "olive oil")
                 .replace("cream", "coconut cream").replace("bacon", "smoked tempeh")
                for s in recipe["steps"]
            ]
            all_recipes.append(vegan)

        # ── 4. Light & healthy version ────────────────────────────────────
        light = copy.deepcopy(recipe)
        light["id"] = f"{bid}_light"
        light["title"] = f"Light & Healthy {recipe['title']}"
        light["tags"] = recipe["tags"] + ["healthy", "low-calorie", "light"]
        light["ingredients"] = [_sub_lighter(i) for i in recipe["ingredients"]]
        light["steps"] = list(recipe["steps"]) + [
            "Serve alongside a green salad for a complete, balanced meal."
        ]
        all_recipes.append(light)

    return all_recipes


def get_all_recipes():
    """Return all recipes (base + variations)."""
    return generate_variations(BASE_RECIPES)
