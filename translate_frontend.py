import re

with open("frontend/index-new.html", "r") as f:
    content = f.read()

replacements = {
    "🍳 AI Recipe Inventor PRO — RAG Engine": "🍳 AI Recipe Agent PRO — Iterative RAG",
    "Motor RAG · TF-IDF · Chatbot · Shopping · Fără LLM": "Agentic RAG · Dense Retrieval · Semantic Search",
    "rețete indexate": "recipes indexed",
    "bucătării": "cuisines",
    "ingrediente/rețetă": "ingredients/recipe",
    "✨ Creator": "✨ Creator",
    "💬 Chatbot": "💬 Chatbot",
    "🛒 Shopping List": "🛒 Shopping List",
    "ℹ️ About": "ℹ️ About",
    "Ce ai în bucătărie?": "What's in your kitchen?",
    "Adaugă ingredientele disponibile și generăm rețete creative pentru tine.": "Add your available ingredients and let the Agent build recipes for you.",
    "Ingrediente": "Ingredients",
    "Ex: pui, usturoi, lămâie… apasă Enter": "E.g. chicken, garlic, lemon... press Enter",
    "Apasă <kbd>Enter</kbd> sau <kbd>,</kbd> după fiecare ingredient.": "Press <kbd>Enter</kbd> or <kbd>,</kbd> after each ingredient.",
    "✕ Șterge tot": "✕ Clear all",
    "Încearcă:": "Try:",
    "Bucătărie": "Cuisine",
    "🌍 Orice": "🌍 Any",
    "Dificultate": "Difficulty",
    "⚡ Orice": "⚡ Any",
    "🟢 Ușor": "🟢 Easy",
    "🟡 Mediu": "🟡 Medium",
    "🔴 Dificil": "🔴 Hard",
    "Timp maxim": "Max Time",
    "⏱ Orice durată": "⏱ Any time",
    "≤ 20 min": "≤ 20 min",
    "≤ 30 min": "≤ 30 min",
    "≤ 1 oră": "≤ 1 hour",
    "≤ 2 ore": "≤ 2 hours",
    "Număr rețete:": "Num recipes:",
    "Inventează Rețete!": "Invent Recipes!",
    "Căutăm prin": "Searching through",
    "rețete…": "recipes...",
    "Motorul RAG găsește cele mai potrivite baze și le combină cu ingredientele tale.": "The Iterative Agent formulates queries and searches ChromaDB for the perfect match.",
    "Rețetele Tale": "Your Recipes",
    "← Caută din nou": "← Search again",
    "← Încearcă din nou": "← Try again",
    "Vorbește cu asistentul tău AI. Spune-i ce ai în cămară și primești rețete potrivite!": "Talk to your AI Assistant. Tell it what you have and get recipes!",
    "🛒 Lista de Cumpărături": "🛒 Shopping List",
    "Ingrediente necesare pentru rețetele tale": "Ingredients needed for your recipes",
    "📋 Export": "📋 Export",
    "🗑️ Șterge": "🗑️ Clear",
    "Lista goală": "Empty List",
    "Generează o rețetă din tab-ul Creator și apasă \"Adaugă la Shopping List\"!": "Generate a recipe in the Creator tab and click 'Add to Shopping List'!",
    "Cumpărate": "Purchased",
    "Budget estimat": "Est. Budget",
    "Adaugă ingredient...": "Add ingredient...",
    "🔄 Substituții Disponibile (RAG)": "🔄 Available Substitutes (RAG)",
    "Ingrediente alternative bazate pe rețetele din bază:": "Alternative ingredients based on vector search:",
    "ℹ️ Despre AI Recipe Inventor PRO": "ℹ️ About AI Recipe Agent PRO",
    "AI Recipe Inventor PRO · RAG cu TF-IDF · Chatbot · Shopping List · Fără LLM · Made with ❤️": "AI Recipe Agent PRO · ChromaDB Dense Retrieval · Iterative Agent · Made with ❤️"
}

for ro, en in replacements.items():
    content = content.replace(ro, en)

with open("frontend/index-new.html", "w") as f:
    f.write(content)
